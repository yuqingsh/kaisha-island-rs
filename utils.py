import yaml
import os
from sentinelhub.geo_utils import bbox_to_dimensions
from sentinelhub import SHConfig, SentinelHubRequest, BBox, CRS, DataCollection, MimeType, MosaickingOrder
import matplotlib.pyplot as plt

KAISHA_ISLAND_BOUNDING_BOX = BBox(bbox=[120.556068, 32.003272, 120.692711, 32.078502], crs=CRS.WGS84)


resolution =  10
kaisha_bbox = BBox(bbox=KAISHA_ISLAND_BOUNDING_BOX, crs=CRS.WGS84)
kaisha_size = bbox_to_dimensions(kaisha_bbox, resolution=resolution)

with open("config.yaml", "r") as file:
        config_data = yaml.safe_load(file)

config = SHConfig()
config.sh_client_id = config_data['sentinelhub']['client_id']
config.sh_client_secret = config_data['sentinelhub']['client_secret']

print(f"Image shape at {resolution} m resolution: {kaisha_size} pixels")

evalscript_true_color = """
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

request_true_color = SentinelHubRequest(
    evalscript=evalscript_true_color,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L1C,
            time_interval=("2024-10-01", "2024-10-30"),
            mosaicking_order=MosaickingOrder.LEAST_CC,
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=KAISHA_ISLAND_BOUNDING_BOX,
    size=kaisha_size,
    config=config,
)

true_color_imgs = request_true_color.get_data()
print(f"Returned data is of type = {type(true_color_imgs)} and length {len(true_color_imgs)}.")
print(f"Single element in the list is of type {type(true_color_imgs[-1])} and has shape {true_color_imgs[-1].shape}")

image = true_color_imgs[0]
print(f"Image type: {image.dtype}")

# Save the image to disk
output_path = "rgb_image.png"
plt.imsave(output_path, image)
print(f"Image saved to {output_path}")

# Visualize the image
plt.imshow(image)
plt.axis('off')  # Hide axis
plt.show()