# Statistical Building Height Estimation from Panoramic Imagery Without Camera Parameters

This repository contains a workflow for estimating building heights from panoramic street-view imagery, building masks, and building footprint data. The project combines geometric projection, visibility-based footprint filtering, mask-derived boundary extraction, and single-corner height search under both fixed-step and multiscale strategies. The current implementation also includes utilities for semantic mask extraction and exporting visibility-filtered building footprints as shapefiles.

## Setup 

Simply clone this repository or download the ZIP file to your local machine, then install the required Python packages using `requirements.txt`:

```bash
git clone https://github.com/lyxuan0323/code1.git
cd code1
pip install -r requirements.txt
```
## Overview

The main purpose of this repository is to estimate building heights from panoramic imagery without relying on dense training data. The workflow starts from building footprints and camera metadata, projects footprint corners into panoramic image space, derives roof and bottom boundaries from building masks, and then searches for the height at which a projected corner first reaches the roof boundary in the same image column. A multiscale coarse-to-fine search strategy is implemented and compared with a fixed-step baseline. 

In parallel, the repository provides a visibility-filtering module for building footprints. This module identifies Z-buffer-style visible building footprints and distance-threshold-constrained usable footprints from an observer position, and exports the filtered results as shapefiles.

A utility script is also included to extract semantic regions from colorized segmentation images using predefined Cityscapes-style RGB values, with support for mask export and overlay visualization.

## Main Components

### 1. `Main6_multiscale.py`

This is the main height-estimation script. It:

- reads rectified panoramas, building masks, and metadata JSON files
- extracts top and bottom building boundaries from binary building masks
- selects visible footprint corners from a footprint shapefile
- projects candidate 3D corner points into panoramic image space
- estimates corner heights using either:
  - `fixed_step`: 0.1 m incremental search
  - `multiscale`: 10 → 5 → 2.5 → 1 → 0.5 → 0.1 m coarse-to-fine refinement
- saves per-image height estimation results to Excel
- optionally compares the computational efficiency of the fixed-step and multiscale strategies and writes summary statistics to CSV 

### 2. `project_pano.py`

This script provides the geometric utilities used by the height-estimation workflow. It includes:

- geographic to UTM coordinate conversion
- panoramic projection from 3D relative coordinates to image coordinates
- footprint visibility selection from a shapefile
- basic support for building boundary extraction from segmentation imagery
- a visualization function for projected building corners on panoramas 

### 3. `extract_cityscapes_regions_colors.py`

This utility extracts semantic masks from color segmentation images using predefined RGB mappings. It can:

- read segmentation images and original rectified panoramas
- extract per-class binary masks using a tolerance-based color match
- generate visualization overlays
- save individual class masks and overlays
- produce an integrated mask output
- report per-image processing time statistics

### 4. `visiblefootprint.py`

This script exports filtered footprint shapefiles instead of figures. It:

- reads a building shapefile
- computes visible and usable building footprints from one or more observer locations
- classifies buildings into `non_visible`, `zvis`, or `usable`
- exports:
  - visible building footprints
  - usable building footprints within the distance threshold
  - one combined shapefile with classification attributes

## How to use  

In this project, building height estimation relies on rectified panoramic images, semantic segmentation results, camera metadata, and building footprint data. Since panorama rectification and semantic segmentation can be produced by different external methods or networks, their codes are not integrated into the main height estimation pipeline. Instead, the raw street-view panoramas are first processed separately, and the resulting files are prepared for subsequent height estimation, for example in `./gsi/area/rectdata`, `./gsi/area/svgdata`, and `./gsi/area/360json`.

### Preprocessing

**Panorama rectification**: use the method provided in the LSAA dataset repository.  

Repository: `https://github.com/ZPdesu/lsaa-dataset`

**Semantic segmentation**: use the YOSO repository to generate segmentation maps or building masks for the rectified panoramas.   

Repository: `https://github.com/hujiecpp/yoso`

The installation and usage of these external repositories can be referred to their official documentation. More details about the preprocessing settings used in this study can be found in our paper. Other rectification or segmentation methods may also be used, but the generated files should follow the directory structure and naming rules expected by this repository.

### Required prepared files  

Before running the height estimation code, the following files should be prepared:
- rectified panoramic images in `./gsi/area/rectdata`
- building masks or segmentation-derived building regions in `./gsi/area/svgdata`
- camera metadata JSON files in `./gsi/area/360json`
- building footprint shapefile, such as `./osm/rectdata.shp`

### Height estimation 

When the above files are ready, `Main6_multiscale.py` can be used to estimate building heights.

The script projects building footprint corners into the panoramic image, extracts top and bottom building boundaries from the building mask, and estimates corner heights using fixed-step or multiscale search. The results are exported as Excel files, and optional strategy evaluation results are saved as CSV files.

### Optional footprint filtering  

If visibility-based footprint filtering is needed before height estimation, `visiblefootprint.py` can be used to export visibility-filtered and distance-threshold-filtered building footprint shapefiles.
This step is optional, but it can help remove geometrically unsuitable buildings and improve the reliability of subsequent height estimation.

### Mask extraction

Semantic masks are extracted by matching RGB values in a colorized segmentation image. The script includes a predefined dictionary of Cityscapes-like classes and generates per-class masks and visualization overlays. The `building` class is highlighted separately in the visualization stage. 

## Acknowledgements

We appreciate the open-source contributions of the following projects and repositories, which supported the preprocessing and experimental workflow of this study:

[1] [LSAA dataset](https://github.com/ZPdesu/lsaa-dataset)  
Panorama rectification for street-view imagery  
[2] [YOSO](https://github.com/hujiecpp/yoso)  
Semantic segmentation for panoramic street-view images

## Suggested Repository Structure

You can organize the repository like this:

```text
.
├── Main6_multiscale.py
├── project_pano.py
├── extract_cityscapes_regions_colors.py
├── visiblefootprint.py
├── README.md
├── requirements.txt
├── gsi/
│   └── area/
│       ├── rawdata/
│       ├── rectdata/
│       ├── svgdata/
│       └── 360json/
├── osm/
│   └── rectdata.shp
└── image/
