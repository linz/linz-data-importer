# Change Log

All notable changes to this project will be documented in this file.

# 2.3.1 (2021-08-01)

### Bugs

- Fixed bug causing LINZ Basemaps WMTS not to load
- Use webp format for LINZ Basemaps WMTS
- Fixed CI test timeouts
- Set min supported QGIS version to 3.16

# 2.3.0 (2021-07-29)

### Bugs

- LINZ Basemaps not loading in plugin #159

# 2.2.3 (2021-06-17)

### Bugs

- Fixed preview image request timeout
- Fixed attribute doesn't exist error
- Fixed 'add' and 'cancel' icons not displaying

# 2.2.2 (2021-06-16)

### Bugs

- Correct version in metatata.txt

# 2.2.1 (unreleased)

### Features

- Improved help documentation
- Quality controls added - pylint, black, isort
- Updated license
- Added local docker testing

# 2.2.0 (unreleased)

### Features

- Improved layer searching
- Filter WFS results by bbox of map canvas

# 2.1.0 (2020-10-30)

### Features

- WMS removed (WMS is no-longer supported)
- Configurable for LINZ Basemaps

# 2.0.1 (2019-03-21)

### Features

- When a dataset is served in multiple spatial references system, allow the user to select
  their preference

### Bug Fixes

- Ensure help documents are loaded as utf-8

# 2.0.0 (2019-01-17)

### Features

- Ported to QGIS3 API

### BREAKING CHANGE

- Updated to QGIS3 API. QGIS2 no longer supported

# 1.0.4 (2018-12-18)

### Features

- First Stable Release
