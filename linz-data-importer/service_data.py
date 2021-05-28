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

import glob
import os.path
import re
import time

from owslib.wfs import WebFeatureService
from owslib.wmts import WebMapTileService
from qgis.core import QgsApplication

try:
    from lxml.etree import XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import ParseError as XMLSyntaxError

from urllib.error import URLError
from urllib.request import urlopen

from qgis.PyQt.QtCore import QSettings


class ApiKey:
    """
    Store API Keys for each domain. Required to
    fetch service data
    """

    # TODO// MAKE SINGLETON
    def __init__(self):
        self.api_keys = self.get_api_keys()

    @staticmethod
    def get_api_keys():
        """
        Return Domain / API keys stored in QSettings

        @return: e.g. {domain1: api_key1, domain2: api_key2}
        @rtype: dict
        """

        keys = QSettings().value("linz_data_importer/apikeys")
        if not keys:
            return {}
        return keys

    def get_api_key(self, domain):
        """
        Returns an API Key related to a domain

        @return: API Key
        @rtype: str
        """

        return self.api_keys[domain]

    def set_api_keys(self, keys):
        """
        Save API Keys as Qsettings Value

        :param keys: {domain1: api_key1, domain2: api_key2...}
        :type keys: dict
        """

        # = {domain:api_key}
        QSettings().setValue("linz_data_importer/apikeys", keys)
        self.api_keys = self.get_api_keys()


class Localstore:
    """
    Caching of capability documents
    """

    def __init__(self, domain=None, service=None, file=None):
        """
        Initiate localstore

        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service: Service Type (WMTS or WFS)
        :type service: str
        :param file: file name
        :type file: str
        """

        self.domain = domain
        self.service = service
        self.xml = None
        self.pl_settings_dir = os.path.join(
            QgsApplication.qgisSettingsDirPath(), "linz-data-importer"
        )
        self.ensure_settings_dir()
        self.file = file
        if self.service:
            self.file = os.path.join(
                self.pl_settings_dir,
                "{0}_{1}_{2}.xml".format(
                    domain, service.lower(), time.strftime("%Y%m%d%H%M%S")
                ),
            )

    def ensure_settings_dir(self):
        """
        Create the plugins settings dir if not exists
        """

        if not os.path.exists(self.pl_settings_dir):
            os.makedirs(self.pl_settings_dir)

    def del_local_sevice_xml(self, file=None):
        """
        Delete a single file
        """

        if not file:
            file = self.file
        try:
            os.remove(file)
        except OSError:
            pass

    def del_domains_xml(self, domain):
        """
        Delete all cached files associated with a domain

        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain str
        """

        if not domain:
            domain = self.domain

        dir = self.pl_settings_dir
        for filename in os.listdir(self.pl_settings_dir):
            if re.search(domain, filename):
                file = os.path.join(dir, filename)
                self.del_local_sevice_xml(file)

    def del_all_local_service_xml(self, services=None):
        """
        Find and delete all cached files

        :param domain: list services
        :type domain: list
        """
        if services is None:
            services = ["wfs", "wmts"]

        search_str = "|".join(["_{}.xml".format(x) for x in services])

        dir = self.pl_settings_dir
        for filename in os.listdir(self.pl_settings_dir):
            if re.search(search_str, filename):
                file = os.path.join(dir, filename)
                self.del_local_sevice_xml(file)

    def purge_cache(self):
        """
        Delete all cached documents but the
        most current
        """
        file_metadata = {}
        os.chdir(self.pl_settings_dir)
        cache_files = glob.glob("*_*_[0-9]*.xml")

        # Get cache metadata
        for filename in cache_files:
            file_data = re.search(
                r"(?P<domain>.*)(_)(?P<service>wmts|wfs)(_)(?P<time>[0-9]+)\.xml",
                filename,
            )
            domain = file_data.group("domain")
            service = file_data.group("service")
            timestamp = file_data.group("time")
            if domain not in file_metadata:
                file_metadata[domain] = {}
            if service not in file_metadata[domain]:
                file_metadata[domain][service] = []
            file_metadata[domain][service].append(timestamp)

        # get list of most current
        curr_files = []
        for dom, service_properties in file_metadata.items():
            for ser, file_times in service_properties.items():
                curr_files.append(
                    "{0}_{1}_{2}.xml".format(dom, ser, sorted(file_times)[-1])
                )

        # del old files
        for file in cache_files:
            if file not in curr_files:
                self.del_local_sevice_xml(file)

    def service_xml_is_local(self, file=None):
        """
        Test if the cached capabilties xml doc exists
        and if so set the services file to match this
        :param file: file name
        :type file: str
        @return: boolean. True file exists
        @rtype: boolean
        """

        if not file:
            os.chdir(self.pl_settings_dir)
            files = glob.glob("{0}_{1}_*.xml".format(self.domain, self.service.lower()))
            if files:
                self.file = sorted(files)[-1]
                return True
        return False

    def read_local_service_xml(self, file=None):
        """
        Read the cached XML document

        :param file: file name
        :type file: str
        """

        if not file:
            file = self.file
        with open(file, "rb") as file_pointer:
            self.xml = file_pointer.read()


