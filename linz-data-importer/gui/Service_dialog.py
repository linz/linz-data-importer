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


import os
from PyQt5 import QtGui, QtWidgets, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Service_dialog_base.ui'))


class ServiceDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ServiceDialog, self).__init__(parent)
        self.setupUi(self)

        # Change look of list widget
        self.uListOptions.setStyleSheet(
            """ QListWidget {
                    background-color: rgb(105, 105, 105);
                    outline: 0;
                }
                QListWidget::item {
                    color: white;
                    padding: 3px;
                }
                QListWidget::item::selected {
                    color: black;
                    background-color:palette(Window);
                    padding-right: 0px;
                };
            """
        )
        # Decided to go with white
        #self.uTextDescription.setStyleSheet("background-color:palette(Window);")

        # add grey back ground to html view
#         self.hAboutHtml.setStyleSheet(
#             """ QTextEdit {
#                     background-color:rgb(245,245,245);
#                     outline: 0;
#                 }
#             """ 
#            )
             
