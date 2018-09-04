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
from lxml.etree import XMLSyntaxError
from urllib2 import urlopen, URLError

from PyQt4.QtCore import QSettings

class ApiKey():
    # no longer storing properties
    # this allows the controllers instance
    # to change it and not have
    # to update all other instances
#     def __init__(self):
#        pass

    def getApiKey(self):
        key = QSettings().value('ldsplugin/apikey') 
        if not key:
            return ''
        return key

    def setApiKey(self, key):
        QSettings().setValue('ldsplugin/apikey', key)
        self.api_key = self.getApiKey()

class Localstore():
    """ data service objects managing of the local store
    or can be initiated out side of the service_data and manage
    the local store """
    
    def __init__(self, service=None, file=None):
        self.service=service
        self.xml=None
        self.pl_settings_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), "ldsplugin")
        self.ensureSettingsDir()
        self.file=file
        if self.service:
            self.file = os.path.join(self.pl_settings_dir , 
                               'getcapabilities_{0}.xml'.format(service.lower()))

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

    def delAllLocalServiceXML(self, services=['wfs', 'wms', 'wmts']):
        for service in services:
            file = os.path.join(self.pl_settings_dir , 
                               'getcapabilities_{0}.xml'.format(service.lower()))
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

class ServiceData(Localstore, ApiKey):
    def __init__(self, service, service_version):
        self.version = service_version
        Localstore.__init__(self, service)
        # Data 
        self.obj =None #owslib data obj
        self.info = None # owslib data obj formatted for table
        self.err = None # any errors 


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

        # service info obj
        self.getServiceObj()
        if self.err=='XMLSyntaxError':
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
            self.err = 'XMLSyntaxError'

    def getServiceXml(self):

        try:
            if self.service == 'wmts':
                xml =  urlopen('https://data.linz.govt.nz/services;'
                               'key={0}/{1}/{2}/WMTSCapabilities.xml'.format(self.getApiKey(), 
                                                                             self.service.lower(),
                                                                             self.version))
            elif self.service in ('wms', 'wfs'):
                xml = urlopen('https://data.linz.govt.nz/services;'
                              'key={0}/{1}?service={2}&version={3}'
                              '&request=GetCapabilities'.format(self.getApiKey(), 
                                                                self.service.lower(),
                                                                self.service.upper(),
                                                                self.version))

            self.xml = xml.read()
            # write to cache
            with open(self.file, 'w') as f:
                f.write(self.xml)

        except URLError, e:
            if hasattr(e, 'reason'):
                self.err = 'Error: {0}'.format(e.reason)

            elif hasattr(e, 'code'):
                 self.err = 'Error: {0}'.format(e.code)

    def serviceInfo(self):
        service_data = []
        cont = self.obj.contents

        for dataset_id, dataset_obj in cont.iteritems():
            full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
            type = full_id.group('type')
            id  =  full_id.group('id')
            service_data.append([type, id, self.service.upper(), dataset_obj.title, dataset_obj.abstract])

        self.info = service_data
