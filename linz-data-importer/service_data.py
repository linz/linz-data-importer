"""
/***************************************************************************
 LINZ Data Importer
                                 A QGIS plugin
 Import LINZ (and others) OGC Datasets into QGIS
                              -------------------
        begin                : 2018-04-07
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Land Information New Zealand
        email                : splanzer@linz.govt.nz
 ***************************************************************************/
/***************************************************************************
 *   This program is released under the terms of the 3 clause BSD license. *
 *   see the LICENSE file for more information                             *
 ***************************************************************************/
"""


from builtins import object
import re
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

from owslib.wmts import WebMapTileService
from owslib.util import ServiceException 
from qgis.core import QgsMessageLog, QgsApplication

import os.path
from lxml.etree import XMLSyntaxError
from lxml import etree

from urllib.request import urlopen
from urllib.error import URLError

from qgis.PyQt.QtCore import QSettings

class ApiKey(object):
    """
    Store API Keys for each domain. Required to 
    fetch service data
    """


    # TODO// MAKE SINGLETON
    def __init__(self):
       self.api_keys = self.getApiKeys()

    def getApiKeys(self):
        """
        Return Domain / API keys stored in QSettings

        @return: e.g. {domain1: api_key1, domain2: api_key2}
        @rtype: dict
        """

        keys = QSettings().value('linz_data_importer/apikeys')
        if not keys:
            return {}
        return keys

    def getApiKey(self, domain):
        """
        Returns an API Key related to a domain

        @return: API Key
        @rtype: str
        """

        return self.api_keys[domain]

    def setApiKeys(self, keys):
        """
        Save API Keys as Qsettings Value

        :param keys: {domain1: api_key1, domain2: api_key2...}
        :type keys: dict
        """

        # = {domain:api_key}
        QSettings().setValue('linz_data_importer/apikeys', keys)
        self.api_keys = self.getApiKeys()

class Localstore(object):
    """ 
    Caching of capability documents
    """

    def __init__(self, domain=None, service=None, file=None):
        """
        Initiate localstore 

        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service: Service Type (WMS, WMTS, or WFS)
        :type service: str
        :param file: file name 
        :type file: str
        """

        self.domain=domain
        self.service=service
        self.xml=None
        self.pl_settings_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), "linz-data-importer")
        self.ensureSettingsDir()
        self.file=file
        if self.service:
            self.file = os.path.join(self.pl_settings_dir , 
                               '{0}_{1}.xml'.format(domain, service.lower()))

    def ensureSettingsDir(self):
        """
        Create the plugins settings dir if not exists
        """

        if not os.path.exists(self.pl_settings_dir):
            os.makedirs(self.pl_settings_dir)

    def delLocalSeviceXML(self, file=None):
        """
        Delete a single file
        """

        if not file:
            file = self.file
        try:
            os.remove(file)
        except OSError:
            pass

    def delDomainsXML(self, domain):
        """
        Delete all cached files associated with a domain

        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain str
        """

        if not domain:
            domain = self.domain

        dir = self.pl_settings_dir
        for f in os.listdir(self.pl_settings_dir):
            if re.search(domain, f):
                file = os.path.join(dir, f)
                self.delLocalSeviceXML(file)

    def delAllLocalServiceXML(self, services=['wms','wfs','wmts']):
        """
        Find and delete all cached files

        :param domain: list services
        :type domain: list
        """

        search_str = '|'.join(['_{}.xml'.format(x) for x in services])

        dir = self.pl_settings_dir
        for f in os.listdir(self.pl_settings_dir):
            if re.search(search_str, f):
                file = os.path.join(dir, f)
                self.delLocalSeviceXML(file)

    def serviceXmlIsLocal(self, file=None):
        """
        Test if the cached capabilties xml doc exists
        :param file: file name 
        :type file: str
        @return: boolean. True file exists
        @rtype: boolean
        """

        if not file:
            file = self.file
        return os.path.isfile(file)

    def readLocalServiceXml(self, file=None):
        """
        Read the cached XML document

        :param file: file name 
        :type file: str 
        """

        if not file:
            file = self.file
        with open(file, 'rb') as f:
            self.xml = f.read()

