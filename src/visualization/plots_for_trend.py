import argparse
import sys
import warnings
from typing import Text

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from envyaml import EnvYAML

warnings.filterwarnings("ignore")


def plot_stock_with_trends(config_path: Text):
    """
    Detection of trend of stock market price.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger("PLOT_TREND", log_level=config["base"]["log_level"])
    logger.info("Read data")
    data = pd.read_feather(config["data"]["result_with_trend_and_anomaly"])

    column_with_value = config["featurize"]["trend_detection"]["column_for_macd"]
    column_with_trend = config["featurize"]["trend_detection"]["column_with_trend"]
    logger.info(f"Column with trend {column_with_trend}")
    logger.info(f"Column with values {column_with_value}")

    logger.info("Making copy for each trend")
    data_fall = data.copy()
    data_rise = data.copy()
    data_flat = data.copy()
    data_fall.loc[data_fall[column_with_trend] != "fall", column_with_value] = np.nan
    data_rise.loc[data_rise[column_with_trend] != "rise", column_with_value] = np.nan
    data_flat.loc[data_flat[column_with_trend] != "flat", column_with_value] = np.nan
    len_of_indices = len(data.index)
    divider = config["reports"]["trend_detection"]["step"]
    step = len_of_indices // divider
    logger.info(f"Step of intervals: {step}")

    intervals = [(i, i + step) for i in range(0, len_of_indices - step, step)]
    logger.info(f"Number of intervals {len(intervals)}")
    main_path = config["reports"]["path_to_trend_png"]["path_to_trend_png"]
    colors = config["reports"]["trend_detection"]["colors"]
    logger.info(f"Will use next colors: {colors}")
    for number, period in enumerate(intervals):
        plt.plot(
            data_fall.loc[
                (data_fall.index >= period[0]) & (data_fall.index <= period[1]),
                column_with_value,
            ],
            color=colors[0],
        )
        plt.plot(
            data_rise.loc[
                (data_rise.index >= period[0]) & (data_rise.index <= period[1]),
                column_with_value,
            ],
            color=colors[1],
        )
        plt.plot(
            data_flat.loc[
                (data_flat.index >= period[0]) & (data_flat.index <= period[1]),
                column_with_value,
            ],
            color=colors[2],
        )
        path = main_path + f"trend_{number}.png"
        logger.info(f"Path for {number} photo")
        plt.savefig(path)
        logger.info(f"Photo {number} saved")


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    plot_stock_with_trends(config_path=args.config)
