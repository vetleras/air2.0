import click
import pandas as pd
import os
import functools as ft
import datetime


@click.command()
@click.argument("city")
def main(city: str):
    """Output the worst dates for a given city which has data in air_quality_data and sentinel_product_data"""
    city_dir_path = os.path.join("air_quality_data", city)

    main_df = pd.DataFrame(columns=["time"])
    for filename in os.listdir(city_dir_path):
        df = pd.read_csv(os.path.join(city_dir_path, filename))
        df = df.rename(columns={"DatetimeBegin": "time", "Concentration": filename})
        main_df = pd.merge(
            main_df, df.loc[:, ["time", filename]], on="time", how="outer"
        )

    main_df["time"] = pd.to_datetime(main_df["time"])
    df = main_df[["time"]]

    df["max"] = main_df.max(axis=1, numeric_only=True)
    df = df.loc[df["max"] >= 50]
    df.sort_values(by="max", ascending=False, inplace=True)

    product_df = pd.read_csv(os.path.join("sentinel_product_data", f"{city}.csv"))
    images_taken = pd.to_datetime(product_df["beginposition"], utc=True)

    # measured_at, img_taken, max_concentration, time_difference [s]
    for index, (time, _max) in df.iterrows():
        image_taken = min(images_taken, key=lambda x: abs(x - time))
        df.at[index, "image_taken"] = image_taken
        df.at[index, "time_diff"] = abs(time - image_taken)

    df = df.loc[df["time_diff"] < datetime.timedelta(days=1)]
    print(df)


# large discrepensies between img time and worst dates
# eo browser does not have the sentinel data


if __name__ == "__main__":
    main()
