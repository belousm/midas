import argparse
import sys
import warnings
from typing import Optional, Text

import pandas as pd
from envyaml import EnvYAML
from pandas import DataFrame

warnings.filterwarnings("ignore")


def preprocess_for_volume_anomaly(
    config_path: Text,
) -> Optional[DataFrame]:
    """
    Data preprocessing for volume anomaly search.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger(
        "PREPROCESSING_FOR_VOLUME_DETECTION", log_level=config["base"]["log_level"]
    )

    logger.info("Read initial data")
    data = pd.read_feather(config["data"]["raw"])
    columns_rolling_mean = config["featurize"]["volume_anomaly"]["columns_rolling_mean"]
    logger.info(f"Columns for rolling mean: {columns_rolling_mean}")
    for mean in columns_rolling_mean:
        data[f"rolling_mean_{mean}"] = data["volume"].rolling(mean).mean()

    mean_indicator = config["featurize"]["volume_anomaly"]["mean_indicator"]
    logger.info(f"Window for mean which will be used like indicator: {mean_indicator}")
    data[f"rolling_mean_{mean_indicator}"] = (
        data["volume"].rolling(mean_indicator).mean()
    )
    data[f"rolling_mean_{mean_indicator}_pct_ch"] = data[
        f"rolling_mean_{mean_indicator}"
    ].pct_change()

    path = config["data"]["processed_volume_anomaly"]
    logger.info(f"Writing data to path: {path}")
    data.to_feather(path)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    preprocess_for_volume_anomaly(config_path=args.config)
