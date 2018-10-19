# LDS Data Importer [![Build Status](https://travis-ci.org/SPlanzer/QGIS-LDS-Plugin.svg?branch=master)](https://travis-ci.org/SPlanzer/QGIS-LDS-Plugin)

The intent of this QGIS Plugin is to allow the easy importing of 
[LINZ Data Service](data.govt.linz.nz) data (as well as other data services - 
see [Changing Scope](https://github.com/linz/linz-data-importer/#changing-Scope)) 
 into QIGS. 

![](https://github.com/linz/linz-data-importer/blob/master/images/example.gif)

## Supported Versions
Currently this plugin only supports >QGIS2.8 and <QGIS2.18

This has limited functionality and there are plans for a QGIS3 release 
with greater scope shortly. See the [Issues](https://github.com/linz/linz-data-importer/issues) for more




## Changing Scope
The initial scope of this plugin was to couple the LDS and QGIS. However 
as other New Zealand agencies also make use of the same technology the settings 
interface also allows these other agencies open data web portals to be configured.
 
At the time of release this plugin supports the coupling of the below open data portals with QGIS:
* [data.linz.govt.nz](data.linz.govt.nz) (Toitū Te Whenua - Land Information New Zealand)
* [data.mfe.govt.nz](data.mfe.govt.nz) (Manatū Mō Te Taiao - Ministry for the Environment)
* [datafinder.stats.govt.nz](datafinder.stats.govt.nz) (Tatauranga Aotearoa - Statistics New Zealand)
* [lris.scinfo.org.nz](lris.scinfo.org.nz) (Manaaki Whenua - Landcare Research)
* [geodata.nzdf.mil.nz](geodata.nzdf.mil.nz) (Te Ope Kātua o Aotearoa - New Zealand Defence Force


## Selecting a Service 
The LDS Plugin supports data served over WFS, WMS and WMTS protocols. 
Please see the resource available on the 
[LINZ website](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/which-web-service-should-i-use) for more on these protocols. 

## API Keys 
Prior to using the plugin a domain and related API Key must be stored via the "Settings" menu.
When saving your API key this will trigger the plugin to request all of the services dataset information. This may take sometime.
For more on API keys please see the [LDS user resources](http://www.linz.govt.nz/data/linz-data-service/guides-and-documentation/creating-an-api-key). 

## Coordinate Reference System (CRS)
The available CRS options for each layer are shown next to the import button (This is in 
terms of its ESPG code). If the datasource is stored in multiple CRSs the user
can select which CRS to be requested from the server. 

\* Note if the QGIS projects CRS and the imported datasets CRS do not
match, QGIS will reporject the imported data to the projects CRS. **Beware:** 
reprojecting data can degrade spatial accuracies and relationships.

When importing the first dataset via the plugin for the QGIS session the plugin 
will change the QGIS projects CRS to match the imported data. If On The Fly (OTF)
projection is not enable The plugin will also turn this on to allow any 
further datasets to be reprojected. Both these project settings changes will 
be notified to the user when they occur. 

## Requests, Responses, Patience and Caching
When saving a Domain and API key for the first time via the Setting menu the plugin will request the capabilities documents for each service type (WMS, WMTS, WFS). When these documents are large this can cause the plugin to appear inactive. The good news is this is the only interaction with the plug where substantial patience may be required. Once the initial documents are fetched, they will be cached and will be updated in the background each time the plugin is started.
## Filtering
The left hand panel allows users to filter by service types (either, All, WFS, WMS, WMTS).
All column headers can be toggled to allow ascending or descending ordering of their data.
Text can be entered in the "Filter Data Sets" search bar to filter the datasets by keyword. 
## Source Code, Further Documentation and Feedback
Please see [QGIS-LDS-Plugin](https://github.com/linz/linz-data-importer/) at GitHub

## Dev Notes

### Tests 
[Tests](https://github.com/linz/linz-data-importer/tree/master/linz-data-importer/tests)
 are executed via [Travis](https://travis-ci.com/linz/linz-data-importer)
for branches listed in the `.travis.yml` file. These Travis tests are against
an instance of QGIS within a Docker container as made possible by the 
[Boundless Docker container](https://hub.docker.com/r/boundlessgeo/qgis-testing-environment/). 

If running these test locally they can be speed up by placing one of each of the 
GetCapabilities documents from the [LDS](https://data.linz.govt.nz/) for each 
services (WMS, WMTS, WFS)  in the `/tests/data/` folder. This will
save the tests having to go and fetch these for each time. 

### Thanks
Thanks to all those at LINZ who have provided input and feedback. 
And thanks to Pete King for the icons. 