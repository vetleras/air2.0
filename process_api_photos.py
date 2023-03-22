import sys
import os.path
from pyproj import Proj
from geopy.geocoders import Nominatim
from datetime import datetime
from datetime import timedelta

import matplotlib.image

from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
    SHConfig
)


def generate_bbox(city: str, d=10 * 10**3) -> str:
    GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")
    location = GEOLOCATOR.geocode(city)
    p = Proj("EPSG:3035", preserve_units=False)
    x, y = p(location.latitude, location.longitude)
    tl_lat, tl_lon = p(x - d, y + d, inverse=True)
    br_lat, br_lon = p(x + d, y - d, inverse=True)
    return f"{tl_lon},{tl_lat},{br_lon},{br_lat}"


def download_image(city: str, date: str):
    date = datetime.strptime(date, "%Y-%m-%d")

    start_date = datetime.strftime(date, "%Y-%m-%d")
    filename = f"tmp/{city}_{start_date}.jpeg"

    if (os.path.isfile(filename)):
        print('file exists: ', filename)
        return
    
    end_date = datetime.strftime(date + timedelta(days=1), "%Y-%m-%d")
    
    bbox = generate_bbox(city)
    bbox = BBox(bbox = eval(bbox), crs=CRS.WGS84)

    config = SHConfig()
    config.sh_client_id = '4dd7b50f-f4a0-452c-bb4b-28825691c7eb'
    config.sh_client_secret = 'dyHmnCao1{(_1^Re1]#M)>zP)fr.7rb}-U{q09RI'

    request = SentinelHubRequest(
        evalscript="""
        //VERSION=3

        function setup() {
        return {
            input: ["B02", "B03", "B04"],
            output: { bands: 3 }
        };
        }

        function evaluatePixel(sample) {
        return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,          
                time_interval=(f'{start_date}', f'{end_date}'),          
            ),
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.JPG),
        ],
        bbox=bbox,
        #size=[720, 480],
        size=bbox_to_dimensions(bbox, resolution=10),
        config=config
    )

    true_color_imgs = request.get_data()
    image = true_color_imgs[0]
    matplotlib.image.imsave(filename, image)


def main(city: str, date: str):
    download_image(city, date)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