class ServiceData(Localstore):
    """
    Get, Store and Process WxS Data
    """

    def __init__(  # pylint:disable=too-many-arguments
        self, domain, service, service_version, api_key_instance, upd_cache=False
    ):
        """
        Initialise Service Data instance

        :param service: Service Type (WMTS or WFS)
        :type service: str
        :param domain: Service Domain (e.g. data.linz.govt.nz)
        :type domain: str
        :param service_version: {'wfs': '2.0.0', 'wmts': '1.0.0'}
        :type service_version: dict
        :param api_key_instance: API instance
        :type api_key_instance: linz-data-importer.service_data.ApiKey
        """

        self.version = service_version[service]
        self.api_key_int = (
            api_key_instance  # using one instance as the user can change keys on us
        )
        self.upd_cache = upd_cache
        Localstore.__init__(self, domain, service)
        # Data
        self.obj = None  # owslib data obj
        self.info = None  # owslib data obj formatted for table
        self.err = None  # any errors
        self.disabled = False
        self.crs = []

    def is_enabled(self):
        """
        Test if the service is enable.
        Some services (e.g wmts) are disabled for specific domains. These
        return XML docs without headers.

        @return: boolean. True == Service is diabled
        @rtype: boolean
        """

        disbaled_str = ("Service {0} is disabled").format(self.service.upper())
        if self.xml.find(disbaled_str.encode()) == -1:
            return True
        self.disabled = True
        return False

    def get_service_data(self):
        """
        Select method to obtain capabilities doc.
        Either via localstore or internet
        """

        # If cache get new data and overwrite local store
        if self.upd_cache:
            self.get_service_xml()
            return

        # Plugin opened for first time
        # Read data from local store if exists
        if self.service_xml_is_local():
            self.read_local_service_xml()
        else:
            self.get_service_xml()

    def get_service_data_try_again(self):
        """
        If the reading of the capability doc fails - Try again.
        This is for use cases where for some reason the user
        has corrupted the capability doc in the localstore
        """

        # Clear error, Delete local file and get it a fresh
        self.err = None
        self.del_local_sevice_xml()
        self.get_service_data()
        if self.err:
            return
        self.get_service_obj()
        if self.err:
            return

    def process_service_data(self):
        """
        Get, process and format the service data
        """

        self.get_service_data()
        if self.err:
            return

        if not self.is_enabled():
            return

        # service info obj
        self.get_service_obj()
        if self.err == "{0}: XMLSyntaxError".format(self.domain):
            self.get_service_data_try_again()
        if self.err:
            return

        # Format the response data
        self.format_for_ui()

    def get_service_obj(self):
        try:
            if self.service == "wmts":
                self.obj = WebMapTileService(
                    url=None,
                    xml=self.xml,
                    version=self.version,
                )
            elif self.service == "wfs":
                self.obj = WebFeatureService(
                    url=None,
                    xml=self.xml,
                    version=self.version,
                )
        except XMLSyntaxError:
            # most likely the locally stored xml is corrupt
            self.err = "{0}: XMLSyntaxError".format(self.domain)

    def get_service_xml(self):
        """
        Get capability documents from the internet
        """

        try:
            if self.service == "wmts":
                if self.domain == "basemaps.linz.govt.nz":
                    url = (
                        "https://{0}/v1/tiles/aerial/"
                        "WMTSCapabilities.xml?api={1}".format(
                            self.domain, self.api_key_int.get_api_key(self.domain)
                        )
                    )
                else:
                    url = (
                        "https://{0}/services;"
                        "key={1}/{2}/{3}/WMTSCapabilities.xml".format(
                            self.domain,
                            self.api_key_int.get_api_key(self.domain),
                            self.service.lower(),
                            self.version,
                        )
                    )

            elif self.service == "wfs" and self.domain != "basemaps.linz.govt.nz":
                url = (
                    "https://{0}/services;"
                    "key={1}/{2}?service={3}&version={4}"
                    "&request=GetCapabilities".format(
                        self.domain,
                        self.api_key_int.get_api_key(self.domain),
                        self.service.lower(),
                        self.service.upper(),
                        self.version,
                    )
                )
            with urlopen(url) as xml:
                self.xml = xml.read()

            # write to cache
            with open(self.file, "wb") as file_pointer:
                file_pointer.write(self.xml)

        except URLError as error:
            if hasattr(error, "reason"):
                self.err = "Error: ({0}) {1}".format(self.domain, error.reason)

            elif hasattr(error, "code"):
                self.err = "Error: ({0}) {1}".format(self.domain, error.reason)

    def sort_crs(self):
        # wfs returns some no valid crs values
        valid = re.compile(r"^EPSG:\d+")
        self.crs = [s for s in self.crs if valid.match(s)]
        # sort
        self.crs.sort(key=lambda x: int(x.split(":")[1]))

    def format_for_ui(self):
        """
        Format the service data to display in the UI
        """

        service_data = []
        cont = self.obj.contents
        full_id_regex = re.compile(
            r"([aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\.[aA-zZ]+\\:)?(?P<type>[aA-zZ]+)-(?P<id>[0-9]+)"
        )
        for dataset_id, dataset_obj in cont.items():
            self.crs = []
            if self.domain == "basemaps.linz.govt.nz":
                object_id = dataset_obj.id
                type = "layer"
            else:
                full_id = full_id_regex.search(dataset_obj.id)
                type = full_id.group("type")
                object_id = full_id.group("id")
            # Get and standarise espg codes
            if self.service == "wmts":
                self.crs = dataset_obj.tilematrixsets
                self.sort_crs()
            elif self.service == "wfs":
                self.crs = dataset_obj.crsOptions
                self.crs = ["EPSG:{0}".format(item.code) for item in self.crs]
                self.sort_crs()

            service_data.append(
                [
                    self.domain,
                    type,
                    self.service.upper(),
                    object_id,
                    dataset_obj.title,
                    dataset_obj.abstract,
                    self.crs,
                ]
            )

        self.info = service_data
