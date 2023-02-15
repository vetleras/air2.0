import click
import pandas as pd
import requests
from geopy.geocoders import Nominatim
import io
import pathlib


def get_urls(city: str, country_code: str, pollutant_nr: int = 6001) -> list[str]:
    url = (
        "https://fme.discomap.eea.europa.eu/fmedatastreaming/AirQualityDownload/AQData_Extract.fmw"
        f"?CountryCode={country_code}"
        f"&CityName={city}"
        f"&Pollutant={pollutant_nr}"
        "&Year_from=2013"
        "&Year_to=2022"
        "&Station="
        "&Samplingpoint="
        "&Source=E1a"
        "&Output=TEXT"
        "&UpdateDate="
        "&TimeCoverage=Year"
    )
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = "utf-8-sig"  # to remove BOM at beginning of file
    return response.text.split()


# return dict[sampling_point, pd.DataFrame]
def get_dfs_for_city(city: str, country_code: str) -> dict[str, pd.DataFrame]:
    dfs = {}
    with click.progressbar(
        get_urls(city, country_code), label=f"fetching data for {city}"
    ) as progress_bar:
        for url in progress_bar:
            # extract filename from url (ex. https://ereporting.blob.core.windows.net/downloadservice/NO_6001_28792_2013_timeseries.csv)
            filename = url.split("/")[-1]
            _country_code, _pollutant_nr, sampling_point, _year, _ = filename.split("_")

            response = requests.get(url)
            response.raise_for_status()

            df = pd.read_csv(io.StringIO(response.text), parse_dates=True, index_col=0)

            if dfs.get(sampling_point) is None:
                dfs[sampling_point] = df
            else:
                dfs[sampling_point] = pd.concat([dfs[sampling_point], df])
    return dfs


GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")


def populate_citites_with_country_codes(cities: list[str]) -> list[tuple[str, str]]:
    return [
        (
            city,
            GEOLOCATOR.geocode(city, addressdetails=True, language="en")
            .raw["address"]["country_code"]
            .upper(),
        )
        for city in cities
    ]


@click.command()
@click.argument("cities", nargs=-1)
def main(cities: tuple[str]):
    """Download air quality data from discomap and store them in air_quality_data/city/<sampling_point>.csv"""
    for city, country_code in populate_citites_with_country_codes(cities):
        pathlib.Path(f"air_quality_data/{city}").mkdir(parents=True, exist_ok=True)
        dfs = get_dfs_for_city(city, country_code)
        for sampling_point, df in dfs.items():
            df.to_csv(f"air_quality_data/{city}/{sampling_point}.csv")


if __name__ == "__main__":
    main()
