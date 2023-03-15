import pathlib
from fpdf import FPDF
import requests
import aggregate
from pyproj import Proj
import requests
from distance_calculation import distance_calculation
from geopy.geocoders import Nominatim
from datetime import datetime
from datetime import timedelta
import os

GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")

with open("cities.txt") as file:
    cities = file.read().splitlines()


def generate_bbox(city: str, d=10 * 10**3) -> str:
    location = GEOLOCATOR.geocode(city)
    p = Proj("EPSG:3035", preserve_units=False)
    x, y = p(location.latitude, location.longitude)
    # tl: top left, br: bottom right
    tl_lat, tl_lon = p(x - d, y + d, inverse=True)
    br_lat, br_lon = p(x + d, y - d, inverse=True)
    return f"{tl_lon},{tl_lat},{br_lon},{br_lat}"


def download_image(bbox: str, date: datetime) -> str:
    url = (
        "https://services.sentinel-hub.com/ogc/wms/a1798443-a08f-4218-a2e0-118adfec219b"
    )
    start_date = date
    end_date = date +timedelta(days=1)
    params = {
        "REQUEST": "GetMap",
        "BBOX": bbox,
        "CRS": "CRS:84",
        "LAYERS": "NATURAL-COLOR",
        "MAXCC": "20",
        "WIDTH": "320",
        "HEIGHT": "320",
        "FORMAT": "image/jpeg",
        "TIME": f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
    }

    filename = f"tmp/{city}{date}.jpeg"
    with open(filename, "w+b") as file:
        response = requests.get(url, params=params)
        file.write(response.content)
    return filename

pathlib.Path("tmp").mkdir(exist_ok=True)
pdf = FPDF()
pdf.set_font("Courier")

for city in cities:
    df = aggregate.main(city)
    bbox = generate_bbox(city)
    for index, (measured_at, max, image_taken, time_diff) in df.iterrows():
        pdf.add_page(orientation="L")
        pdf.cell(
            180,
            10,
            f"{city} measured at: {measured_at}, concentration: {max}, image taken: {image_taken}",
            ln=2,
        )
        pdf.image(download_image(bbox, image_taken))
pdf.output(f"pics.pdf", "F")