class ServiceData(Localstore):
    """
    Get, Store and Process WxS Data
    """

    def __init__(self, domain, service, service_version, api_key_instance):
        """
        Initialise Service Data instance 

        :param service: Service Type (WMS, WMTS, or WFS)
        :type service: str
        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service_version: {'wms': '1.1.1', 'wfs': '2.0.0', 'wmts': '1.0.0'}
        :type service_version: dict
        :param api_key_instance: API instance 
        :type api_key_instance: linz-data-importer.service_data.ApiKey
        """

        self.version = service_version[service]
        self.api_key_int = api_key_instance # using one instance as the user can change keys on us
        Localstore.__init__(self, domain, service)
        # Data 
        self.obj = None #owslib data obj
        self.info = None # owslib data obj formatted for table
        self.err = None # any errors 
        self.disabled = False

    def isEnabled(self):
        """
        Test if the service is enable.
        Some services (e.g wms) are disabled for specific domains. These 
        return XML docs without headers. 

        @return: boolean. True == Service is diabled
        @rtype: boolean
        """

        disbaled_str = ('Service {0} is disabled').format(self.service.upper())
        if self.xml.find(disbaled_str.encode()) == -1:
            return True
        self.disabled = True
        return False

    def getServiceData(self):
        """
        Select method to obtain capbilties doc. 
        Either via localstore or internet 
        """

        # Get service xml
        if self.serviceXmlIsLocal():
            self.readLocalServiceXml()
        else:
            self.getServiceXml()

    def getServiceDataTryAgain(self):
        """
        If the reading of the capability doc fails - Try again.
        This is for use cases where for some reason the user
        has corrupted the capability doc in the localstore
        """

        #Clear error, Delete local file and get it a fresh
        self.err=None
        self.delLocalSeviceXML()
        self.getServiceData()
        if self.err:
            return
        self.getServiceObj()
        if self.err:
            return

    def processServiceData(self):
        """
        Get, process and format the service data
        """

        self.getServiceData()
        if self.err:
            return

        if not self.isEnabled():
            return

        # service info obj
        self.getServiceObj()
        if self.err=='{0}: XMLSyntaxError'.format(self.domain):
            self.getServiceDataTryAgain()
        if self.err:
            return

        # Format the response data
        self.formatForUI()

    def getServiceObj(self):
        try:
            if self.service == 'wms':
                self.obj = WebMapService(url=None, xml=self.xml, version=self.version)
            elif self.service == 'wmts':
                self.obj = WebMapTileService(url=None, xml=self.xml, version=self.version,)
            elif self.service == 'wfs':
                self.obj = WebFeatureService(url=None, xml=self.xml, version=self.version,)
        except XMLSyntaxError as e:
            #most likely the locally stored xml is corrupt
            self.err = '{0}: XMLSyntaxError'.format(self.domain)
        

    def getServiceXml(self):
        """
        Get capability documents from the internet
        """

        try:
            if self.service == 'wmts':
                xml =  urlopen('https://{0}/services;'
                               'key={1}/{2}/{3}/WMTSCapabilities.xml'.format(self.domain,
                                                                             self.api_key_int.getApiKey(self.domain), 
                                                                             self.service.lower(),
                                                                             self.version))

            elif self.service in ('wms', 'wfs'):
                xml = urlopen('https://{0}/services;'
                              'key={1}/{2}?service={3}&version={4}'
                              '&request=GetCapabilities'.format(self.domain,
                                                                self.api_key_int.getApiKey(self.domain), 
                                                                self.service.lower(),
                                                                self.service.upper(),
                                                                self.version))
            self.xml = xml.read()

            # write to cache
            with open(self.file, 'wb') as f:
                f.write(self.xml)

        except URLError as e:
            if hasattr(e, 'reason'):
                self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)

            elif hasattr(e, 'code'):
                 self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)

    def formatForUI(self):
        """
        Format the service data to display in the UI
        """

        service_data = []
        cont = self.obj.contents

        for dataset_id, dataset_obj in cont.items():
            full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
            type = full_id.group('type')
            id  =  full_id.group('id')
            service_data.append([self.domain, type, id, self.service.upper(), dataset_obj.title, dataset_obj.abstract])

        self.info = service_data
