import requests
import io
import pandas as pd


def get_csv_urls(
    country_code: str, city: str, pollutant_nr: int = 6001
) -> list[str]:
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

city = "Sevilla"
urls = get_csv_urls("ES", city)
dfs = {}

for i, url in enumerate(urls):
    print(i+1, len(urls))
    # extract filename from url (ex. https://ereporting.blob.core.windows.net/downloadservice/NO_6001_28792_2013_timeseries.csv)
    filename = url.split("/")[-1]
    country_code, pollutant_nr, sampling_point, year, _ = filename.split("_")

    response = requests.get(url)
    response.raise_for_status()

    df = pd.read_csv(
        io.StringIO(response.text), parse_dates=True, index_col=0
    )

    if dfs.get(sampling_point) is None:
        dfs[sampling_point] = df
    else:
        dfs[sampling_point] = pd.concat([dfs[sampling_point], df])


with pd.ExcelWriter(f"{city}.xlsx") as writer:  
    for sampling_point, df in dfs.items():
        df.to_csv(f"{city}_{sampling_point}.csv")
        df.to_excel(writer, sheet_name=sampling_point)
