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

import unittest
import time

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QListWidget,
    QTableView,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
)
from qgis.utils import plugins
from qgis.PyQt.Qt import QComboBox

WAIT = 1000


class UiTest(unittest.TestCase):
    """
    Just test UI elements. No data requests
    """

    def setUp(self):
        """
        Runs before each test.
        """

        self.ldi = plugins.get("linz-data-importer")
        self.ldi.actions[0].trigger()

    def tearDown(self):
        """
        Runs after each test
        """

        QTest.qWait(WAIT)  # Just because I want to watch it open a close
        self.ldi.dlg.close()
        self.services_loaded = False

        # Remove filter set tab back to "ALL"
        item = self.ldi.dlg.uListOptions.findItems("ALL", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

    def test_service_dialog_is_active(self):
        """
        Test UI dialog is show when Plugin is ran
        """
        self.assertTrue(self.ldi.dlg.isVisible())

    def test_elements_exist(self):
        """
        Test all ui elements exist
        and are of the expected types
        """

        # StackWidget - TableView
        self.assertEqual(type(self.ldi.dlg.uListOptions), QListWidget)
        self.assertEqual(type(self.ldi.dlg.uTableView), QTableView)
        self.assertEqual(type(self.ldi.dlg.uBtnImport), QPushButton)
        self.assertEqual(type(self.ldi.dlg.uTextFilter), QLineEdit)
        self.assertEqual(type(self.ldi.dlg.uTextDescription), QTextEdit)
        self.assertEqual(type(self.ldi.dlg.uLabelImgPreview), QLabel)
        self.assertEqual(type(self.ldi.dlg.uLabelWarning), QLabel)
        # StackWidget - Settings
        item = self.ldi.dlg.uListOptions.findItems("About", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(type(self.ldi.dlg.uComboBoxDomain), QComboBox)
        self.assertEqual(type(self.ldi.dlg.uBtnAddDomain), QPushButton)
        for n in range(1, 11):
            self.assertEqual(
                type(getattr(self.ldi.dlg, "uTextAPIKey{0}".format(n))), QLineEdit
            )
            self.assertEqual(
                type(getattr(self.ldi.dlg, "uTextAPIKey{0}".format(n))), QLineEdit
            )
            self.assertEqual(
                type(getattr(self.ldi.dlg, "uBtnRemoveDomain{0}".format(n))),
                QPushButton,
            )
            self.assertEqual(
                type(getattr(self.ldi.dlg, "uBtnSaveDomain{0}".format(n))), QPushButton
            )

    def test_sw_tableview_is_default(self):
        """
        The table view should be the first
        stack widget shown when plugin opened
        """

        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

    def test_listItem_about_shows_widget_swSettings(self):
        """
        Check the stacked widget index and siGnals
        When 'Settings' is clicked - the stacked widgets current index
        should now be == 1
        """

        item = self.ldi.dlg.uListOptions.findItems("Settings", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 1)

    def test_listItem_all_shows_widget_swTableView(self):
        """
        Check the stacked widget index and sinals
        When 'All' is clicked - the stacked widgets current index
        should now be == 0
        """

        item = self.ldi.dlg.uListOptions.findItems("ALL", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

    def test_listItem_about_shows_widget_swAbout(self):
        """
        Check the stacked widget index and sinals
        When 'All' is clicked - the stacked widgets current index
        should now be == 2
        """

        item = self.ldi.dlg.uListOptions.findItems("About", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 2)

    def test_listItem_wmts_shows_widget_swTableView(self):
        """
        Check the stacked widget index and sinals
        When 'WMTS' is clicked - the stacked widgets current index
        should now be == 0
        """
        item = self.ldi.dlg.uListOptions.findItems("WMTS", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

    def test_listItem_wfs_shows_widget_swTableView(self):
        """
        Check the stacked widget index and sinals
        When 'WFS' is clicked - the stacked widgets current index
        should now be == 0
        """

        item = self.ldi.dlg.uListOptions.findItems("WFS", Qt.MatchFixedString)[0]
        self.ldi.dlg.uListOptions.itemClicked.emit(item)
        self.assertEqual(self.ldi.dlg.uStackedWidget.currentIndex(), 0)

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(UiTest, "test"))
    return suite


def run_tests():
    unittest.TextTestRunner(verbosity=3).run(suite())
