import argparse
import sys
import warnings
from datetime import timedelta
from typing import Optional, Text

import numpy as np
import pandas as pd
from envyaml import EnvYAML
from pandas import DataFrame, Timestamp
from tqdm import tqdm

warnings.filterwarnings("ignore")


def pct_change_mean(current_mean: float, args: tuple[float, np.nan]) -> list[float]:
    """
    Change between two rolling means.

    Args:
        current_mean {float}: Mean of current window.
        args {tuple[floar, np.mean]}: Tuple of means for comparing.

    Returns:
        list[float]: List of changes between current mean and others.
    """
    pct_change_means = []
    for previous_mean in args:
        if previous_mean:
            pct_change_means.append((current_mean - previous_mean) / current_mean)
    return pct_change_means


def daterange(end_date: Timestamp, gap_end_date: int, step: int) -> Timestamp:
    """
    Generator of end date until current with step.

    Args:
        end_date {float}: End date from which start to generate.
        gap_end_date {int}: Number of days between start date and end date.
        step {int}: Step of iteration from end date to start date.

    Returns:
        Timestamp: Next end date.
    """
    for m in range(0, gap_end_date - step, step):
        yield end_date - timedelta(minutes=m)


def anomaly_detection(pct_change_between_mean: float, threshold: float) -> bool:
    """
    Check change between rolling means. If larger then threshold, thus anomaly detected.

    Args:
        pct_change_between_mean {float}: Change between two rolling mean.
        threshold {float}: Treshold for anomaly detection.

    Returns:
        bool: Return flag of anomaly detection.
    """
    if pct_change_between_mean >= threshold:
        return True
    else:
        return False


def check_for_anomaly_in_window(
    config: EnvYAML, data: DataFrame, check_date: Timestamp, *args
) -> Optional[Timestamp]:
    """
    Checking for anomaly starting from current checkpoint to end of window.

    Args:
        config {EnvYAML}: Yaml file with configurations.
        data {DataFrame}: DataFrame of data.
        check_date {Timestamp}: Start date for checking.
        *args {float}: Tuple of means for comparing.

    Returns:
        bool: Return flag of anomaly detection.
    """
    from src.utils.exceptions import NoAvailableData

    if not args:
        raise NoAvailableData

    if np.all(np.isnan(args)):
        return None

    gap_end_date = config["featurize"]["volume_anomaly"]["gap_end_date"]
    step_to_end_date = config["featurize"]["volume_anomaly"]["step_to_end_date"]
    end_date = check_date + timedelta(minutes=gap_end_date)
    laps = config["featurize"]["volume_anomaly"]["laps"]
    thresholds = config["featurize"]["volume_anomaly"]["thresholds"]
    for lap, end_anomaly_date in enumerate(
        daterange(end_date, gap_end_date, step_to_end_date)
    ):
        current_mean = data.loc[
            (data.index >= check_date) & (data.index <= end_anomaly_date), "volume"
        ].mean()
        current_pct_change_between_mean = max(pct_change_mean(current_mean, args))
        if lap >= laps[-1]:
            id_of_threshold = -1
        else:
            id_of_threshold = next(i[0] for i in enumerate(laps) if i[1] > lap)
        anomaly_bool = anomaly_detection(
            current_pct_change_between_mean, thresholds[id_of_threshold]
        )
        if anomaly_bool:
            return end_anomaly_date


def find_volume_anomaly(
    config_path: Text,
) -> Optional[DataFrame]:
    """
    Data preparation for binary classification.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger("FIND_VOLUME_ANOMALY", log_level=config["base"]["log_level"])

    logger.info("Read preprocessed data")
    data = pd.read_feather(config["data"]["processed_volume_anomaly"])
    data.set_index("date", inplace=True)
    logger.info("Set date colums as index")
    mean_indicator = config["featurize"]["volume_anomaly"]["mean_indicator"]
    logger.info(f"Window for mean which will be used like indicator: {mean_indicator}")

    column_for_indicating = f"rolling_mean_{mean_indicator}_pct_ch"
    threshold_indicator = config["featurize"]["volume_anomaly"]["threshold_indicator"]
    logger.info(f"Treshold indicator: {threshold_indicator}")
    columns_rolling_mean = config["featurize"]["volume_anomaly"]["columns_rolling_mean"]
    logger.info(f"Windows for rolling means: {columns_rolling_mean}")
    anomaly_dates = []
    for current_date, checking_pct_change in tqdm(
        zip(data.index, data[column_for_indicating])
    ):
        if checking_pct_change > threshold_indicator:
            means = []
            for mean in columns_rolling_mean:
                means.append(
                    data.loc[data.index == current_date, f"rolling_mean_{mean}"].values[
                        0
                    ]
                )
            end_of_anomaly = check_for_anomaly_in_window(
                config, data, current_date, *means
            )
            if end_of_anomaly:
                anomaly_dates.append((current_date, end_of_anomaly))
    logger.info(f"Number of found anomalies: {len(anomaly_dates)}")
    column_with_anomaly_detection = config["featurize"]["volume_anomaly"][
        "column_with_anomaly"
    ]
    data[column_with_anomaly_detection] = False
    for start_date, end_date in tqdm(anomaly_dates):
        data.loc[
            (data.index >= start_date) & (data.index <= end_date),
            column_with_anomaly_detection,
        ] = True
    logger.info(f"Created new column {column_with_anomaly_detection}")
    for mean in columns_rolling_mean:
        data.drop([f"rolling_mean_{mean}"], axis=1, inplace=True)
    data.drop(
        [f"rolling_mean_{mean_indicator}", f"rolling_mean_{mean_indicator}_pct_ch"],
        axis=1,
        inplace=True,
    )
    logger.info("Drop additional columns")

    data.reset_index(inplace=True)
    logger.info("Reset index")
    path = config["data"]["result_volume_anomaly"]
    data.to_feather(path)
    data.info(f"Write data to {path}")


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    find_volume_anomaly(config_path=args.config)
