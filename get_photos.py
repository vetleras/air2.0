import sys
import requests
from PIL import Image
from geopy.geocoders import Nominatim
import numpy as np
from pyproj import Proj

RES = 640

def distance_calculation(latitude, longitude):
  p = Proj('EPSG:3857', preserve_units=False)
  x,y = p(latitude, longitude)

  point1 = [x-5*10**3, y]
  point1_c = p(point1[0], point1[1], inverse=True)
  point2 = [x, y-5*10**3]
  point2_c = p(point2[0], point2[1], inverse=True)

  max_latitude = np.max([np.abs(point1_c[0] - latitude), np.abs(point2_c[0] - latitude)])
  max_longitude = np.max([np.abs(point1_c[1] - longitude), np.abs(point2_c[1] - longitude)])

  offset = (max_latitude + max_longitude) / 2
  
  #p1 = [latitude-offset, longitude-offset]
  p2 = [latitude-offset, longitude+offset]
  #p3 = [latitude+offset, longitude+offset]
  p4 = [latitude+offset, longitude-offset]

  return [p2, p4]



def main(city):
    url = 'https://services.sentinel-hub.com/ogc/wms/a1798443-a08f-4218-a2e0-118adfec219b'
    GEOLOCATOR = Nominatim(user_agent="NTNU TTK4852 group 1")

    location = GEOLOCATOR.geocode(city)
    pointList = distance_calculation(location.latitude, location.longitude)

    p1 = pointList[0]
    p2 = pointList[1]
    box = ",".join([str(p2[1]), str(p1[0]), str(p1[1]), str(p2[0])])
    
    parameters = {
        'REQUEST'   : 'GetMap',
        'CRS'       : 'CRS:84',
        'BBOX'      : box,
        'LAYERS'    : 'NATURAL-COLOR',
        'MAXCC'     : '10',
        'WIDTH'     : RES,
        'HEIGHT'    : RES,
        'FORMAT'    : 'image/jpeg',
        #'TIME'      : '2023-01-20/2023-01-20'
    }

    response = requests.get(url, parameters)
    #print(response.request.url)
    image = response.content

    f = open('img.jpg','wb')
    f.write(image)
    f.close()
    
    img = Image.open('img.jpg')
    img.show()


if __name__ == "__main__":
    main(sys.argv[1])
