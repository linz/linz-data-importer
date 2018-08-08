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


from PyQt4.QtCore import QSettings

class ApiKey():
    def __init__(self):
        self.api_key = self.get_api_key()

    #TODO // change naming to Camel case
    def get_api_key(self):
        key = QSettings().value('ldsplugin/apikey') 
        if not key:
            return ''
        return key
    
    def set_api_key(self, key):
        QSettings().setValue('ldsplugin/apikey', key)
        self.api_key = self.get_api_key()
