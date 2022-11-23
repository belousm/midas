import argparse
import sys
import warnings
from typing import Text

import matplotlib.pyplot as plt
import pandas as pd
from envyaml import EnvYAML

warnings.filterwarnings("ignore")


def plot_volume_with_anomaly(config_path: Text):
    """
    Plot volume with anomaly.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger("PLOT_VOLUME_ANOMALY", log_level=config["base"]["log_level"])
    logger.info("Read data")
    data = pd.read_feather(config["data"]["result_with_trend_and_anomaly"])
    data.reset_index(inplace=True)
    column_with_anomaly = config["featurize"]["volume_anomaly"]["column_with_anomaly"]

    width_of_bar = config["reports"]["volume_anomaly"]["width_of_bar"]
    logger.info(f"Width of bar: {width_of_bar}")
    len_of_indices = len(data.index)
    divider = config["reports"]["volume_anomaly"]["step"]
    step = len_of_indices // divider

    logger.info(f"Step of intervals: {step}")
    intervals = [(i, i + step) for i in range(0, len_of_indices - step, step)]
    logger.info(f"Number of intervals {len(intervals)}")

    main_path = config["reports"]["volume_anomaly"]["path_to_volume_png"]
    colors = config["reports"]["volume_anomaly"]["colors"]
    logger.info(f"Will use next colors: {colors}")
    number_of_xticks = config["reports"]["volume_anomaly"]["number_of_xticks"] 
    logger.info(f"Number of xticks: {number_of_xticks}")
    all_dates = data["date"]
    step_for_dates = step // number_of_xticks
    logger.info("Creating list with colors")
    for _, row in data.iterrows():
        if row[column_with_anomaly]:
            colors.append(colors[0])
        else:
            colors.append(colors[1])
    for number, period in enumerate(intervals[1:2]):
        plt.bar(
            data.index[period[0] : period[1]],
            data[column_with_anomaly][period[0] : period[1]],
            width=width_of_bar,
            color=colors,
        )
        dates = [data.loc[data.index == i, "date"].values[0] for i in range(period[0], period[1], step_for_dates)]
        indeces = [i for i in range(period[0], period[1], step_for_dates)]
        dates = [all_dates[i+period[0]] for i in range(0, step, step_for_dates)]
        indeces = [i+period[0] for i in range(0, step, step_for_dates)]
        plt.xticks(indeces, dates, rotation = 45)
        plt.xlabel("Dates")
        plt.ylabel("Volume")
        plt.title("BTC volume with anomaly")
        path = main_path + f"volume_{number}.png"
        logger.info(f"Path for {number} photo")
        plt.savefig(path)
        plt.close()
        logger.info(f"Photo {number} saved")


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    plot_volume_with_anomaly(config_path=args.config)
