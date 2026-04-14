# -*- coding: utf-8 -*-
"""
Export filtered building footprints instead of a figure.

This script reads the input building shapefile, computes Z-buffer visible
building footprints and usable building footprints within the distance threshold,
and exports the filtered results as shapefiles.
"""

import os
import geopandas as gpd

from shapely.geometry import Point, LineString

# =========================
# USER PARAMS
# =========================
DIST_THRESH_M = 25.0
SHOW_INVISIBLE_POINTS = False

# =========================
# INPUT / OUTPUT PATHS
# =========================
BUILDING_SHP = r"F:\gsv3d\code1\osm\rectdata.shp"
OUT_ZVIS_SHP = r"F:\gsv3d\code1\osm\parisosmarea\paris_area2bldt_zvis_25m.shp"
OUT_USABLE_SHP = r"F:\gsv3d\code1\osm\parisosmarea\paris_area2bldt_usable_25m.shp"
OUT_COMBINED_SHP = r"F:\gsv3d\code1\osm\parisosmarea\paris_area2bldt_visibility_class_25m.shp"

# =========================
# observer: (lon, lat, heading)
# =========================
OBSERVERS_WGS84 = [
    (2.355323455596569, 48.85911140268727, 37.66719818115234)
]


# =========================
# HELPERS
# =========================
def iter_exterior_coords(geom):
    if geom.geom_type == "Polygon":
        coords = list(geom.exterior.coords)
        for xy in coords[:-1]:
            yield xy
    elif geom.geom_type == "MultiPolygon":
        for g in geom.geoms:
            coords = list(g.exterior.coords)
            for xy in coords[:-1]:
                yield xy



def compute_visibility_for_observer(observation_point, buildings_poly, sidx,
                                    dist_thresh_m, show_invisible=False):
    zvis_points = []
    usable_points = []
    invisible_points = []
    zvis_building_idx = set()
    usable_building_idx = set()

    for idx, building in buildings_poly.iterrows():
        geom = building.geometry
        if geom is None or geom.is_empty:
            continue

        has_zvis = False
        has_usable = False

        for xy in iter_exterior_coords(geom):
            p = Point(xy)
            sight_line = LineString([observation_point, p])
            cand_pos = list(sidx.intersection(sight_line.bounds))
            blocked = False

            for j in cand_pos:
                other = buildings_poly.iloc[j]
                other_idx = other.name
                if other_idx == idx:
                    continue

                other_geom = other.geometry
                if other_geom is None or other_geom.is_empty:
                    continue

                if sight_line.crosses(other_geom):
                    blocked = True
                    break

            if blocked:
                if show_invisible:
                    invisible_points.append(p)
                continue

            zvis_points.append(p)
            has_zvis = True

            if observation_point.distance(p) <= dist_thresh_m:
                usable_points.append(p)
                has_usable = True

        if has_zvis:
            zvis_building_idx.add(idx)
        if has_usable:
            usable_building_idx.add(idx)

    return zvis_points, usable_points, invisible_points, zvis_building_idx, usable_building_idx



def main():
    if not os.path.exists(BUILDING_SHP):
        raise FileNotFoundError(f"Building shapefile not found: {BUILDING_SHP}")

    buildings = gpd.read_file(BUILDING_SHP)
    if buildings.crs is None:
        raise ValueError("The shapefile has no CRS. Please define the correct coordinate reference system first.")

    original_crs = buildings.crs

    # Project to a metric CRS for visibility and distance computation
    buildings_3857 = buildings.to_crs(epsg=3857)

    # Keep polygon geometries only
    buildings_poly = buildings_3857[
        buildings_3857.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    if len(buildings_poly) == 0:
        raise ValueError("No Polygon or MultiPolygon geometries were found in the input shapefile.")

    sidx = buildings_poly.sindex

    # Project observers to EPSG:3857
    obs_wgs84 = gpd.GeoSeries(
        [Point(lon, lat) for lon, lat, _ in OBSERVERS_WGS84],
        crs="EPSG:4326"
    )
    observation_points = list(obs_wgs84.to_crs(epsg=3857).geometry)

    all_zvis_idx = set()
    all_usable_idx = set()

    for obs in observation_points:
        _, _, _, zvis_idx, usable_idx = compute_visibility_for_observer(
            obs, buildings_poly, sidx, DIST_THRESH_M, SHOW_INVISIBLE_POINTS
        )
        all_zvis_idx |= zvis_idx
        all_usable_idx |= usable_idx

    if all_zvis_idx:
        zvis_buildings = buildings_poly.loc[list(all_zvis_idx)].copy()
    else:
        zvis_buildings = buildings_poly.iloc[0:0].copy()

    if all_usable_idx:
        usable_buildings = buildings_poly.loc[list(all_usable_idx)].copy()
    else:
        usable_buildings = buildings_poly.iloc[0:0].copy()

    combined = buildings_poly.copy()
    combined["zvis"] = combined.index.isin(all_zvis_idx).astype(int)
    combined["usable"] = combined.index.isin(all_usable_idx).astype(int)
    combined["vis_class"] = "non_visible"
    combined.loc[combined["zvis"] == 1, "vis_class"] = "zvis"
    combined.loc[combined["usable"] == 1, "vis_class"] = "usable"

    # Export in the original CRS
    zvis_buildings = zvis_buildings.to_crs(original_crs)
    usable_buildings = usable_buildings.to_crs(original_crs)
    combined = combined.to_crs(original_crs)

    os.makedirs(os.path.dirname(OUT_ZVIS_SHP), exist_ok=True)

    zvis_buildings.to_file(OUT_ZVIS_SHP, encoding='utf-8')
    usable_buildings.to_file(OUT_USABLE_SHP, encoding='utf-8')
    combined.to_file(OUT_COMBINED_SHP, encoding='utf-8')

    print("Filtered Z-buffer visible building shapefile saved to:", OUT_ZVIS_SHP)
    print("Filtered usable building shapefile saved to:", OUT_USABLE_SHP)
    print("Combined visibility-class shapefile saved to:", OUT_COMBINED_SHP)
    print("Counts -> zvis:", len(zvis_buildings), ", usable:", len(usable_buildings), ", total:", len(combined))


if __name__ == "__main__":
    main()
