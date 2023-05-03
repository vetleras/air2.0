from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import os
import pickle
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.location import Location
from sentinelsat import SentinelAPI
from tqdm import tqdm
import requests
import csv


@dataclass
class Measurement:
    sampling_point: str
    value: int
    datetime: datetime


class City:
    def __init__(self, name: str, country_code: str) -> None:
        self.name = name
        self.country_code = country_code
        self.location: Optional[Tuple[float, float]] = None
        self.measurements: list[Measurement] = []
        self.capture_dates: list[datetime] = []
        self.aggregates: list[Tuple[Measurement, datetime]] = []

    def save(self):
        with open("cities.pkl-hex", "a+") as file:
            file.write(pickle.dumps(self).hex() + "\n")


def get_location(city: str, country_code: str) -> Optional[Tuple[float, float]]:
    location: Location = Nominatim(user_agent="NTNU TTK4852 group 1").geocode(
        {"city": city, "country": country_code}
    )
    if location is not None:
        return (location.latitude, location.longitude)


def get_measurement_urls(city: str, country_code: str) -> list[str]:
    url = "https://fme.discomap.eea.europa.eu/fmedatastreaming/AirQualityDownload/AQData_Extract.fmw"
    response = requests.get(
        url,
        params={
            "CountryCode": country_code,
            "CityName": city,
            "Pollutant": 6001,
            "Year_from": 2013,
            "Year_to": 2022,
            "Source": "E1a",
            "Output": "TEXT",
        },
    )
    response.raise_for_status()
    response.encoding = "utf-8-sig"
    return response.text.split()


def get_measurements(city: str, country_code: str) -> list[Measurement]:
    measurements = []
    for url in get_measurement_urls(city, country_code):
        response = requests.get(url)
        response.raise_for_status()
        reader = csv.DictReader(response.text.splitlines())
        for row in reader:
            if row["Concentration"] == "":
                continue
            measurement = Measurement(
                sampling_point=row["AirQualityStationEoICode"],
                value=round(float(row["Concentration"])),
                datetime=datetime.strptime(
                    row["DatetimeBegin"], "%Y-%m-%d %H:%M:%S %z"
                ),
            )
            measurements.append(measurement)
    return measurements


def get_capture_dates(lat: float, lon: float) -> list[datetime]:
    products = SentinelAPI(
        "username",
        "password",
        show_progressbars=False,
    ).query(
        area=f"{lat}, {lon}",
        area_relation="Contains",
        platformname="Sentinel-2",
        producttype="S2MSI2A",
        cloudcoverpercentage=(0, 30),
    )
    return [
        product["beginposition"].replace(tzinfo=timezone.utc)
        for product in products.values()
    ]


def aggregate(
    capture_datetimes: list[datetime], measurements: list[Measurement]
) -> list[Tuple[Measurement, datetime]]:
    """
    Return all (measurement, capture_datetime) where the measurement is the most recent one within 24 hours before the capture.
    If there are multiple applicable measurements, then the largest one is chosen.

    Subsequent captures at the same time are ignored.
    """
    # Aggregation strategy:
    # Assume capture_datetimes sorted in ascending order and measurements sorted in descending order by datetime, value.
    # Take the first (least recent) capture and pop measurements until the second to last occured after the capture.
    # The last measurement is now the most recent before (or simultanious) the capture. Add this to result and repeat.
    aggregates = []
    measurements = sorted(
        measurements, key=lambda m: (m.datetime, m.value), reverse=True
    )
    for capture_datetime in sorted(capture_datetimes):
        if not measurements:
            return aggregates

        while len(measurements) > 1 and measurements[-2].datetime < capture_datetime:
            measurements.pop()

        measurement = measurements.pop()
        if timedelta() < capture_datetime - measurement.datetime < timedelta(days=1):
            aggregates.append((measurement, capture_datetime))
    return aggregates


def load_cities() -> list[City]:
    if os.path.isfile("cities.pkl-hex"):
        with open("cities.pkl-hex", "r") as file:
            return [pickle.loads(bytes.fromhex(row)) for row in file]
    else:
        return []


if __name__ == "__main__":
    with open("cities.json", "r") as file:
        city_bar = tqdm(json.load(file)[len(load_cities()) :], unit="city")

    for country_code, city_name in city_bar:
        city = City(city_name, country_code)

        def describe(s: str):
            city_bar.set_description(f"{city.country_code} {city.name} - {s}")

        describe("getting location")
        city.location = get_location(city_name, country_code)
        if city.location is None:
            describe("writing to file")
            city.save()
            continue

        describe("downloading measurements")
        city.measurements = get_measurements(city_name, country_code)
        if not city.measurements:
            describe("writing to file")
            city.save()
            continue

        describe("downloading capture datetimes")
        city.capture_dates = get_capture_dates(*city.location)

        describe("aggregating")
        city.aggregates = aggregate(city.capture_dates, city.measurements)

        describe("writing to file")
        city.save()
