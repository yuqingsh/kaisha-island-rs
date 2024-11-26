import yaml
import argparse
import os
import datetime
from dateutil.relativedelta import relativedelta
from sentinelhub.geo_utils import bbox_to_dimensions
from sentinelhub import SHConfig, SentinelHubRequest, BBox, CRS, DataCollection, MimeType, MosaickingOrder
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt

# GLOBAL VARIABLES
CONFIG_PATH = "config.yaml"
RAW_DATA_FOLDER = "raw_data/"
PROCESSED_DATA_FOLDER_256 = "processed_data_256/"
BRIGHTNESS_FACTOR = 2.0
GAMMA = 0.8
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

def download_images_to_disk(bbox, size, cfg, evalscript, time_interval=("2023-1-01", "2023-12-31"), output_dir=RAW_DATA_FOLDER):
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

def crop_and_process_images(input_dir, output_dir, tile_size=(256,256), brightness_factor=BRIGHTNESS_FACTOR, gamma=GAMMA):
    """
    Crop and normalize the images to the given size

    :param input_dir: directory containing the images
    :param output_dir: directory to save the processed images
    :param size: size of the cropped images
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
            img_path = os.path.join(input_dir, filename)
            try:
                with Image.open(img_path).convert('RGB') as img:
                    width, height = img.size
                    tiles_x = width // tile_size[0]
                    tiles_y = height // tile_size[1]

                    for i in range(tiles_y):
                        for j in range(tiles_x):
                            left = j * tile_size[0]
                            upper = i * tile_size[1]
                            right = left + tile_size[0]
                            lower = upper + tile_size[1]

                            # Crop the sub-image
                            tile = img.crop((left, upper, right, lower))

                            # Enhance brightness
                            enhancer = ImageEnhance.Brightness(tile)
                            tile_bright = enhancer.enhance(brightness_factor)

                            if gamma != 1.0:
                                inv_gamma = 1.0 / gamma
                                # Create a lookup table for gamma correction
                                table = [((c / 255.0) ** inv_gamma) * 255 for c in range(256)]
                                # Since the image is RGB, replicate the table for each channel
                                gamma_table = table * 3
                                tile_bright = tile_bright.point(gamma_table)

                            # Save the processed tile
                            tile_filename = f"{os.path.splitext(filename)[0]}_tile_{i}_{j}.png"
                            tile_save_path = os.path.join(output_dir, tile_filename)
                            tile_bright.save(tile_save_path)

            except Exception as e:
                print(f"Error processing {img_path}: {e}")

    print(f"Processing completed. Processed images are saved in '{output_dir}'.")


def main(args=None):
    parser = argparse.ArgumentParser(description="Download and preprocess Sentinel-2 images")

    parser.add_argument(
        '--config', '-c',
        type=str,
        default=CONFIG_PATH,
        help="Path to the configuration file. Default is config.yaml."
    )

    parser.add_argument(
        '--download', '-d',
        nargs='?',
        const=RAW_DATA_FOLDER,
        default=None,
        metavar='DOWNLOAD_PATH',
        help="Download images to the specified path. Default is raw_data/."
    )

    parser.add_argument(
        '--process', '-p',
        nargs='*',
        metavar=('RAW_DATA_FOLDER', 'PROCESSED_DATA_FOLDER_256'),
        help="Process images in the specified directory and save the processed images to the output directory."
    )

    args = parser.parse_args()

    cfg = load_cfg_file(args.config)

    # Check if neither download nor process is specified
    if args.download is None and args.process is None:
        # Perform both download and process with default paths
        download_output_dir = RAW_DATA_FOLDER
        download_images_to_disk(
            KAISHA_ISLAND_BOUNDING_BOX,
            KAISHA_SIZE,
            cfg,
            EVALSCRIPT_TRUE_COLOR,
            output_dir=download_output_dir
        )
        crop_and_process_images(RAW_DATA_FOLDER, PROCESSED_DATA_FOLDER_256)
    else:
        if args.download is not None:
            download_output_dir = args.download if isinstance(args.download, str) else RAW_DATA_FOLDER
            download_images_to_disk(
                KAISHA_ISLAND_BOUNDING_BOX,
                KAISHA_SIZE,
                cfg,
                EVALSCRIPT_TRUE_COLOR,
                output_dir=download_output_dir
            )

        if args.process is not None:
            if len(args.process) == 2:
                raw_data_path, target_path = args.process
            elif len(args.process) == 1:
                raw_data_path = args.process[0]
                target_path = PROCESSED_DATA_FOLDER_256
            else:  # len(args.process) == 0
                raw_data_path = RAW_DATA_FOLDER
                target_path = PROCESSED_DATA_FOLDER_256
            crop_and_process_images(raw_data_path, target_path)


if __name__=="__main__":
    main()