import numpy as np
from pyproj import Proj
from shapely import geometry

def distance_calculation(latitude, longitude):
  p = Proj('EPSG:3035', preserve_units=False)
  x,y = p(latitude, longitude)
  distance = 10*10**3
  point1 = [x-distance, y]
  point1_c = p(point1[0], point1[1], inverse=True)
  point2 = [x, y-distance]
  point2_c = p(point2[0], point2[1], inverse=True)

  max_latitude = np.max([np.abs(point1_c[0] - latitude), np.abs(point2_c[0] - latitude)])
  max_longitude = np.max([np.abs(point1_c[1] - longitude), np.abs(point2_c[1] - longitude)])

  offset = (max_latitude + max_longitude) / 2
  #https://stackoverflow.com/questions/30457089/how-to-create-a-shapely-polygon-from-a-list-of-shapely-points
  p1 = geometry.Point(latitude-offset, longitude-offset)
  p2 = geometry.Point(latitude-offset, longitude+offset)
  p3 = geometry.Point(latitude+offset, longitude+offset)
  p4 = geometry.Point(latitude+offset, longitude-offset)
  pointList = [p1, p2, p3, p4]
  poly = geometry.Polygon([[p.x, p.y] for p in pointList])

  return poly.wkt

if __name__ == "__main__":
  distance_calculation()