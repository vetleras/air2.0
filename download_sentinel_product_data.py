import pathlib
import click
from geopy.geocoders import Nominatim
from sentinelsat import SentinelAPI
from shapely import Point

GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")
API = SentinelAPI("vetlerastirsed-javru6-nixdAk", "tirsed-javru6-nixdAk")


@click.command()
@click.argument("cities", nargs=-1)
def main(cities: tuple[str]):
    """Download product data from Sentinel API and store them in sentinel_product_data/<city>.csv"""
    pathlib.Path(f"sentinel_product_data").mkdir(exist_ok=True)
    for city in cities:
        location = GEOLOCATOR.geocode(city)
        point = Point((location.latitude, location.longitude))
        products = API.query(
            point,
            area_relation="Contains",
            platformname="Sentinel-2",
            cloudcoverpercentage=(0, 30),
        )
        df = API.to_dataframe(products)
        df.to_csv(f"sentinel_product_data/{city}.csv")


if __name__ == "__main__":
    main()
