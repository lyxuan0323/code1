# Panoramic Building Height Estimation from Street-Level Imagery

This repository contains a workflow for estimating building heights from panoramic street-view imagery, building masks, and building footprint data. The project combines geometric projection, visibility-based footprint filtering, mask-derived boundary extraction, and single-corner height search under both fixed-step and multiscale strategies. The current implementation also includes utilities for semantic mask extraction and exporting visibility-filtered building footprints as shapefiles. 

## Overview

The main purpose of this repository is to estimate building heights from panoramic imagery without relying on dense training data. The workflow starts from building footprints and camera metadata, projects footprint corners into panoramic image space, derives roof and bottom boundaries from building masks, and then searches for the height at which a projected corner first reaches the roof boundary in the same image column. A multiscale coarse-to-fine search strategy is implemented and compared with a fixed-step baseline. 

In parallel, the repository provides a visibility-filtering module for building footprints. This module identifies Z-buffer-style visible building footprints and distance-threshold-constrained usable footprints from an observer position, and exports the filtered results as shapefiles. :contentReference[oaicite:3]{index=3}

A utility script is also included to extract semantic regions from colorized segmentation images using predefined Cityscapes-style RGB values, with support for mask export and overlay visualization. :contentReference[oaicite:4]{index=4}

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
- optionally compares the computational efficiency of the fixed-step and multiscale strategies and writes summary statistics to CSV :contentReference[oaicite:5]{index=5}

### 2. `project_pano.py`

This script provides the geometric utilities used by the height-estimation workflow. It includes:

- geographic to UTM coordinate conversion
- panoramic projection from 3D relative coordinates to image coordinates
- footprint visibility selection from a shapefile
- basic support for building boundary extraction from segmentation imagery
- a visualization function for projected building corners on panoramas :contentReference[oaicite:6]{index=6}

### 3. `extract_cityscapes_regions_colors.py`

This utility extracts semantic masks from color segmentation images using predefined RGB mappings. It can:

- read segmentation images and original rectified panoramas
- extract per-class binary masks using a tolerance-based color match
- generate visualization overlays
- save individual class masks and overlays
- produce an integrated mask output
- report per-image processing time statistics :contentReference[oaicite:7]{index=7}

### 4. `visiblefootprint.py`

This script exports filtered footprint shapefiles instead of figures. It:

- reads a building shapefile
- computes visible and usable building footprints from one or more observer locations
- classifies buildings into `non_visible`, `zvis`, or `usable`
- exports:
  - visible building footprints
  - usable building footprints within the distance threshold
  - one combined shapefile with classification attributes :contentReference[oaicite:8]{index=8}

## Method Summary

### Height estimation

For each building corner, the bottom point is first projected onto the panoramic image to define a fixed image column. The bottom boundary and roof boundary are then read from that same column in the building mask. Candidate heights are searched vertically, and the estimated corner height is taken as the first height whose projected row coordinate reaches or crosses the roof boundary in the same column. The repository implements both a fixed-step search and a multiscale coarse-to-fine search for this purpose. :contentReference[oaicite:9]{index=9}

### Visibility filtering

Before height estimation, building footprints can be filtered by line-of-sight visibility and distance threshold. The current implementation uses observer-to-corner sight lines and polygon-crossing tests to identify visible and usable footprints. Exported shapefiles can then be used as filtered geometric input for later processing. 

### Mask extraction

Semantic masks are extracted by matching RGB values in a colorized segmentation image. The script includes a predefined dictionary of Cityscapes-like classes and generates per-class masks and visualization overlays. The `building` class is highlighted separately in the visualization stage. :contentReference[oaicite:11]{index=11}

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
