import argparse
import collections
import sys
import warnings
from typing import Dict, Optional, Text

import numpy as np
import pandas as pd
from envyaml import EnvYAML
from pandas import DataFrame
from scipy.signal import argrelextrema

warnings.filterwarnings("ignore")


def define_trend(value: str) -> str:
    """
    Define trend direction.

    Args:
        value {str}: Specifies the extremum refers to the local minimum or local maximum.

    Returns:
        str: Direction of stock price.
    """
    if value == "max":
        return "rise"
    else:
        return "fall"


def get_indices_of_extremes(signal_line: np.ndarray, order: int) -> tuple[np.ndarray]:
    """
    Find indices of local extremes.

    Args:
        signal_line {np.ndarray}: Signal line.
        order {int}: Number of points for comparison.

    Return:
        Tuple[np.ndarray]
    """
    indices_max = argrelextrema(signal_line, np.greater, order=order)
    indices_min = argrelextrema(signal_line, np.less, order=order)
    return indices_min[0], indices_max[0]


def make_directions_from_indices(
    indices_min: np.ndarray, indices_max: np.ndarray
) -> Dict[tuple[int], str]:
    """
    Find indices where stock price fall or rise.

    Args:
        indices_min {np.ndarray}: Indices of price with local min extreme.
        indices_max {np.ndarray}: Indices of price with local max extreme.

    Returns:
        Dict[tuple(int), str]: Dictionary with indices of stock price and detecting fall it or rise.
    """
    directions = {}
    for id_min in indices_min:
        directions[id_min] = "min"

    for id_max in indices_max:
        directions[id_max] = "max"

    od = collections.OrderedDict(sorted(directions.items()))
    directions = {}
    prev_key = 0
    for curr_key, value in od.items():
        directions[(prev_key, curr_key)] = define_trend(value)
        prev_key = curr_key

    return directions


def make_directions_from_indices_for_flat(
    data: DataFrame,
    indices_min: np.ndarray,
    indices_max: np.ndarray,
    window_size_for_rolling_mean: int,
    left_border_for_flat_detection: float,
    right_border_for_flat_detection: float,
) -> tuple[int]:
    """
    Find indices where stock price flatting.

    Args:
        data {DataFrame}: Our DataFrame for analyse.
        indices_min {np.ndarray}: Indices of price with local min extreme.
        indices_max {np.ndarray}: Indices of price with local max extreme.
        window_size_for_rolling_mean {int}: Window size for rolling mean.
        left_border_for_flat_detection {float}: Left border for flat detection.
        right_border_for_flat_detection {float}: Right border for flat detection.

    Returns:
        tuple(int): Tuple with indices where stock price flatting.
    """

    indices = np.sort(np.concatenate([indices_min, indices_max]))
    extremes_signals = data["signal_line"][indices]
    extremes_signals_pct_change = extremes_signals.pct_change()
    extremes_signals_pct_change_rolling_mean = extremes_signals_pct_change.rolling(
        window_size_for_rolling_mean
    ).mean()
    flats = []

    for ind, (signal_pct_change, index) in enumerate(
        zip(extremes_signals_pct_change_rolling_mean, indices)
    ):
        if (
            left_border_for_flat_detection
            < signal_pct_change
            < right_border_for_flat_detection
        ):
            flats.append((indices[ind - window_size_for_rolling_mean], index))
    return flats


def detect_trend(
    config_path: Text,
) -> Optional[DataFrame]:
    """
    Detection of trend of stock market price.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger("DETECT_TREND", log_level=config["base"]["log_level"])

    logger.info("Read preprocessed data")
    data = pd.read_feather(config["data"]["processed_trend_detection"])

    order_for_fall_rise = config["featurize"]["trend_detection"]["order_for_fall_rise"]
    logger.info("Find local extrema for falling and rising price")
    indices_min, indices_max = get_indices_of_extremes(
        np.array(data.signal_line), order_for_fall_rise
    )
    logger.info("Find directions of price using local extremes")
    directions = make_directions_from_indices(indices_min, indices_max)

    logger.info("Define last direction of trend")
    last_trend = "rise" if tuple(directions.values())[-1] == "fall" else "fall"
    directions[(tuple(directions.keys())[-1][1], data.index[-1])] = last_trend

    logger.info("Creating new column `trend`")
    column_with_trend = config["featurize"]["trend_detection"]["column_with_trend"]
    data[column_with_trend] = "null"
    for key, value in directions.items():
        if value == "fall":
            data.loc[
                (data.index >= key[0]) & (data.index <= key[1]), column_with_trend
            ] = "fall"
        else:
            data.loc[
                (data.index >= key[0]) & (data.index <= key[1]), column_with_trend
            ] = "rise"

    logger.info("Find local extrema for flatting price")
    order_for_flat = config["featurize"]["trend_detection"]["order_for_flat"]
    indices_min_flat, indices_max_flat = get_indices_of_extremes(
        np.array(data.signal_line), order_for_flat
    )

    window_size_for_rolling_mean = config["featurize"]["trend_detection"][
        "window_size_for_rolling_mean"
    ]
    logger.info(f"Window size for rolling mean: {window_size_for_rolling_mean}")
    left_border_for_flat_detection = config["featurize"]["trend_detection"][
        "left_border_for_flat_detection"
    ]
    logger.info(f"Left border for flat detection: {left_border_for_flat_detection}")
    right_border_for_flat_detection = config["featurize"]["trend_detection"][
        "right_border_for_flat_detection"
    ]
    logger.info(f"Right border for flat detection: {right_border_for_flat_detection}")
    indices_flat = make_directions_from_indices_for_flat(
        data,
        indices_min_flat,
        indices_max_flat,
        window_size_for_rolling_mean,
        left_border_for_flat_detection,
        right_border_for_flat_detection,
    )
    logger.info("Found indices where data flatting")
    logger.info(f"Fill {column_with_trend} column with `flat`")
    for flat in indices_flat:
        data.loc[
            (data.index >= flat[0]) & (data.index <= flat[-1]), column_with_trend
        ] = "flat"

    logger.info("Drop unnecessary columns: `signal_line` & `macd`")
    data.drop(["signal_line", "macd"], axis=1, inplace=True)
    path = config["data"]["result_trend_detection"]
    logger.info(f"Writing data to path: {path}")
    data.to_feather(path)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    detect_trend(config_path=args.config)
