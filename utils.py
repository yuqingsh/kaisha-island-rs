import yaml
import os
from sentinelhub import SHConfig, SentinelHubRequest, BBox, CRS, DataCollection, MimeType
from datetime import datetime, timedelta
from rasterio.transform import from_bounds

OUTPUT_FOLDER_PATH = "data/"
KAISHA_ISLAND_BOUNDING_BOX = BBox(bbox=[121.8, 32.0, 121.9, 32.1], crs=CRS.WGS84)
DEFAULT_START_DATE = datetime(2023, 1, 1)
DEFAULT_END_DATE = datetime(2023, 12, 31)
DEFAULT_DELTA = timedelta(days=30)  # 每30天下载一次影像

def load_config():
    with open("config.yaml", "r") as file:
        config_data = yaml.safe_load(file)

    config = SHConfig()
    config.sh_client_id = config_data['sentinelhub']['client_id']
    config.sh_client_secret = config_data['sentinelhub']['client_secret']

    if not config.sh_client_id or not config.sh_client_secret:
        raise ValueError("Missing Sentinel Hub credentials in config.yaml.")
    return config

def download_single_image(cfg, bbox, index, start_date, end_date, output_folder):
    time_interval=(start_date, end_date)
    request = SentinelHubRequest(
        evalscript="""
        function setup() {
            return {
                input: ["B04", "B08"],
                output: { bands: 1 }
            };
        }
        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            return [ndvi];
        }
        """,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=(512, 512),
        config=cfg
    )
    ndvi_data = request.get_data()
    if ndvi_data and len(ndvi_data) > 0:
        output_path = os.path.join(output_folder, f"ndvi_kaisha_{index}.tiff")
        with open(output_path, "wb") as file:
            file.write(ndvi_data[0])
        print(f"Image saved: {start_date} to {end_date}")
    else:
        print(f"No data fetched for {time_interval} ")

def download_many_images(cfg, bbox, start_date, end_date, time_interval):
    output_folder = OUTPUT_FOLDER_PATH + start_date.strftime("%Y-%m-%d") + "to" + end_date.strftime("%Y-%m-%d")
    os.makedirs(output_folder, exist_ok=True)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + time_interval
        dates.append((current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")))
        current_date = next_date

    for i, time_interval in enumerate(dates):
        download_single_image(cfg, bbox, i, time_interval[0], time_interval[1], output_folder)

if __name__ == "__main__":
    config = load_config()
    download_many_images(config, KAISHA_ISLAND_BOUNDING_BOX, DEFAULT_START_DATE,
                         DEFAULT_END_DATE, DEFAULT_DELTA)