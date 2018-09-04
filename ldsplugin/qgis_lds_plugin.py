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

# This program is released under the terms of the 3 clause BSD license. See the
# LICENSE file for more information.

from PyQt4.QtCore import (QSettings, QTranslator, qVersion, QCoreApplication, 
                          Qt, QRegExp, QSize) 
from PyQt4.QtGui import (QAction, QIcon, QListWidgetItem, QSortFilterProxyModel,
                         QHeaderView, QMenu, QToolButton, QPixmap, QImage)
from qgis.core import (QgsRasterLayer, QgsVectorLayer, QgsMapLayerRegistry, 
                       QgsCoordinateReferenceSystem)
from qgis.gui import QgsMessageBar
from lds_tablemodel import LDSTableModel, LDSTableView
from service_data import ServiceData, Localstore, ApiKey
import re
import urllib.request
import threading
import time

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from gui.Service_dialog import ServiceDialog

#from gui.Test import Test
import os.path

from owslib import wfs, wms, wmts


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(CustomSortFilterProxyModel, self).__init__(parent)
        self.service_type = ('WMS', 'WMTS', 'WFS')

    def setServiceType(self, service_type):
        self.service_type = service_type
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index2 = self.sourceModel().index(sourceRow, 2, sourceParent) # SERVICE TYPE
        index3 = self.sourceModel().index(sourceRow, 3, sourceParent)

        return  (self.sourceModel().data(index2, Qt.DisplayRole) in self.service_type
            and self.filterRegExp().indexIn(self.sourceModel().data(index3, Qt.DisplayRole)) >= 0) 


class QgisLdsPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.services_loaded = False
        self.cache_updated = False
        self.update_cache = True # Skip cache updates. Useful for testing.

        # initialise plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QgisLdsPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.toolbar = self.iface.addToolBar(u'QgisLdsPlugin')
        self.toolbar.setObjectName(u'QgisLdsPlugin')
        self.tool_button = QToolButton()
        self.menu = self.tr(u'&QGIS-LDS-Plugin')

        # Track data reading
        self.row = None
        self.service = None
        self.id = None
        self.layer_title = None
        self.wmts_epsg = 'EPSG:3857'
        self.service_versions = {'wfs': '2.0.0', 
                        'wms': '1.1.1' , 
                        'wmts': '1.0.0'}

        # Instances 
        self.api_key = ApiKey()
        self.local_store = Localstore()
        self.wmts_data = ServiceData('wmts',
                                     self.service_versions['wmts'])
        self.wfs_data = ServiceData('wfs', 
                                    self.service_versions['wfs'])
        self.wms_data = ServiceData('wms', 
                                    self.service_versions['wms'])

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QgisLdsPlugin', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type         index1 = self.sourceModel().index(sourceRow, 1, sourceParent)
        index2 = self.sourceModel().index(sourceRow, 2, sourceParent)text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: boloadWMSol

        :param add_to_menu: Flag incdicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QgisLdsPlugin/icons/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load LDS Data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # Plugin Dialog 
        self.service_dlg = ServiceDialog()
        self.stacked_widget = self.service_dlg.qStackedWidget
        self.list_options = self.service_dlg.uListOptions
        self.list_options.itemClicked.connect(self.showSelectedOption)
        self.list_options.itemClicked.emit(self.list_options.item(0))

        self.warning = self.service_dlg.uLabelWarning
        self.warning.setStyleSheet('color:red')

        self.img_preview = self.service_dlg.uImagePreview

        item = QListWidgetItem("ALL")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "all.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WFS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "wfs.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WMS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "wms.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("WMTS")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "wmts.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("Settings")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "settings.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        item = QListWidgetItem("About")
        image_path = os.path.join(os.path.dirname(__file__), "icons", "about.png")
        item.setIcon(QIcon(image_path))
        self.list_options.addItem(item)

        # add placeholder api key to ui
        self.showApiKey()

        #set table model
        self.setTableModelView()

        #set about html
        about_file = os.path.join(self.plugin_dir, 'about.html')
        icon_path = os.path.join(self.plugin_dir, 'icons')
        with open(about_file) as file:
            about_html = file.read()
            about_html.format(self.plugin_dir)
        self.service_dlg.hAboutHtml.setHtml(about_html.format(icon_path))

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&QGIS-LDS-Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        if not self.services_loaded:
            self.loadUi()
        self.service_dlg.show()
        if not self.cache_updated and self.update_cache:
            self.updateServiceDataCache()

    def updateServiceDataCache(self):

        while not self.services_loaded:
            time.sleep(10)
            continue
        self.services_loaded=False
        self.local_store.delAllLocalServiceXML()
        t = threading.Thread(target=self.loadAllServices)
        t.start()
        self.cache_updated=True

    def loadUi(self):
        # load data to tables if API key has been set
        if not self.api_key.getApiKey():
            self.warning.setText('Error: LDS API key must be provided - see settings')

        else:
            load_data_err = self.loadAllServices()
            if load_data_err:
                self.warning.setText(load_data_err)
                self.warning.show()
            else:
                self.warning.hide()

    def setApiKey(self):
        key = self.service_dlg.uTextAPIKey.text()
        self.api_key.setApiKey(key)
        self.warning.hide()
        self.local_store.delAllLocalServiceXML()
        self.services_loaded = False # key change, load data again
        self.stacked_widget.setCurrentIndex(0)
        self.loadUi()

    def showApiKey(self):
        curr_key = self.api_key.getApiKey()
        if curr_key == '':
            curr_key = 'No API Key stored. Please save a valid API Key'
        self.service_dlg.uTextAPIKey.setPlaceholderText(curr_key)

    def showSelectedOption(self, item):
        if item:
            if item.text() == 'ALL':
                self.stacked_widget.setCurrentIndex(0)
                self.proxy_model.setServiceType(('WMS', 'WMTS', 'WFS'))
            elif item.text() == 'WFS':
                self.proxy_model.setServiceType((item.text()))
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WMTS':
                self.proxy_model.setServiceType((item.text()))
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WMS':
                self.proxy_model.setServiceType((item.text()))
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'Settings':
                self.stacked_widget.setCurrentIndex(1)
            elif item.text() == 'About':
                self.stacked_widget.setCurrentIndex(2)

    def getPreview(self, res, res_timeout):
        image = QImage()
        url = ('http://koordinates-tiles-d.global.ssl.fastly.net'
            '/services/tiles/v4/thumbnail/layer={0},style=auto/{1}.png'.format(self.id, res))
        try:
            data = urllib.request.urlopen(url, timeout=res_timeout).read()
        except:
            return False
        image.loadFromData(data)
        if res == '300x200':
            self.img_preview.setPixmap(QPixmap(image))
        else:
            self.img_preview.setPixmap(QPixmap(image).scaledToHeight(200))
        return True

    def updDescription(self):
        abstract = self.row[4]
        self.service_type = self.row[0]
        self.id = self.row[1]
        self.service = self.row[2]
        self.layer_title = self.row[3]
        self.service_dlg.uTextDescription.setText(abstract)

    def updPreview(self):
        if self.service_type != 'layer':
            self.img_preview.clear()
            self.img_preview.setText('No preview available')
            return 

        if self.getPreview('300x200',0.5):
            return
        elif self.getPreview('150x100',5):
            return 
        else:
            self.img_preview.clear()
            self.img_preview.setText('No preview available')

    def userSelection(self, selected):
        sourceIndex = self.proxy_model.mapToSource(selected)
        self.row = self.table_model.selectedRow(sourceIndex.row())

        self.updDescription()
        self.updPreview()

    def filterTable(self):
        filter_text = self.service_dlg.uTextFilter.text()
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(3)
        self.proxy_model.setFilterRegExp(filter_text)

    def setTableModelView(self):
        # Set Table Model
        data = [['','','','']]

        headers = ['type','id', 'service', 'layer', 'hidden']
        self.proxy_model = CustomSortFilterProxyModel()
        self.table_view = self.service_dlg.uDatasetsTableView
        self.table_model = LDSTableModel(data, headers)
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)   
        self.table_view.horizontalHeader().setStretchLastSection(True)

        # Trigger updating of data abstract on user selection
        selectionModel = self.table_view.selectionModel()
        selectionModel.currentRowChanged.connect(self.userSelection)

        # Table filtering trigger
        self.service_dlg.uTextFilter.textChanged.connect(self.filterTable)

        # Import Button Clicked
        self.service_dlg.uBtnImport.clicked.connect(self.importDataset)

        # Save API Key Cicked
        self.service_dlg.uBtnSaveApiKey.clicked.connect(self.setApiKey)

    def loadAllServices(self):
        #services=['wmtsData', 'wmsData', 'wfsData']
        services=['wmts', 'wms', 'wfs']
        all_data = []
        for service in services:
            # service data object e.g self.wms_data
            serv_data = getattr(self, '{0}_data'.format(service))
            serv_data.processServiceData()
            if serv_data.err:
                return serv_data.err
                break
            all_data.extend(serv_data.info)
        self.dataToTable(all_data)
        self.services_loaded = True
        return None

    def dataToTable(self, table_data):
        self.table_model.setData(table_data)

    def mapCrs(self):
        crs = str(self.canvas.mapSettings().destinationCrs().authid())
        return crs

    def enableOTF(self):
        if not self.iface.mapCanvas().hasCrsTransformEnabled():
            self.canvas.setCrsTransformEnabled(True)

    def setSRID(self):
        crs = QgsCoordinateReferenceSystem(3857,QgsCoordinateReferenceSystem.EpsgCrsId)
        self.canvas.setDestinationCrs(crs)

    def infoCRS(self):
        self.iface.messageBar().pushMessage("Info", 
            '''LDS Plugin has changed the projects CRS to {0} to 
            provide a common CRS when importing LDS datasets'''.format(self.wmts_epsg),
                                             level=QgsMessageBar.INFO,
                                             duration=10)

    def zoomTo(self):
        ''' zoom to newly imported'''
        # Will seek user feedback. QGIS will 
        # Pan to first layer loaded
        pass

    def importDataset(self):
        # MVP once a layer is imported the CRS is changed to ESPG:3857
        # and the user notified
        # ESPG:3857 as all WMTS datasets are served in the CRS

        self.enableOTF()
        if self.mapCrs() != self.wmts_epsg:
            self.setSRID()
            self.infoCRS()

        if self.service == "WFS":
            url = ("https://data.linz.govt.nz/services;"
                   "key={0}/{1}?"
                   "SERVICE={1}&"
                   "VERSION={2}&"
                   "REQUEST=GetFeature&"
                   "TYPENAME=data.linz.govt.nz:{3}-{4}").format(self.api_key.getApiKey(), 
                                                                self.service.lower(), 
                                                                self.service_versions[self.service.lower()], 
                                                                self.service_type, 
                                                                self.id)
            layer = QgsVectorLayer(url,
                                  self.layer_title,
                                  self.service.upper())  

        elif self.service == "WMS":
            uri = ("crs={0}&"
                   "dpiMode=7&"
                   "format=image/png&"
                   "layers={1}-{2}&"
                   "styles=&"
                   "url=https://data.linz.govt.nz/services;"
                   "key={3}/{4}/{1}-{2}?"
                   "version={5}").format(self.wmts_epsg, 
                                        self.service_type, 
                                        self.id, 
                                        self.api_key.getApiKey(), 
                                        self.service.lower(), 
                                        self.service_versions[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                   'wms') 

        elif 'WMTS':
            uri = ("IgnoreAxisOrientation=1&SmoothPixmapTransform=1&"
                   "contextualWMSLegend=0&crs={0}&dpiMode=7&format=image/png&"
                   "layers={1}-{2}&styles=style%3Dauto&tileMatrixSet={0}&"
                   "url=https://data.linz.govt.nz/services;"
                   "key={3}/{4}/{5}/{1}/{2}/"
                   "WMTSCapabilities.xml").format(self.wmts_epsg,
                                                self.service_type, 
                                                self.id, 
                                                self.api_key.getApiKey(), 
                                                self.service.lower(), 
                                                self.service_versions[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                  'wms')
        else: pass # ERRORnot supported

        QgsMapLayerRegistry.instance().addMapLayer(layer) 
        self.service_dlg.close()
