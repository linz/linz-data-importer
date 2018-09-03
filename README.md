# QGIS-LDS-Plugin
[![Build Status](https://travis-ci.org/SPlanzer/QGIS-LDS-Plugin.svg?branch=master)](https://travis-ci.org/SPlanzer/QGIS-LDS-Plugin)
This is the minimum viable product! Please see the issues for future enhancements
# 

This QGIS Plugins intent is to allow the easy importing of 
[LINZ Data Service](data.govt.linz.nz) into QIGS. 

Once a user adds their LDS API key to the plugins settings (see instructions
[below](https://github.com/linz/QGIS-LDS-Plugin#API-Key) )





![](https://github.com/linz/QGIS-LDS-Plugin/blob/master/images/import_wmts.gif)

## Supported Versions
Currently this plugin only supports >QGIS2.8 and <QGIS2.18

There are plans to support QGIS3.



## Selecting a Service
The QGIS LDS Plugin supports LDS data served over WFS, WMS and WMTS protocols.  
Please see the online resource  available on the LINZ website for more on these protocols.  
## API Key  
Prior to using the plugin your LDS API Key must be stored via the "Settings menu" 
When saving your API key this will trigger the plugin to request all LDS dataset information from the LDS server. This may take sometime - please see the below "Requests, Responses and Patience" 
For more on LDS API keys please see the LDS resources. 
## Coordinate Reference System 
As an initial release, when selecting and importing LDS datasets via the QGIS LDS Plugin. the plugin will force the QGIS projects CRS to WGS 84 Web Mercator (EPSG:3857). The user is then notified by QGIS's message bar when the CRS change is made. 
Currently WGS 84 Web Mercator (EPSG:3857) is used by default as all LDS WMTS services are served in this projection and it is not always a good idea to reproject WMTS. This is the initial release of the plugin and there are plans to improve the handling of CRS with subsequent releases. 
## Requests, Responses and Patience 
When opening the plugin for the first time, the QGIS interface will be temporarily inactive while awaiting the LDS server's response (again this is an initial release and there are plans to improve this also). However, after the initial request LDS dataset information is stored in memory and all subsequent requests for the current QGIS session will see the dataset information populated immediately.  
If your internet connection is slow or at times the LDS server is experiencing high load the plugin may fail to populate the table with the available dataset information. In this case the user will need to close the plugin interface and re-open it. 
For those experiencing on going slowness when the plugin loads, the settings tab has the ability to disable services. If services that are not required are disabled the plugin will load faster. For the settings to take affect the plugin must be reloaded (there is however no need for the setting to take affect until the next session as when viewing the "settings" tab the data should already have been loaded.   
## Filtering 
The left hand panel allows users to filter by service types (either, All, WFS, WMS, WMTS). 
All column headers can be toggled to allow ascending or descending ordering of their data. 
Text can be entered in the "Filter Data Sets" search bar to filter the datasets by keyword.
## Source Code, Further Documentation and Feedback 
Issues and pull requests welcome