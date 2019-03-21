# -*- coding: utf-8 -*-
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

 This script initializes the plugin, making it known to QGIS.
"""

import sys
from os.path import dirname, abspath
sys.path.append(dirname(abspath(__file__)))


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LinzDataImporter class from file linz_data_importer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .linz_data_importer import LinzDataImporter
    return LinzDataImporter(iface)
