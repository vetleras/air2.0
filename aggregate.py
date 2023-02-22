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

    main_df = pd.DataFrame(columns=["measured_at"])
    for filename in os.listdir(city_dir_path):
        df = pd.read_csv(os.path.join(city_dir_path, filename))
        df.rename(
            columns={"DatetimeBegin": "measured_at", "Concentration": filename},
            inplace=True,
        )
        main_df = pd.merge(
            main_df, df.loc[:, ["measured_at", filename]], on="measured_at", how="outer"
        )

    main_df["measured_at"] = pd.to_datetime(main_df["measured_at"])
    df = main_df[["measured_at"]]

    df["max"] = main_df.max(axis=1, numeric_only=True)
    df = df.loc[df["max"] >= 50]
    df.sort_values(by="max", ascending=False, inplace=True)

    product_df = pd.read_csv(os.path.join("sentinel_product_data", f"{city}.csv"))
    images_taken = pd.to_datetime(product_df["beginposition"], utc=True)

    # df: measured_at, img_taken, max_concentration, time_diff
    for index, (measured_at, _max) in df.iterrows():
        image_taken = min(images_taken, key=lambda x: abs(x - measured_at))
        df.at[index, "image_taken"] = image_taken
        df.at[index, "time_diff"] = abs(measured_at - image_taken)

    df = df.loc[df["time_diff"] < datetime.timedelta(days=1)]
    print(df)


if __name__ == "__main__":
    main()
