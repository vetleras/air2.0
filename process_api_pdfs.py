import pathlib
from fpdf import FPDF
import aggregate
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


config = SHConfig()
config.sh_client_id = '4dd7b50f-f4a0-452c-bb4b-28825691c7eb'
config.sh_client_secret = 'dyHmnCao1{(_1^Re1]#M)>zP)fr.7rb}-U{q09RI'

GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")


def generate_bbox(city: str, d=10 * 10**3) -> str:
    location = GEOLOCATOR.geocode(city)
    p = Proj("EPSG:3035", preserve_units=False)
    x, y = p(location.latitude, location.longitude)
    # tl: top left, br: bottom right
    tl_lat, tl_lon = p(x - d, y + d, inverse=True)
    br_lat, br_lon = p(x + d, y - d, inverse=True)
    return f"{tl_lon},{tl_lat},{br_lon},{br_lat}"


def download_image(bbox: str, date: datetime) -> str:
    start_date = datetime.strftime(date, "%Y-%m-%d")
    end_date = datetime.strftime(date + timedelta(days=1), "%Y-%m-%d")

    bbox = BBox(bbox = eval(bbox), crs=CRS.WGS84)

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
            SentinelHubRequest.output_response('default', MimeType.PNG),
        ],
        bbox=bbox,
        #size=[720, 480],
        size=bbox_to_dimensions(bbox, resolution=10),
        config=config
    )

    true_color_imgs = request.get_data()
    image = true_color_imgs[0]

    date = datetime.strftime(date, "%Y_%m_%d_%H_%M_%S")
    filename = f"tmp/{city}{date}.png"

    matplotlib.image.imsave(filename, image)

    return filename


with open("cities.txt") as file:
    cities = file.read().splitlines()

pathlib.Path("tmp").mkdir(exist_ok=True)
pdf = FPDF('L', 'mm', 'A3')
pdf.set_auto_page_break(False, margin = 0.0)
pdf.set_font("Courier")

for city in cities:
    df = aggregate.main(city)
    bbox = generate_bbox(city)
    for index, (measured_at, max, image_taken, time_diff) in df.iterrows():
        pdf.add_page(orientation="L")
        pdf.cell(
            0,
            10,
            f"{city} measured at: {measured_at}, concentration: {max}, image taken: {image_taken}",
            ln=1,
        )
        pdf.image(download_image(bbox, image_taken), None, None, 0, 260)
pdf.output(f"pics.pdf", "F")