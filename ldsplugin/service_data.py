"""
/***************************************************************************
 QgisLdsPlugin
                                 A QGIS plugin
 Import LDS OGC Datasets into QGIS
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
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

from owslib.wmts import WebMapTileService
from owslib.util import ServiceException 
from qgis.core import QgsMessageLog, QgsApplication

import os.path
from lxml.etree import XMLSyntaxError, ElementTree
from urllib2 import urlopen, URLError

from PyQt4.QtCore import QSettings
from gc import isenabled

class ApiKey():
    # TODO// MAKE SINGLETON
    def __init__(self):
       self.api_keys = self.getApiKeys()

    def getApiKeys(self):
        keys = QSettings().value('ldsplugin/apikeys')
        if not keys:
            return {}
        return keys

    def getApiKey(self, domain):
        return self.api_keys[domain]

    def setApiKeys(self, keys):
        # = {domain:api_key}
        QSettings().setValue('ldsplugin/apikeys', keys)
        self.api_keys = self.getApiKeys()

class Localstore():
    """ data service objects managing of the local store
    or can be initiated out side of the service_data and manage
    the local store """

    def __init__(self, domain=None, service=None, file=None):
        self.domain=domain
        self.service=service
        self.xml=None
        self.pl_settings_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), "ldsplugin")
        self.ensureSettingsDir()
        self.file=file
        if self.service:
            self.file = os.path.join(self.pl_settings_dir , 
                               '{0}_{1}.xml'.format(domain, service.lower()))

    def ensureSettingsDir(self):
        if not os.path.exists(self.pl_settings_dir):
            os.makedirs(self.pl_settings_dir)

    def delLocalSeviceXML(self, file):
        if not file:
            file = self.file
        try:
            os.remove(file)
        except OSError:
            pass

    def delDomainsXML(self, domain):
        if not domain:
            domain = self.domain

        dir = self.pl_settings_dir
        for f in os.listdir(self.pl_settings_dir):
            if re.search(domain, f):
                file = os.path.join(dir, f)
                self.delLocalSeviceXML(file)

    def delAllLocalServiceXML(self, services=['wms','wfs','wmts']):
        search_str = '|'.join(['_{}.xml'.format(x) for x in services])

        dir = self.pl_settings_dir
        for f in os.listdir(self.pl_settings_dir):
            if re.search(search_str, f):
                file = os.path.join(dir, f)
                self.delLocalSeviceXML(file)

    def serviceXmlIsLocal(self, file=None):
        if not file:
            file = self.file
        return os.path.isfile(file)

    def readLocalServiceXml(self, file=None):
        if not file:
            file = self.file
        with open(file, 'r') as f:
            self.xml = f.read()

class ServiceData(Localstore):
    def __init__(self, domain, service, service_version, api_key_instance):
        self.version = service_version[service]
        self.api_key_int = api_key_instance # using instance as the user can change keys on us
        Localstore.__init__(self, domain, service)
        # Data 
        self.obj = None #owslib data obj
        self.info = None # owslib data obj formatted for table
        self.err = None # any errors 
        self.disabled = False
        
    def isEnabled(self):
        # Turns out some services are disabled
        # Will only know this based on the returned capabilities doc.
        # Though this doc has no header and is not simply xml parse-able
        # so... 
        disbaled_str = ('Service {0} is disabled').format(self.service.upper())
        if self.xml.find(disbaled_str) == -1:
            return True
        self.disabled = True
        return False
        
    def getServiceData(self):
        # Get service xml
        if self.serviceXmlIsLocal():
            self.readLocalServiceXml()
        else:
            self.getServiceXml()

    def getServiceDataTryAgain(self):
        pass
        ''' If the creating of the service obj fails
        due to xml syntax; delete and recreate local xml
        and try build the service obj again'''
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
        self.serviceInfo()

    def getServiceObj(self):
        try:
            if self.service == 'wms':
                self.obj = WebMapService(url=None, xml=self.xml, version=self.version)
            elif self.service == 'wmts':
                self.obj = WebMapTileService(url=None, xml=self.xml, version=self.version,)
            elif self.service == 'wfs':
                self.obj = WebFeatureService(url=None, xml=self.xml, version=self.version,)
        except XMLSyntaxError, e:
            #most likely the locally stored xml is corrupt
            self.err = '{0}: XMLSyntaxError'.formatt(self.domain)

    def getServiceXml(self):

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
            with open(self.file, 'w') as f:
                f.write(self.xml)

        except URLError, e:
            if hasattr(e, 'reason'):
                self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)

            elif hasattr(e, 'code'):
                 self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)

    def serviceInfo(self):
        service_data = []
        cont = self.obj.contents

        for dataset_id, dataset_obj in cont.iteritems():
            full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
            type = full_id.group('type')
            id  =  full_id.group('id')
            service_data.append([self.domain, type, id, self.service.upper(), dataset_obj.title, dataset_obj.abstract])

        self.info = service_data
