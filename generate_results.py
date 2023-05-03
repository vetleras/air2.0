import os
from pyproj import Proj
from datetime import datetime, timedelta
import matplotlib.image
from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    bbox_to_dimensions,
    SHConfig,
)
from tqdm import tqdm
from download_and_aggregate import City, load_cities, Measurement
from jinja2 import Template
from unidecode import unidecode
import pathlib


def generate_bbox(lat: float, lon: float, d=9 * 10**3) -> str:
    p = Proj("EPSG:3035", preserve_units=False)
    x, y = p(lat, lon)
    # tl top left, br bottom right
    tl_lat, tl_lon = p(x - d, y + d, inverse=True)
    br_lat, br_lon = p(x + d, y - d, inverse=True)
    return BBox((tl_lon, tl_lat, br_lon, br_lat), crs=CRS.WGS84)


def download_image(lat: float, lon: float, datetime: datetime, filename: str):
    if os.path.isfile(filename):
        return

    config = SHConfig()
    config.sh_client_id = "client_id"
    config.sh_client_secret = "client_secret"

    bbox = generate_bbox(lat, lon)
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
                time_interval=(datetime.date(), datetime.date() + timedelta(days=1)),
            ),
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.JPG),
        ],
        bbox=bbox,
        size=bbox_to_dimensions(bbox, resolution=10),
        config=config,
    )
    matplotlib.image.imsave(filename, request.get_data()[0])


def normalize(s: str) -> str:
    """
    Replace all non-ascii characters with ascii characters and replace all non-alphanumerical characters with underscores
    """
    return "".join(c if c.isalnum() else "_" for c in unidecode(s))


class Image:
    def __init__(
        self, city: City, datetime: datetime, measurement: Measurement
    ) -> None:
        self.filename = (
            f"{city.country_code}-{normalize(city.name)}-{datetime.date()}.jpg"
        )
        download_image(*city.location, datetime, "results/" + self.filename)
        self.datetime = datetime
        self.measurement = measurement


def generate_result(
    city: City,
    bad_image: Image,
    good_image: Image,
    filename: str,
    previous_result: str,
    next_result: str,
):
    with open("template.html", "r") as file:
        template: Template = Template(file.read())

    with open("results/" + filename, mode="w") as file:
        file.write(
            template.render(
                city=city,
                bad_image=bad_image,
                good_image=good_image,
                previous_result=previous_result,
                next_result=next_result,
            )
        )


if __name__ == "__main__":
    cities = load_cities()
    bad_aggregates = sorted(
        (
            (city, measurement, capture_datetime)
            for city in cities
            for measurement, capture_datetime in city.aggregates
        ),
        key=lambda c: c[1].value,
        reverse=True,
    )[:100]
    pathlib.Path.mkdir(pathlib.Path("results"), exist_ok=True)

    for i, (city, bad_measurement, bad_capture_datetime) in enumerate(
        tqdm(bad_aggregates)
    ):
        bad_image = Image(city, bad_capture_datetime, bad_measurement)

        good_measurement, good_capture_datetime = min(
            (aggregate for aggregate in city.aggregates), key=lambda a: a[0].value
        )
        good_image = Image(city, good_capture_datetime, good_measurement)

        generate_result(
            city,
            bad_image,
            good_image,
            filename=f"{i}.html",
            previous_result=f"{i-1}.html" if i > 0 else None,
            next_result=f"{i+1}.html" if i < len(bad_aggregates) - 1 else None,
        )
    print(f"file://{os.getcwd()}/results/0.html")
