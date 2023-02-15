import click
import pandas as pd
import os
import functools as ft

# Stakkars jævel som skal lese detta


@click.command()
@click.argument("city")
def main(city: str):
    """Output the worst dates for a given city which has data in air_quality_data and sentinel_product_data"""
    city_dir_path = os.path.join("air_quality_data", city)

    dfs = []
    for filename in os.listdir(city_dir_path):
        sampling_point = filename.split(".")[0]
        df = pd.read_csv(os.path.join(city_dir_path, filename))
        df = df.rename(
            columns={"DatetimeBegin": "time", "Concentration": sampling_point}
        )
        dfs.append(df.loc[:, ["time", sampling_point]])

    # https://stackoverflow.com/a/30512931
    df = ft.reduce(
        lambda left, right: pd.merge(left, right, on="time", how="outer"), dfs
    )

    df["max"] = df.max(axis=1, numeric_only=True)
    df.sort_values(by="max", ascending=False, inplace=True)
    df = df.head(100)
    df = df.loc[:, ["time", "max"]]
    df["time"] = pd.to_datetime(df["time"])

    img_df = pd.read_csv(os.path.join("sentinel_product_data", f"{city}.csv"))
    img_dates = pd.to_datetime(img_df["beginposition"], utc=True)

    print("img time, bad time, concentration")
    for _i, (time, max) in df.iterrows():
        t = min(img_dates, key=lambda x: abs(x - time))
        print(t, time, max)

# large discrepensies between img time and worst dates
# eo browser does not have the sentinel data


if __name__ == "__main__":
    main()
