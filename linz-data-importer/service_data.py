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

class ServiceData():
    """
    Get, Store and Process WxS Data
    """

    def __init__(self, domain, service, service_version, api_key_instance):
        """
        Initialise Service Data instance 

        :param service: Service Type (WMTS, or WFS)
        :type service: str
        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service_version: {'wfs': '2.0.0', 'wmts': '1.0.0'}
        :type service_version: dict
        :param api_key_instance: API instance 
        :type api_key_instance: linz-data-importer.service_data.ApiKey
        """

        self.domain=domain
        self.version = service_version[service]
        self.api_key_int = api_key_instance # using one instance as the user can change keys on us
        # Data 
        self.obj = None #owslib data obj
        self.xml = None        
        self.service=service
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


    def processServiceData(self):
        """
        Get, process and format the service data
        """

        self.getServiceXml()
        if self.err:
            return

        # service info obj
        self.getServiceObj()

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
                xml =  urlopen('https://{0}/services;'
                               'key={1}/{2}/{3}/WMTSCapabilities.xml'.format(self.domain,
                                                                             self.api_key_int.getApiKey(self.domain), 
                                                                             self.service.lower(),
                                                                             self.version))

            elif self.service =='wfs':
                xml = urlopen('https://{0}/services;'
                              'key={1}/{2}?service={3}&version={4}'
                              '&request=GetCapabilities'.format(self.domain,
                                                                self.api_key_int.getApiKey(self.domain), 
                                                                self.service.lower(),
                                                                self.service.upper(),
                                                                self.version))
            self.xml = xml.read()

        except URLError as e:
            if hasattr(e, 'reason'):
                self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)

            elif hasattr(e, 'code'):
                 self.err = 'Error: ({0}) {1}'.format(self.domain, e.reason)
    
    def sortCrs(self):
        # wms returns some no valid crs values            
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

