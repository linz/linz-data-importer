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


import ast
import re
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService

from owslib.wmts import WebMapTileService
from owslib.util import ServiceException 
from qgis.core import QgsMessageLog, QgsApplication

import os.path
from lxml.etree import XMLSyntaxError
from urllib2 import urlopen, URLError

class LdsInterface():
    def __init__(self, api_key_instance, service_versions):
        self.api_key_instance = api_key_instance
        self.key = self.api_key_instance.getApiKey()
        self.versions = service_versions
        self.pl_settings_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), "ldsplugin")
        self.makeSettingsDir()
        self.file = None

    def makeSettingsDir(self):
        if not os.path.exists(self.pl_settings_dir):
            os.makedirs(self.pl_settings_dir)

    def keyChanged(self):
        self.key = self.api_key_instance.getApiKey()

    def hasKey(self):
        if not self.key:
            return False
        return True
    
    def getServiceData(self, service):
        # Get service xml
        if self.serviceXmlIsLocal(service):
            self.readLocalServiceXml(service)
        else:
            self.getServiceXml(service)

    def getServiceDataTryAgain(self, service):
        ''' If the creating of the service obj fails
        due to xml syntax; delete and recreate local xml
        and try build the service obj again'''
        #Clear error, Delete local file and get it a fresh
        self.resp['err']=None
        self.delLocalSeviceXML(self.file)
        self.getServiceData(service)
        if self.resp['err']:
            return
        self.getServiceObj(service)
        if self.resp['err']:
            return

    def processServiceData(self, service):
        self.file = os.path.join(self.pl_settings_dir , 
                                 'getcapabilities_{0}.xml'.format(service.lower()))

        self.resp = {'err' : None,
                     'xml' : None,
                     'obj' : None,
                     'info': None}

        self.getServiceData(service)
        if self.resp['err']:
            return self.resp

        # service info obj
        self.getServiceObj(service)
        if self.resp['err']=='XMLSyntaxError':
            self.getServiceDataTryAgain(service)
        if self.resp['err']:
            return self.resp
 
        # Format the response data
        self.serviceInfo(service)

        return self.resp

    def getServiceObj(self, service):
        try:
            if service == 'WMS':
                self.resp['obj'] = WebMapService(url=None, xml=self.resp['xml'], version='1.1.1')
            elif service == 'WMTS':
                self.resp['obj'] = WebMapTileService(url=None, xml=self.resp['xml'], version = '1.0',)
            elif service == 'WFS':
                self.resp['obj'] = WebFeatureService(url=None, xml=self.resp['xml'], version = '2.0',)
        except XMLSyntaxError, e:
            #most likely the locally stored xml is corrupt
            self.resp['err'] = 'XMLSyntaxError'

    def getServiceXml(self, service):

        try:
            if service == 'WMTS':
                xml =  urlopen('https://data.linz.govt.nz/services;key={0}/{1}/{2}/WMTSCapabilities.xml'.format(self.key, 
                                                                                                              service.lower(),
                                                                                                              self.versions[service.lower()]))
            elif service in ('WMS', 'WFS'):
                xml = urlopen('https://data.linz.govt.nz/services;key={0}/{1}?service={2}&version={3}&request=GetCapabilities'.format(self.key, 
                                                                                                                                    service.lower(),
                                                                                                                                    service,
                                                                                                                                    self.versions[service.lower()]))

            self.resp['xml'] = xml.read()
            with open(self.file, 'w') as f:
                f.write(self.resp['xml'])

        except URLError, e:
            if hasattr(e, 'reason'):
                self.resp['err'] = 'Error: {0}'.format(e.reason)

            elif hasattr(e, 'code'):
                 self.resp['err'] = 'Error: {0}'.format(e.code)

    def delLocalSeviceXML(self, file=None):
        try:
            os.remove(file)
        except OSError:
            pass

    def delAllLocalServiceXML(self):
        # THIS IS TEMP. THIS MODULE IS
        # NOW READY FOR A RE-FACTOR
        for service in ['wfs', 'wms', 'wmts']:
            file = os.path.join(self.pl_settings_dir , 
                               'getcapabilities_{0}.xml'.format(service.lower()))
            self.delLocalSeviceXML(file)

    def serviceXmlIsLocal(self, service):
        return os.path.isfile(self.file)

    def readLocalServiceXml(self, service):
        with open(self.file, 'r') as f:
            self.resp['xml'] = f.read()

    def serviceInfo(self, service):
        service_data = []
        cont = self.resp['obj'].contents

        for dataset_id, dataset_obj in cont.iteritems():
            full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
            type = full_id.group('type')
            id  =  full_id.group('id')
            service_data.append([type, id, service, dataset_obj.title, dataset_obj.abstract])

        self.resp['info'] = service_data
