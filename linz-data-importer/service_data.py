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

import re        
import time        
import glob

from owslib.wfs import WebFeatureService

from owslib.wmts import WebMapTileService
from owslib.util import ServiceException 
from qgis.core import QgsApplication

import os.path

try: 
    from lxml import etree
    from lxml.etree import XMLSyntaxError
except ImportError:  
    from xml import etree 
    from xml.etree.ElementTree import ParseError as XMLSyntaxError

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
        :param service: Service Type (WMTS or WFS)
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
                               '{0}_{1}_{2}.xml'.format(domain, 
                                                        service.lower(), 
                                                        time.strftime("%Y%m%d%H%M%S")))
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

    def delAllLocalServiceXML(self, services=['wfs', 'wmts']):
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

    def purgeCache(self):
        """
        Delete all cached documents but the 
        most current
        """
        file_metadata={}
        os.chdir(self.pl_settings_dir)
        cache_files = glob.glob('*_*_[0-9]*.xml')

        # Get cache metadata
        for f in cache_files:
            file_data=re.search(r'(?P<domain>.*)(_)(?P<service>wmts|wfs)(_)(?P<time>[0-9]+)\.xml', f)
            domain=file_data.group('domain') 
            service=file_data.group('service') 
            timestamp=file_data.group('time') 
            if domain not in file_metadata:
                file_metadata[domain]={}
            if service not in file_metadata[domain]:
                file_metadata[domain][service]=[]
            file_metadata[domain][service].append(timestamp)

        # get list of most current
        curr_files = []
        for dom, v in file_metadata.items():
            for ser , file_times in v.items():
                curr_files.append('{0}_{1}_{2}.xml'.format(dom, 
                                                           ser, 
                                                           sorted(file_times)[-1]))

        # del old files
        for file in cache_files:
            if file not in curr_files:
                self.delLocalSeviceXML(file)

    def serviceXmlIsLocal(self, file=None):
        """
        Test if the cached capabilties xml doc exists
        and if so set the services file to match this
        :param file: file name 
        :type file: str
        @return: boolean. True file exists
        @rtype: boolean
        """

        if not file:
            os.chdir(self.pl_settings_dir)
            files = glob.glob('{0}_{1}_*.xml'.format(self.domain, 
                                                    self.service.lower()))
            if files:
                self.file = sorted(files)[-1]
                return True
        return False

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

    def __init__(self, domain, service, service_version, api_key_instance, upd_cache=False):        
        """
        Initialise Service Data instance 

        :param service: Service Type (WMTS or WFS)
        :type service: str
        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service_version: {'wfs': '2.0.0', 'wmts': '1.0.0'}
        :type service_version: dict
        :param api_key_instance: API instance 
        :type api_key_instance: linz-data-importer.service_data.ApiKey
        """

        self.version = service_version[service]
        self.api_key_int = api_key_instance # using one instance as the user can change keys on us
        self.upd_cache=upd_cache
        Localstore.__init__(self, domain, service)
        # Data 
        self.obj = None #owslib data obj
        self.info = None # owslib data obj formatted for table
        self.err = None # any errors 
        self.disabled = False

    def isEnabled(self):
        """
        Test if the service is enable.
        Some services (e.g wmts) are disabled for specific domains. These
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
        Select method to obtain capabilities doc. 
        Either via localstore or internet 
        """

        # If cache get new data and overwrite local store
        if self.upd_cache:
            self.getServiceXml()
            return

        # Plugin opened for first time
        # Read data from local store if exists
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
            if self.service == 'wmts':
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
                if self.domain == 'basemaps.linz.govt.nz':
                    xml =  urlopen('https://{0}/v1/tiles/aerial/'
                                   'WMTSCapabilities.xml?api={1}'.format(self.domain,
                                                                         self.api_key_int.getApiKey(self.domain)))
                else:
                    xml =  urlopen('https://{0}/services;'
                                   'key={1}/{2}/{3}/WMTSCapabilities.xml'.format(self.domain,
                                                                                 self.api_key_int.getApiKey(self.domain), 
                                                                                 self.service.lower(),
                                                                                 self.version))


            elif self.service in ('wfs') and self.domain != 'basemaps.linz.govt.nz':
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
    
    def sortCrs(self):
        # wfs returns some no valid crs values
        valid = re.compile('^EPSG\:\d+')
        self.crs = [s for s in self.crs if valid.match(s)]
        # sort
        self.crs.sort(key = lambda x: int(x.split(':')[1]))
    
    def formatForUI(self):
        """
        Format the service data to display in the UI 
        """
        
        service_data = []
        cont = self.obj.contents
        for dataset_id, dataset_obj in cont.items():
            self.crs=[]
            if self.domain == 'basemaps.linz.govt.nz':
              id = dataset_obj.id
              type = 'layer'
            else:
              full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
              type = full_id.group('type')
              id = full_id.group('id')
            # Get and standarise espg codes
            if self.service == 'wmts':
                self.crs = dataset_obj.tilematrixsets
                self.sortCrs()
            elif self.service in ('wfs'):
                self.crs = dataset_obj.crsOptions
                self.crs = ['EPSG:{0}'.format(item.code) for item in self.crs]
                self.sortCrs()
 
            service_data.append([self.domain, type, self.service.upper(), id,
                                 dataset_obj.title, dataset_obj.abstract, self.crs])

        self.info = service_data

