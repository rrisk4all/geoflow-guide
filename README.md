# GeoFlow Guide 0.2.0

GeoFlow Guide is a standalone QGIS plugin for layer-aware, plain-language
workflow guidance. Install one ZIP; everything runs inside QGIS.

## Install and test

1. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP**.
2. Select `geoflow-guide-0.2.0.zip`.
3. Open **Vector → GeoFlow Guide**.
4. Choose a Point, Line or Polygon sample and click **Load Sample**, or select one of your own layers.
5. Choose a recommended task, read its explanation and click **Run Task**.

Generated processing results are temporary and do not overwrite the input.
Choose an item under **Generated results** and use **Remove Selected Result**.

Version 0.2 automatically creates metre/kilometre buffers through a suitable
local metric CRS, while returning the result to the original CRS. It also adds
task categories, built-in help and a compatibility self-check.

## Project links

- Homepage and source: https://github.com/rrisk4all/geoflow-guide
- Issue tracker: https://github.com/rrisk4all/geoflow-guide/issues

This is a testing build for QGIS 3.28–3.99. Please report problems through the
public issue tracker before submission to the official QGIS Plugin Repository.

Author: Hrishikesh Tambe  
Institute: RRI Skill and Knowledge Foundation  
Licence: GPL-2.0-or-later
