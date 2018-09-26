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

# This program is released under the terms of the 3 clause BSD license. See the
# LICENSE file for more information.

from PyQt4.QtCore import (QSettings, QTranslator, qVersion, QCoreApplication, 
                          Qt, QRegExp, QSize, Qt) 

from PyQt4.QtGui import (QAction, QIcon, QListWidgetItem, QSortFilterProxyModel,
                         QHeaderView, QMenu, QToolButton, QPixmap, QImage)
from qgis.core import (QgsRasterLayer, QgsVectorLayer, QgsMapLayerRegistry, 
                       QgsCoordinateReferenceSystem)
from qgis.gui import QgsMessageBar
from tablemodel import TableModel, TableView
from service_data import ServiceData, Localstore, ApiKey

import re
import urllib.request
import threading
import time
import os.path
from owslib import wfs, wms, wmts

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from gui.Service_dialog import ServiceDialog

# Hardcoded service .see #20 for enhancement
SER=['',
    'geodata.nzdf.mil.nz',
    'data.linz.govt.nz',
    'data.mfe.govt.nz',
    'datafinder.stats.govt.nz',
    'lris.scinfo.org.nz',
    'OTHER'
    ]

SER_TYPES=['wmts', 'wms', 'wfs']

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(CustomSortFilterProxyModel, self).__init__(parent)
        self.service_type = ('WMS', 'WMTS', 'WFS')

    def setServiceType(self, service_type):
        self.service_type = service_type
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index2 = self.sourceModel().index(sourceRow, 3, sourceParent) # SERVICE TYPE
        index3 = self.sourceModel().index(sourceRow, 4, sourceParent)

        return  (self.sourceModel().data(index2, Qt.DisplayRole) in self.service_type
            and self.filterRegExp().indexIn(self.sourceModel().data(index3, Qt.DisplayRole)) >= 0) 

