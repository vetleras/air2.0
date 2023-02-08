from geopy.geocoders import Nominatim
import shapely
from geopy.distance import Distance
import geopy



geolocator = Nominatim(user_agent="NTNU TTK4852 group 1")
address = "Sevilla"
location = geolocator.geocode(address)

point = shapely.Point((location.latitude, location.longitude))
print(location.height)
# the distance arg in buffer is a bad approximation. Consider changing in the future
square = point.buffer(0.08, cap_style="square")
print(point, square)

from sentinelsat import SentinelAPI
from datetime import date

api = SentinelAPI('vetleras', 'tirsed-javru6-nixdAk', 'https://scihub.copernicus.eu/dhus/')

products = api.query(square,
                     date=(date(2023, 1, 8), date(2023, 2, 8)),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 30))

print(products)