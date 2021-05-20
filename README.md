# LDS Data Importer [![Build Status](https://api.travis-ci.com/linz/linz-data-importer.svg?token=4YGqrWWw1nJqpi344cuy&branch=master_qgis3)](https://travis-ci.com/linz/linz-data-importer)

The intent of this QGIS Plugin is to allow the easy discovery and import of
[LINZ Data Service](data.linz.govt.nz) and [LINZ Basemaps](basemaps.linz.govt.nz) data into QGIS.

![](https://github.com/linz/linz-data-importer/blob/master_qgis3/images/import_example.gif)

## Supported Services
As well as the LINZ Data Service, the plugin can be configured to allow the discovery and importing of data
from other New Zealand agencies that make use of the same technology platform to publish their data.

This plugin supports the below open data portals:
* [data.linz.govt.nz](http://data.linz.govt.nz) (Toitū Te Whenua - Land Information New Zealand)
* [data.mfe.govt.nz](http://data.mfe.govt.nz) (Manatū Mō Te Taiao - Ministry for the Environment)
* [datafinder.stats.govt.nz](http://datafinder.stats.govt.nz) (Tatauranga Aotearoa - Statistics New Zealand)
* [lris.scinfo.org.nz](http://lris.scinfo.org.nz) (Manaaki Whenua - Landcare Research)
* [geodata.nzdf.mil.nz](http://geodata.nzdf.mil.nz) (Te Ope Kātua o Aotearoa - New Zealand Defence Force)
* [basemaps.linz.govt.nz](http://basemaps.linz.govt.nz) (LINZ Basemaps)

## Selecting a Service / Protocol
The LINZ Data Service Plugin supports data served over WFS and WMTS protocols.
Please see the resources available on the
[LINZ website](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/which-web-service-should-i-use) for more on these protocols.

## API Keys
Prior to using the plugin, an API Key for each domain that data is to be loaded from must be must be configured via the "Settings" menu.
Configuring each domain and API key will trigger the plugin to request all of the domain's dataset information, allowing a user to view
and import the domain's data in QGIS.

### Obtaining Data Portal API Keys
An API key for each of the supported services can be allocated from each of the service's websites
(see [Supported Services](https://github.com/linz/linz-data-importer/#supported-services)
for a link to each services website were the API Keys can be got).

For detailed instructions on getting an API key, please see the [LINZ Data Services user resources](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/creating-an-api-key).

### Obtaining LINZ Basemap API Keys
To configure LINZ basemaps please visit https://basemaps.linz.govt.nz/ to obtain an API Key.

When at https://basemaps.linz.govt.nz/:
* Open the menu on the right
* Extract the API key from the url in this menu

\* Note; these keys are rotated every 90 days and will need to be update accordingly


![Example of Domains configured via the settings menu](https://github.com/linz/linz-data-importer/blob/master_qgis3/images/settings_example.png)




## Coordinate Reference System (CRS)
The available CRS options for each layer are shown next to the import button (in
terms of EPSG code). If the data source is stored in multiple CRSs the user
can select which CRS the dataset is to be requested in from the server.

\* Note; if the QGIS project's CRS and the imported dataset's CRS do not
match, QGIS will reproject the imported data to the project's CRS.
**Beware:** reprojecting data can degrade spatial accuracies and relationships.

When importing the first dataset via the plugin for a QGIS session, the plugin
will change the QGIS project's CRS to match the imported data. If On The Fly (OTF)
projection is not enabled, the plugin will enable OTF to allow any
further datasets to be reprojected to the project's / QGIS session's CRS.
When these changes occur the user will be informed via the QGIS message bar.

## Requests, Responses, Patience and Caching
When saving a Domain and API key for the first time via the Setting menu, the plugin
will request the capabilities documents for each service / protocol type (WMTS, WFS).
The Data Portal's server can be slow to respond with these documents causing the
plugin to appear inactive. The good news is this is the only interaction with the
plugin where substantial patience may be required. Once the initial documents
are fetched, they will be cached and updated in the background each time
the plugin is started.

## Filtering
The left hand panel allows users to filter by service / protocol types (either, All, WFS, WMTS).
All column headers can be toggled to allow ascending or descending ordering of their data.
Text can be entered in the "Filter Data Sets" search bar to filter the datasets by keyword.

## Source Code and Feedback
Please see the [LINZ-Data-Importer](https://github.com/linz/linz-data-importer/) repository on GitHub.

## Dev Notes

### Tests
[Tests](https://github.com/linz/linz-data-importer/tree/master_qgis3/linz-data-importer/tests)
are executed via [GitHub Actions](https://github.com/linz/linz-data-importer/actions)
for branches listed in the [`.ci.yml`](https://github.com/linz/linz-data-importer/blob/master_qgis3/.github/workflows/ci.yml)
file. These tests are against an instance of QGIS within a Docker container as made possible by the
[elpaso's Docker container](https://hub.docker.com/r/elpaso/qgis-testing-environment).

You can run the tests using the test.bash script.

### Thanks
Thanks to all those at LINZ who have provided input and feedback.
And thanks to Pete King for the icons.
