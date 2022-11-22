import argparse
import sys
import warnings
from typing import Optional, Text

import pandas as pd
from envyaml import EnvYAML
from pandas import DataFrame

warnings.filterwarnings("ignore")


def macd(data: DataFrame, column: str, sm: int, lm: int, ds: int, ps: int) -> DataFrame:
    """
    Build Moving Average Convergence Divergence.

    Args:
        data {DataFrame}: Initial data.
        column {str}: Name of column for which build MACD.
        sm {int}: Decay in terms of center of mass.
        lm {int}: Decay in terms of span.
        ds {int}: Decay in terms of center of mass for signal line.
        ps {int}: Decay in terms of span for signal line.

    Returns:
        DataFrame: Result df with signal line and MACD.
    """

    data[f"sema_{column}_{sm}"] = (
        data[column].ewm(span=sm, min_periods=sm, adjust=False).mean()
    )
    data[f"lema_{column}_{lm}"] = (
        data[column].ewm(span=lm, min_periods=lm, adjust=False).mean()
    )

    data["macd"] = data[f"sema_{column}_{sm}"] - data[f"lema_{column}_{lm}"]
    data["signal_line"] = data.macd.ewm(span=ds, min_periods=ps, adjust=False).mean()
    data.drop([f"sema_{column}_{sm}", f"lema_{column}_{lm}"], axis=1, inplace=True)

    return data


def preprocess_for_trend_detection(
    config_path: Text,
) -> Optional[DataFrame]:
    """
    Data preprocessing for trend detection.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger(
        "PREPROCESSINF_FOR_TREND_DETECTION", log_level=config["base"]["log_level"]
    )

    logger.info("Read initial data")
    data = pd.read_feather(config["data"]["raw"])

    decay_sm = config["featurize"]["trend_detection"]["decay_sm"]
    decay_lm = config["featurize"]["trend_detection"]["decay_lm"]
    decay_signal = config["featurize"]["trend_detection"]["decay_signal"]
    period_signal = config["featurize"]["trend_detection"]["period_signal"]
    column_for_macd = config["featurize"]["trend_detection"]["column_for_macd"]

    data = macd(data, column_for_macd, decay_sm, decay_lm, decay_signal, period_signal)
    path = config["data"]["processed_trend_detection"]
    logger.info(f"Writing data to path: {path}")
    data.to_feather(path)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    preprocess_for_trend_detection(config_path=args.config)
