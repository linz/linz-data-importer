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

from PyQt4.QtCore import  *
from PyQt4.QtGui import *
import sys


class LDSTableView(QTableView):
    
    """    
    @param QTableView: Inherits from QtGui.QWidget
    @param QTableView: QtGui.QTableView()
    """

    def __init__( self, parent=None ):
        """ 
        Initialise  View for AIMS Queues
        """

        QTableView.__init__( self, parent )
        # Change default settings
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(17)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)

class LDSTableModel(QAbstractTableModel):

    def __init__(self, data = [[]], headers = [], parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = data
        self.header = headers

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        try:
            return len(self.arraydata[0])-1 # hiding description
        except:
            return 0
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return unicode(self.arraydata[index.row()][index.column()])

    def setData(self, data):
        # refreshing all data in table
        self.layoutAboutToBeChanged.emit()
        self.arraydata = data
        self.layoutChanged.emit()

    def selectedRow(self, row):
        ''' 
        return the datasets abstract
        '''
        return self.arraydata[row]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable #obviously not the final product

