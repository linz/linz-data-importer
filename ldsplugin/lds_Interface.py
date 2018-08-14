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
#from owslib.feature.wfs200 import WebFeatureService_2_0_0

from owslib.wmts import WebMapTileService
from owslib.util import ServiceException 
from qgis.core import QgsMessageLog, QgsNetworkAccessManager

from urllib2 import urlopen, URLError

class LdsInterface():
    def __init__(self, api_key_instance, service_versions):
        self.api_key_instance = api_key_instance
        self.key = self.api_key_instance.getApiKey()
        self.versions = service_versions

    def keyChanged(self):
        self.key = self.api_key_instance.getApiKey()

    def hasKey(self):
        if not self.key:
            return False
        return True

    def getServiceData(self, service):
        self.resp = {'err' : None,
                     'xml' : None,
                     'obj' : None,
                     'info': None}

        # Get service xml
        self.getServiceXml(service)
        if self.resp['err']:
            return self.resp

        # service info obj
        self.getServiceObj(service)

        # Format the response data
        self.serviceInfo(service)

        return self.resp

    def getServiceObj(self, service):

        if service == 'WMS':
            self.resp['obj'] = WebMapService(url=None, xml=self.resp['xml'], version='1.1.1')
        elif service == 'WMTS':
            self.resp['obj'] = WebMapTileService(url=None, xml=self.resp['xml'], version = '1.0',)
        elif service == 'WFS':
            self.resp['obj'] = WebFeatureService(url=None, xml=self.resp['xml'], version = '2.0',)

    def getServiceXml(self, service):

        try:
            if service == 'WMTS':
                f =  urlopen('https://data.linz.govt.nz/services;key={0}/{1}/{2}/WMTSCapabilities.xml'.format(self.key, 
                                                                                                                   service.lower(),
                                                                                                                   self.versions[service.lower()]))
            elif service in ('WMS', 'WFS'):
                f = urlopen('https://data.linz.govt.nz/services;key={0}/{1}?service={2}&version={3}&request=GetCapabilities'.format(self.key, 
                                                                                                                                service.lower(),
                                                                                                                                service,
                                                                                                                                self.versions[service.lower()]))
            self.resp['xml'] = f.read()

        except URLError, e:
            if hasattr(e, 'reason'):
                self.resp['err'] = 'Error: {0}'.format(e.reason)

            elif hasattr(e, 'code'):
                 self.resp['err'] = 'Error: {0}'.format(e.code)

    def serviceInfo(self, service):
        service_data = []
        cont = self.resp['obj'].contents

        for dataset_id, dataset_obj in cont.iteritems():
            full_id = re.search(r'([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)', dataset_obj.id)
            type = full_id.group('type')
            id  =  full_id.group('id')
            service_data.append([type, id, service, dataset_obj.title, dataset_obj.abstract])

        self.resp['info'] = service_data
