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
import sys
import unittest

__location__ = os.path.dirname(os.path.realpath(__file__))


def run_test_modules():
    """
    Loops through all TestCase instances in a test folder to find
    unique test modules
    """
    test_suite = unittest.TestLoader().discover(__location__, pattern="test_*.py")
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(test_suite)
