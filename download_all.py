import download_air_quality_data, download_sentinel_product_data

with open("cities.txt") as file:
    cities = file.readlines()

download_air_quality_data.main(cities)
download_sentinel_product_data.main(cities)