class LinzDataImporter:
    """
    QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """
        Constructor.
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
            'linz-data-importer{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.toolbar = self.iface.addToolBar(u'LINZ Data Importer')
        self.toolbar.setObjectName(u'LINZ Data Importer')
        self.tool_button = QToolButton()
        self.menu = self.tr(u'&linz-data-importer')

        # Track data reading
        self.data_feeds = {}
        self.domains = []
        self.domain = None #curr domain
        self.row = None
        self.service = None
        self.id = None
        self.layer_title = None
        self.wmts_epsg = 'EPSG:3857'
        self.wmts_epsg_int = 3857
        self.service_versions = {'wfs': '2.0.0', 
                        'wms': '1.1.1' , 
                        'wmts': '1.0.0'}

        # Instances 
        self.api_key_instance = ApiKey() # TODO / REVIEW NEED OF
        self.local_store = Localstore()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LinzDataImporter', message)

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
        """
        Add a toolbar icon to the toolbar.

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
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initGui(self):
        """
        Create the menu entries and toolbar icons inside the QGIS GUI.
        """

        icon_path = ':/plugins/linz-data-importer/icons/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load Data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # Plugin Dialog 
        self.service_dlg = ServiceDialog()
        self.stacked_widget = self.service_dlg.qStackedWidget
        self.list_options = self.service_dlg.uListOptions
        self.list_options.itemClicked.connect(self.showSelectedOption)
        self.list_options.itemClicked.emit(self.list_options.item(0))
        self.curr_list_wid_index=0

        self.warning = self.service_dlg.uLabelWarning #TODO mix of uElements allocated to properties and others self.service_dlg.uLabelWarning.xxxxxx
        self.warning.setStyleSheet('color:red')
        self.warningSettings = self.service_dlg.uWarningSettings
        self.warningSettings.setStyleSheet('color:red')

        self.img_preview = self.service_dlg.uLabelImgPreview

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

        #set table model
        self.setTableModelView()

        #set about html
        self.service_dlg.hAboutHtml.setOpenExternalLinks(True)
        about_file = os.path.join(self.plugin_dir, 'about.html')
        icon_path = os.path.join(self.plugin_dir, 'icons')
        with open(about_file) as file:
            about_html = file.read().decode("utf-8")
            about_html.format(self.plugin_dir)
        self.service_dlg.hAboutHtml.setHtml(about_html.format(icon_path))

        # populate settings
        # default data services to combo TODO/ IMPROVE Dropdown should be ord name

        self.service_dlg.uComboBoxDomain.addItems(SER)

        #settings signals
        self.service_dlg.uBtnAddDomain.clicked.connect(self.addNewDomain)
        for n in range(1,11):
            getattr(self.service_dlg, 'uBtnSaveDomain{0}'.format(n)).clicked.connect(self.saveDomain)
            getattr(self.service_dlg, 'uBtnRemoveDomain{0}'.format(n)).clicked.connect(self.saveDomain)
        self.loadSettings()

    def clearSettings(self):
        """ 
        Removes text from settings QLineEdits 
        """

        for n in range(1,11):
            getattr(self.service_dlg, 'uTextDomain{0}'.format(n)).setText('')
            getattr(self.service_dlg, 'uTextAPIKey{0}'.format(n)).setText('')

    def loadSettings(self):
        """ 
        1. Populate settings QLineEdits with domain /
        API keys as stored via service_data.ApiKey().
        2. Hide all the settings QLineEdits that do not
        have text. 
        """

        self.domains=[]
        self.clearSettings()
        api_keys = self.api_key_instance.getApiKeys()
        if api_keys:
            for domain, api_key in api_keys.items():
                self.domains.append(domain)
                getattr(self.service_dlg, 'uTextDomain{0}'.format(len(self.domains))).setText(domain)
                getattr(self.service_dlg, 'uTextAPIKey{0}'.format(len(self.domains))).setText(api_key)

        # Hide un-populated domain rows
        for n in range(len(self.domains)+1,11):
            getattr(self.service_dlg, 'uTextDomain{0}'.format(n)).hide()
            getattr(self.service_dlg, 'uTextAPIKey{0}'.format(n)).hide()
            getattr(self.service_dlg, 'uBtnRemoveDomain{0}'.format(n)).hide()
            getattr(self.service_dlg, 'uBtnSaveDomain{0}'.format(n)).hide()

    def saveDomain(self):
        """ 
        Save all domain / API combinations as entered by the user.
        If the calling button was a remove button do not save 
        the text in the associated QLineEdits. 
        """

        del_domain = 0
        save_domain = 0

        sending_btn = self.service_dlg.sender().objectName()
        if sending_btn[:-1] == 'uBtnRemoveDomain':
            del_domain = sending_btn[-1]
        if sending_btn[:-1] == 'uBtnSaveDomain':
            save_domain = sending_btn[-1]

        keys = {}
        for n in range (1, len(self.domains)+2):
            if int(del_domain) == n:
                continue
            domain = getattr(self.service_dlg, 'uTextDomain{0}'.format(n)).text()
            key = getattr(self.service_dlg, 'uTextAPIKey{0}'.format(n)).text().strip()
            if domain and key:
                keys[domain]=key
        self.api_key_instance.setApiKeys(keys)

        #remove store capability docs for the removed or add domain/key
        # if they already exits .i.e these will be reloaded
        if save_domain: ui_elem_num = save_domain
        else: ui_elem_num = del_domain

        domain = getattr(self.service_dlg, 'uTextDomain{0}'.format(ui_elem_num)).text()
        self.local_store.delDomainsXML(domain)

        # load / Reload service data
        self.loadSettings()
        self.warningSettings.hide()
        self.warning.hide()
        try:
            self.list_options.setCurrentItem(self.curr_list_wid_index)
        except: 
            self.list_options.setCurrentRow(0)

        self.stacked_widget.setCurrentIndex(0)
        self.services_loaded = False # key change, load data again
        self.loadUi()

    def addNewDomain(self):
        """ 
        Connected to the dialogs uBtnAddDomain button.
        When the button is clicked add a new row
        domain and API QLineEdits
        """

        domain = self.service_dlg.uComboBoxDomain.currentText()

        if domain in self.domains:
            self.service_dlg.uWarningSettings.show()
            self.warningSettings.setText('Warning: Domains must be unique. '
                                                      'Please edit the domain below')
            return

        if len(self.domains)>=10:
            self.service_dlg.uWarningSettings.show()
            self.warningSettings.setText('Warning: You can only store up to . '
                                                      '10 domain entries')
            return

        if domain == 'OTHER': domain='' 
        getattr(self.service_dlg, 'uTextDomain{0}'.format(len(self.domains)+1)).setText(domain)
        getattr(self.service_dlg, 'uTextDomain{0}'.format(len(self.domains)+1)).show()
        getattr(self.service_dlg, 'uTextAPIKey{0}'.format(len(self.domains)+1)).show()
        getattr(self.service_dlg, 'uBtnRemoveDomain{0}'.format(len(self.domains)+1)).show()
        getattr(self.service_dlg, 'uBtnSaveDomain{0}'.format(len(self.domains)+1)).show()
        self.service_dlg.uWarningSettings.hide()

    def unload(self):
        """
        Removes the plugin menu item and icon from QGIS GUI.
        """

        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&linz-data-importer'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """ 
        Connected to the plugins tool bar icon. 
        load the table data and show the main UI.
        """

        if not self.services_loaded:
            if not self.api_key_instance.getApiKeys():
                self.warning.setText('ERROR: No API Details Provided - see settings')
                self.warning.show()
            else:
                self.loadUi()
                if not self.cache_updated and self.update_cache:
                    self.updateServiceDataCache()
        self.service_dlg.show()

    def updateServiceDataCache(self):
        """ 
        Update the local cache by deleting the locally stored capability 
        documents and then re-fetching from the associated web resource
        """

        while not self.services_loaded:
            time.sleep(10)
            continue
        self.services_loaded=False
        self.local_store.delAllLocalServiceXML()
        t = threading.Thread(target=self.loadAllServices)
        t.start()
        self.cache_updated=True

    def loadUi(self):
        """ 
        Wrapper for loadAllServices() to handle any errors
        """

        load_data_err = self.loadAllServices()
        if load_data_err:
            self.warning.setText(load_data_err)
            self.warning.show()
            self.update_cache=False
        else:
            self.warning.hide()

    def loadAllServices(self):
        """ 
        Iterate over all domains and service types (WMS, WMTS, WFS). 
        Request, process, store and format capability documents
        """

        all_data = [] 
        for domain in self.api_key_instance.getApiKeys():
            for service in SER_TYPES:
                # set service_data obj e.g self.linz_wms = service_data obj
                data_feed = '{0}_{1}'.format(domain, service) # eg linz_wms
                setattr(self, data_feed, ServiceData(domain,
                                                     service, 
                                                     self.service_versions,
                                                     self.api_key_instance)) 
                service_data_instance = getattr(self, data_feed)
                self.data_feeds[data_feed]=service_data_instance #keep record of ser data insts
                service_data_instance.processServiceData()
                if service_data_instance.disabled:
                    continue
                if service_data_instance.err:
                    return service_data_instance.err
                all_data.extend(service_data_instance.info)
        self.table_model.setData(all_data)
        self.services_loaded = True
        return None

    def showSelectedOption(self, item):
        """
        Connected to left pane QListWidget TOC. When items in the QListWidget 
        are clicked, display the associated Tab. If 'WMS', 'WMTS', 
        'WFS' or 'ALL' apply the filter to the tables proxy model

        :param item: The item in the QListWidget that was clicked
        :type item: QListWidgetItem
        """

        if item:
            if item.text() == 'ALL':
                self.stacked_widget.setCurrentIndex(0)
                self.curr_list_wid_index = self.list_options.findItems(item.text(), Qt.MatchExactly)[0]
                self.proxy_model.setServiceType(('WMS', 'WMTS', 'WFS'))
            elif item.text() == 'WFS':
                self.proxy_model.setServiceType((item.text()))
                self.curr_list_wid_index = self.list_options.findItems(item.text(), Qt.MatchExactly)[0]
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WMTS':
                self.proxy_model.setServiceType((item.text()))
                self.curr_list_wid_index = self.list_options.findItems(item.text(), Qt.MatchExactly)[0]
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'WMS':
                self.curr_list_wid_index=0
                self.curr_list_wid_index = self.list_options.findItems(item.text(), Qt.MatchExactly)[0]
                self.proxy_model.setServiceType((item.text()))
                self.stacked_widget.setCurrentIndex(0)
            elif item.text() == 'Settings':
                self.stacked_widget.setCurrentIndex(1)
            elif item.text() == 'About':
                self.stacked_widget.setCurrentIndex(2)

    def getPreview(self, res, res_timeout):
        """
        Fetch the preview image from the internet

        :param res: The resolution of the image to be fetched
        :type res: str
        :param res_timeout: How long the request should wait for a response 
        :type res_timeout: int
        """

        self.qimage = QImage()
        url = ('http://koordinates-tiles-d.global.ssl.fastly.net'
            '/services/tiles/v4/thumbnail/layer={0},style=auto/{1}.png'.format(self.id, res))
        try:
            img_data = urllib.request.urlopen(url, timeout=res_timeout).read()
        except:
            return False
        self.qimage.loadFromData(img_data)
        if res == '300x200':
            self.img_preview.setPixmap(QPixmap(self.qimage))
        else:
            self.img_preview.setPixmap(QPixmap(self.qimage).scaledToHeight(200))
        return True

    def updPreview(self):
        """ 
        On the tableviews rowChanged fetch the datasets preview image 
        """

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

    def currSelection(self):
        """
        On the tableviews currentRowChanged store the details of the current 
        record Also, update the abstract as shown in the UI
        """

        self.domain = self.row[0]
        abstract = self.row[5]
        self.service_type = self.row[1]
        self.id = self.row[2]
        self.service = self.row[3]
        self.layer_title = self.row[4]
        self.service_dlg.uTextDescription.setText(abstract)

    def userSelection(self, selected):
        """
        wrapper for methods required when the tableviews currentRowChanged

        :param res: Current item tableView item 
        :type res: QModelIndex
        """

        sourceIndex = self.proxy_model.mapToSource(selected)
        self.row = self.table_model.selectedRow(sourceIndex.row())

        self.currSelection()
        self.updPreview()

    def filterTable(self):
        """
        Filter the table data when uTextFilter.textChanged
        """

        filter_text = self.service_dlg.uTextFilter.text()
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(3)
        self.proxy_model.setFilterRegExp(filter_text)

    def setTableModelView(self):
        """
        Connect the tableView to the proxy model to the table model
        """
        # Set Table Model
        data = [['','','','','']]

        headers = ['domain', 'type','id', 'service', 'layer', 'hidden']
        self.proxy_model = CustomSortFilterProxyModel()
        self.table_view = self.service_dlg.uDatasetsTableView
        self.table_model = TableModel(data, headers)
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        # Trigger updating of data abstract on user selection
        self.selectionModel = self.table_view.selectionModel()
        self.selectionModel.currentRowChanged.connect(self.userSelection)

        # Table filtering trigger
        self.service_dlg.uTextFilter.textChanged.connect(self.filterTable)

        # Import Button Clicked
        self.service_dlg.uBtnImport.clicked.connect(self.importDataset)

    def mapCrs(self):
        """
        Return the current mapCanvas CRS

        @return: crs reference (e.g EPSG:3857)
        @rtype: str
        """

        crs = self.canvas.mapSettings().destinationCrs().authid()
        return crs

    def enableOTF(self):
        """
        Enable on the fly projection
        """

        if not self.iface.mapCanvas().hasCrsTransformEnabled():
            self.canvas.setCrsTransformEnabled(True)

    def setSRID(self):
        """ 
        Set the projects projection
        """

        crs = QgsCoordinateReferenceSystem(self.wmts_epsg_int,QgsCoordinateReferenceSystem.EpsgCrsId)
        self.canvas.setDestinationCrs(crs)

    def infoCRS(self):
        """
        Open a QgsMessageBar informing the projects crs has changed
        """

        self.iface.messageBar().pushMessage("Info", 
            '''The LINZ Data Importer Plugin has changed the projects CRS to {0} to 
            provide a common CRS when importing datasets'''.format(self.wmts_epsg),
                                             level=QgsMessageBar.INFO,
                                             duration=10)

    def zoomTo(self):
        ''' zoom to newly imported'''
        # Will seek user feedback. QGIS will 
        # Pan to first layer loaded
        pass

    def importDataset(self):
        """
        Import the selected dataset to QGIS
        """
        # MVP once a layer is imported the CRS is changed to ESPG:3857
        # and the user notified
        # ESPG:3857 as all WMTS datasets are served in the CRS

        self.enableOTF()
        if self.mapCrs() != self.wmts_epsg:
            self.setSRID()
            self.infoCRS()

        if self.service == "WFS":
            url = ("https://{0}/services;"
                   "key={1}/{2}?"
                   "SERVICE={2}&"
                   "VERSION={3}&"
                   "REQUEST=GetFeature&"
                   "TYPENAME={0}:{4}-{5}").format(self.domain,
                                                  self.api_key_instance.getApiKey(self.domain), 
                                                  self.service.lower(), 
                                                  self.service_versions[self.service.lower()], 
                                                  self.service_type, 
                                                  self.id)
            layer = QgsVectorLayer(url,
                                  self.layer_title,
                                  self.service.upper())  

        elif self.service == "WMS":
            uri = ("crs={1}&"
                   "dpiMode=7&"
                   "format=image/png&"
                   "layers={2}-{3}&"
                   "styles=&"
                   "url=https://{0}/services;"
                   "key={4}/{5}/{2}-{3}?"
                   "version={6}").format(self.domain,
                                         self.wmts_epsg, 
                                         self.service_type, 
                                         self.id, 
                                         self.api_key_instance.getApiKey(self.domain), 
                                         self.service.lower(), 
                                         self.service_versions[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                   'wms') 

        elif 'WMTS':
            uri = ("IgnoreAxisOrientation=1&SmoothPixmapTransform=1&"
                   "contextualWMSLegend=0&crs={1}&dpiMode=7&format=image/png&"
                   "layers={2}-{3}&styles=style%3Dauto&tileMatrixSet={1}&"
                   "url=https://{0}/services;"
                   "key={4}/{5}/{6}/{2}/{3}/"
                   "WMTSCapabilities.xml").format(self.domain,
                                                  self.wmts_epsg,
                                                  self.service_type, 
                                                  self.id, 
                                                  self.api_key_instance.getApiKey(self.domain), 
                                                  self.service.lower(), 
                                                  self.service_versions[self.service.lower()])
            layer = QgsRasterLayer(uri,
                                   self.layer_title,
                                  'wms')
        else: pass # ERRORnot supported

        QgsMapLayerRegistry.instance().addMapLayer(layer) 
        self.service_dlg.close()