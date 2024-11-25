import yaml
import os
import datetime
from dateutil.relativedelta import relativedelta
from sentinelhub.geo_utils import bbox_to_dimensions
from sentinelhub import SHConfig, SentinelHubRequest, BBox, CRS, DataCollection, MimeType, MosaickingOrder
import matplotlib.pyplot as plt

# GLOBAL VARIABLES
CONFIG_PATH = "config.yaml"
RESOLUTION = 10
KAISHA_ISLAND_BOUNDING_BOX = BBox(bbox=[120.556068, 32.003272, 120.692711, 32.078502], crs=CRS.WGS84)
KAISHA_SIZE = bbox_to_dimensions(KAISHA_ISLAND_BOUNDING_BOX, resolution=RESOLUTION)
EVALSCRIPT_TRUE_COLOR = """
    //VERSION=3

    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04"]
            }],
            output: {
                bands: 3
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B03, sample.B02];
    }
"""

def load_cfg_file(cfg_path):
    """
    Load the configuration file. The config file contains the Sentinel Hub client ID and secret.
    :param cfg_path: path to the configuration file
    :return: configuration object
    """
    with open(cfg_path, "r") as file:
        config_data = yaml.safe_load(file)

    config = SHConfig()
    config.sh_client_id = config_data['sentinelhub']['client_id']
    config.sh_client_secret = config_data['sentinelhub']['client_secret']
    return config

def save_image_to_disk(image, output_path):
    """
    Save the image to disk
    :param image: image to save
    :param output_path: path to save the image
    """
    plt.imsave(output_path, image)
    print(f"Image saved to {output_path}")

def download_single_image(bbox, size, cfg, evalscript, time_interval=("2024-10-01", "2024-10-30")):
    """
    Download a single image from Sentinel Hub
    :param bbox: bounding box of the AOI
    :param resolution: resolution of the image in meters
    :param evalscript: evalscript to use for the request
    :param time_interval: time interval for the request
    :return: image
    """

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L1C,
                time_interval=time_interval,
                mosaicking_order=MosaickingOrder.LEAST_CC,
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=size,
        config=cfg,
    )

    image = request.get_data()[0]
    return image

def download_images_to_disk(bbox, size, cfg, evalscript, time_interval=("2020-1-01", "2023-12-31"), output_dir="data/"):
    """
    Download all images from Sentinel Hub in the given interval and save them to disk
    For each month, a single image mosaicked by least CC is downloaded
    :param bbox: bounding box of the AOI
    :param resolution: resolution of the image in meters
    :param evalscript: evalscript to use for the request
    :param time_interval: time interval for the request
    :param output_dir: directory to save the images
    """

    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_date = datetime.datetime.strptime(time_interval[0], "%Y-%m-%d")
    end_date = datetime.datetime.strptime(time_interval[1], "%Y-%m-%d")
    current_date = start_date

    while current_date <= end_date:
        month_end = current_date + relativedelta(months=1) - datetime.timedelta(days=1)
        if month_end > end_date:
            month_end = end_date
        current_month = (current_date.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d"))
        save_image_to_disk(download_single_image(bbox, size, cfg, evalscript, time_interval=current_month), f"{output_dir}/{current_month[0]}.png")
        current_date += relativedelta(months=1)

    print("All images downloaded and saved to disk")

def main(args=None):
    cfg = load_cfg_file(CONFIG_PATH)
    download_images_to_disk(KAISHA_ISLAND_BOUNDING_BOX, KAISHA_SIZE, cfg, EVALSCRIPT_TRUE_COLOR)

if __name__=="__main__":
    main()