import os

import geopandas as gpd

from lib.tracking_decorator import TrackingDecorator


@TrackingDecorator.track_time
def convert_to_geojson(data_transformation, source_path, results_path, clean, quiet):
    already_exists, converted, exception = 0, 0, 0

    if data_transformation.input_ports:
        for input_port in data_transformation.input_ports:
            for file in input_port.files:
                source_file_path = os.path.join(
                    source_path, input_port.id, file.source_file_name
                )
                target_file_path = os.path.join(
                    results_path, input_port.id, file.target_file_name
                )

                if not clean and os.path.exists(target_file_path):
                    already_exists += 1
                    not quiet and print(f"✓ Already converted {file.target_file_name}")
                    continue

                _, source_file_extension = os.path.splitext(source_file_path)

                try:
                    if source_file_extension == ".shp":
                        os.makedirs(
                            os.path.join(results_path, input_port.id), exist_ok=True
                        )
                        gpd.read_file(source_file_path).to_file(
                            target_file_path, driver="GeoJSON"
                        )
                        converted += 1
                        not quiet and print(f"✓ Convert {file.target_file_name}")
                except Exception as e:
                    exception += 1
                    print(f"✗️ Exception: {str(e)}")

    print(
        f"convert_to_geojson finished with already_exists: {already_exists}, converted: {converted}, exception: {exception}"
    )
