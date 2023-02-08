import numpy as np
from pyproj import Proj

def distance_calculation(latitude, longitude):
  p = Proj('EPSG:3035', preserve_units=False)
  x,y = p(latitude, longitude)
  point1 = [x-10*10**3, y]
  point1_c = p(point1[0], point1[1], inverse=True)
  point2 = [x, y-10*10**3]
  point2_c = p(point2[0], point2[1], inverse=True)

  max_latitude = np.max([np.abs(point1_c[0] - latitude), np.abs(point2_c[0] - latitude)])
  max_longitude = np.max([np.abs(point1_c[1] - longitude), np.abs(point2_c[1] - longitude)])

  return (max_latitude + max_longitude) / 2

    