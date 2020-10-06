# LDS Data Importer [![Build Status](https://api.travis-ci.com/linz/linz-data-importer.svg?token=4YGqrWWw1nJqpi344cuy&branch=master_qgis3)](https://travis-ci.com/linz/linz-data-importer)

The intent of this QGIS Plugin is to allow the easy importing of 
[LINZ Data Service](data.govt.linz.nz) data (as well as other data services - 
see [Other Supported Services](https://github.com/linz/linz-data-importer/#Other-Supported-Services)) 
 into QGIS. 

![](https://github.com/linz/linz-data-importer/blob/master_qgis3/images/import_example.gif)

## Other Supported Services
Other New Zealand agencies that make use of the same technology platform to publish their data can 
can also be imported using this plugin.

This plugin supports the below open data portals:
* [data.linz.govt.nz](data.linz.govt.nz) (Toitū Te Whenua - Land Information New Zealand)
* [data.mfe.govt.nz](data.mfe.govt.nz) (Manatū Mō Te Taiao - Ministry for the Environment)
* [datafinder.stats.govt.nz](datafinder.stats.govt.nz) (Tatauranga Aotearoa - Statistics New Zealand)
* [lris.scinfo.org.nz](lris.scinfo.org.nz) (Manaaki Whenua - Landcare Research)
* [geodata.nzdf.mil.nz](geodata.nzdf.mil.nz) (Te Ope Kātua o Aotearoa - New Zealand Defence Force)
* [basemaps.linz.govt.nz](basemaps.linz.govt.nz) (LINZ Basemaps)

## Selecting a Service / Protocol
The LDS Plugin supports data served over WFS and WMTS protocols.
Please see the resource available on the 
[LINZ website](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/which-web-service-should-i-use) for more on these protocols. 

## API Keys 
Prior to using the plugin, a domain and related API Key must be stored via the "Settings" menu.
When saving your API key this will trigger the plugin to request all of the domain's dataset information. This may take some time.
For more on API keys please see the [LDS user resources](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/creating-an-api-key). 

For instructions about obtaining basemaps API keys please see
https://basemaps.linz.govt.nz/.


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
The data portal's server can be slow to respond with these documents causing the 
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
 are executed via [Travis](https://travis-ci.com/linz/linz-data-importer)
for branches listed in the `.travis.yml` file. These Travis tests are against
an instance of QGIS within a Docker container as made possible by the 
[Boundless Docker container](https://hub.docker.com/r/boundlessgeo/qgis-testing-environment/). 


### Thanks
Thanks to all those at LINZ who have provided input and feedback.  
And thanks to Pete King for the icons.
