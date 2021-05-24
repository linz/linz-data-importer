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

from builtins import str

from qgis.PyQt.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt
from qgis.PyQt.QtWidgets import QComboBox, QCompleter

## Below model not currently in-use
# class TableView(QTableView):
#
#     """
#     :param QTableView: Inherits from QtGui.QWidget
#     :param QTableView: QtGui.QTableView()
#     """
#
#     def __init__( self, parent=None ):
#         """
#         Initialise  View for AIMS Queues
#
#         :param parent: QModelIndex
#         :param parent: PyQt4.QtCore.QModelIndex
#         """
#
#         QTableView.__init__( self, parent )
#         # Change default settings
#         self.setSelectionBehavior(QAbstractItemView.SelectRows)
#         self.horizontalHeader().setStretchLastSection(True)
#         self.horizontalHeader().setHighlightSections(False)
#
#         self.verticalHeader().setVisible(False)
#         self.verticalHeader().setDefaultSectionSize(17)
#         self.setSortingEnabled(True)
#         self.setEditTriggers(QAbstractItemView.AllEditTriggers)


class TableModel(QAbstractTableModel):
    """
    models that represent table data data as a two-dimensional array of items
    """

    def __init__(self, data, headers, parent=None):
        """
        Initialise  TableModel

        :param data: table data
        :param data: 2d array
        :param headers: list of headers
        :param headers: list
        :param parent: None
        :param parent: None
        """

        QAbstractTableModel.__init__(self, parent)
        self.arraydata = data
        self.header = headers

    def rowCount(self, parent):  # pylint:disable=invalid-name,unused-argument
        """
        Returns the number of rows under the given parent

        :param parent: QModelIndex
        :param parent: PyQt4.QtCore.QModelIndex
        :return: Count of rows
        :rtype: int
        """

        return len(self.arraydata)

    def columnCount(self, parent):  # pylint:disable=invalid-name,unused-argument
        """
        Returns the number of columns for the children of the given parent

        :param parent: QModelIndex
        :param parent: PyQt4.QtCore.QModelIndex
        :return: Count of columns
        :rtype: int
        """

        try:
            return len(self.arraydata[0]) - 2  # hiding description
        except:
            return 0

    def data(self, index, role):
        """
        Returns the data stored under the given role for the item referred to by the index

        :param parent: QModelIndex
        :param parent: PyQt4.QtCore.QModelIndex
        :param role: DisplayRole
        :param role: int
        :return: Data related to index
        :rtype: str
        """

        if not index.isValid():
            return None
        if role != Qt.DisplayRole:
            return None
        return str(self.arraydata[index.row()][index.column()])

    def setData(self, data):  # pylint:disable=invalid-name
        """
        Sets the role data for the item at index to value

        :param data: List of lists of row data
        :param data: 2d array
        """

        # refreshing all data in table
        self.layoutAboutToBeChanged.emit()
        self.arraydata = data
        self.layoutChanged.emit()

    def selectedRow(self, row):  # pylint:disable=invalid-name
        """
        Return data for row selected by user

        :param row: Selected Row Number
        :param row: int
        :return: List of row data
        :rtype: list
        """

        return self.arraydata[row]

    def headerData(self, col, orientation, role):  # pylint:disable=invalid-name
        """ "
        Returns the data for the given role and section in the header
        with the specified orientation.

        :param col: Selected Column Number
        :param col: int
        :param orientation: Orientation
        :param orientation: Qt.Orientation
        :param role: DisplayRole
        :param role: int
        :return: Header data
        :rtype: str
        """

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def flags(self, index):  # pylint:disable=no-self-use,unused-argument
        """
        Returns the item flags for the given index.

        :param index: QModelIndex
        :type index: PyQt4.QtCore.QModelIndex
        :return: ItemFlags
        :rtype: PyQt4.QtCore.ItemFlags
        """

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class ExtendedCombobox(QComboBox):
    """
    Overwrite combobox to provide text filtering of
    combobox list.
    """

    def __init__(self, parent):
        """
        Initialise  ExtendedCombobox

        :param parent: Parent of combobox
        :type parent: PyQt5.QtWidgets.QWidget
        """

        super().__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.completer = QCompleter(self)

        # always show all completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.p_filter_model = QSortFilterProxyModel(self)
        self.p_filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        self.lineEdit().textEdited.connect(self.p_filter_model.setFilterFixedString)
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

    def setModel(self, model):  # pylint:disable=invalid-name
        """
        Set the model to use the Filter model

        :param model: The model to be used by the combobox
        :type model: PyQt5.QtGui.QStandardItemModel
        """

        super().setModel(model)
        self.p_filter_model.setSourceModel(model)
        self.completer.setModel(self.p_filter_model)

    def setModelColumn(self, column):  # pylint:disable=invalid-name
        """
        :param model: The model to be used by the combobox
        :type model: PyQt5.QtGui.QStandardItemModel
        """

        self.completer.setCompletionColumn(column)
        self.p_filter_model.setFilterKeyColumn(column)
        super().setModelColumn(column)

    def view(self):
        """
        A QListView of items stored in the model

        :return: items stored in the model
        :rtype: PyQt5.QtWidgets.QListView
        """

        return self.completer.popup()

    def index(self):
        """
        Index of the current item in the combobox.

        :return: index of the current item
        :rtype: int
        """

        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):  # pylint:disable=invalid-name
        """
        :param text: The current text of the qlineedit
        :type text: str

        If the combobx lineedit is clicked, set the lineedits
        current item as the combobox's current item
        """

        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
