import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

import json
import numbers
import os
import pyproj
from tqdm import tqdm

from lib.tracking_decorator import TrackingDecorator

target_projection_number = "4326"


@TrackingDecorator.track_time
def convert_projection(
    data_transformation, source_path, results_path, clean=False, quiet=False
):
    already_exists, converted, empty, exception = 0, 0, 0, 0

    if data_transformation.input_ports:
        for input_port in data_transformation.input_ports:
            for file in input_port.files:
                source_file_path = os.path.join(
                    source_path, input_port.id, file.target_file_name
                )
                target_file_path = os.path.join(
                    results_path, input_port.id, file.target_file_name
                )

                with open(source_file_path, "r", encoding="utf-8") as geojson_file:
                    geojson = json.load(geojson_file, strict=False)
                    projection = str(geojson["crs"]["properties"]["name"])
                    projection_number = projection.split(":")[-1]

                    if not clean and (
                        projection_number == target_projection_number
                        or projection_number == "CRS84"
                    ):
                        already_exists += 1
                        if not quiet:
                            print(f"✓ Already exists {file.target_file_name}")
                        continue

                    geojson_polar = convert_to_polar(
                        geojson=geojson,
                        target_projection_number=target_projection_number,
                        source_projection=pyproj.Proj(init=f"epsg:{projection_number}"),
                        target_projection=pyproj.Proj(
                            init=f"epsg:{target_projection_number}"
                        ),
                    )

                    with open(
                        target_file_path, "w", encoding="utf-8"
                    ) as geojson_polar_file:
                        json.dump(geojson_polar, geojson_polar_file, ensure_ascii=False)

                    converted += 1
                    if not quiet:
                        print(f"✓ Convert {file.target_file_name}")

    print(
        f"convert_projection finished with already_exists: {already_exists}, converted: {converted}, empty: {empty}, exception: {exception}"
    )


def convert_to_polar(
    geojson, target_projection_number, source_projection, target_projection
):
    projected_features = []

    for feature in tqdm(
        iterable=geojson["features"], desc="Convert features", unit="feature"
    ):
        projected_features.append(
            project_feature(feature, source_projection, target_projection)
        )

    geojson["features"] = projected_features
    geojson["crs"]["properties"]["name"] = (
        f"urn:ogc:def:crs:EPSG::{target_projection_number}"
    )

    return geojson


def project_feature(feature, source_projection, target_projection):
    if "geometry" not in feature or "coordinates" not in feature["geometry"]:
        return None

    converted_coordinates = project_coords(
        feature["geometry"]["coordinates"], source_projection, target_projection
    )
    feature["geometry"]["coordinates"] = converted_coordinates
    return feature


def project_coords(coords, source_projection, target_projection):
    if len(coords) < 1:
        return []

    if isinstance(coords[0], numbers.Number):
        lon, lat = coords
        converted_lon, converted_lat = pyproj.transform(
            source_projection, target_projection, lon, lat
        )
        return [converted_lon, converted_lat]

    converted_coordinates = []
    for coord in coords:
        converted_coordinates.append(
            project_coords(coord, source_projection, target_projection)
        )
    return converted_coordinates