import sys
import requests
from PIL import Image
from geopy.geocoders import Nominatim
import numpy as np
from pyproj import Proj
from shapely import geometry

def distance_calculation(latitude, longitude):
  p = Proj('EPSG:3857', preserve_units=False)
  x,y = p(latitude, longitude)
  point1 = [x-10*10**3, y]
  point1_c = p(point1[0], point1[1], inverse=True)
  point2 = [x, y-10*10**3]
  point2_c = p(point2[0], point2[1], inverse=True)

  max_latitude = np.max([np.abs(point1_c[0] - latitude), np.abs(point2_c[0] - latitude)])
  max_longitude = np.max([np.abs(point1_c[1] - longitude), np.abs(point2_c[1] - longitude)])

  offset = (max_latitude + max_longitude) / 2
  p1 = [int((latitude-offset) * 1000000), int((longitude-offset) * 1000000)]
  p2 = [int((latitude-offset) * 1000000), int((longitude+offset) * 1000000)]
  p3 = [int((latitude+offset) * 1000000), int((longitude+offset) * 1000000)]
  p4 = [int((latitude+offset) * 1000000), int((longitude-offset) * 1000000)]
  pointList = [p1, p2, p3, p4]

  return pointList

def main(city):
    url = 'https://services.sentinel-hub.com/ogc/wms/a1798443-a08f-4218-a2e0-118adfec219b'
    GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")

    location = GEOLOCATOR.geocode(city)
    pointList = distance_calculation(location.latitude, location.longitude)
    
    p1 = pointList[1]
    p2 = pointList[3]
    box = ",".join([str(p1[0]), str(p1[1]), str(p2[0]), str(p2[1])])
    print(box)
    
    parameters = {
        'REQUEST'   : 'GetMap',
        'CRS'       : 'EPSG:4326',
        'BBOX'      : box,
        'LAYERS'    : 'NATURAL-COLOR',
        #'MAXCC'     : '20',
        'WIDTH'     : '320',
        'HEIGHT'    : '320',
        #'RESX'      : '320',
        #'RESY'      : '320',
        'FORMAT'    : 'image/jpeg',
        'TIME'      : '2023-01-20/2023-01-20'
    }

    image = requests.get(url, parameters).content

    f = open('img.jpg','wb')
    f.write(image)
    f.close()
    
    img = Image.open('img.jpg')
    img.show()


if __name__ == "__main__":
    main(sys.argv[1])
