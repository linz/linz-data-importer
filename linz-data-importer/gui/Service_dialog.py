#TODO// header



import os
#from .ExtendedCombobox import ExtendedCombobox
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
             
