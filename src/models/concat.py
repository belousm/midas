import argparse
import sys
import warnings
from typing import Optional, Text

import pandas as pd
from envyaml import EnvYAML
from pandas import DataFrame

warnings.filterwarnings("ignore")


def concat(
    config_path: Text,
) -> Optional[DataFrame]:
    """
    Concat results from dataframe with trend and dataframe with volume anomaly.

    Args:
        config_path {Text}: path to config
    """
    config = EnvYAML(config_path)
    sys.path.append(config["base"]["project_path"])
    from src.utils.logger import get_logger

    logger = get_logger("CONCAT", log_level=config["base"]["log_level"])

    logger.info("Read volume data")
    data_volume = pd.read_feather(config["data"]["result_volume_anomaly"])
    logger.info("Read trend data")
    data_trend = pd.read_feather(config["data"]["result_trend_detection"])
    column_with_anomaly = config["featurize"]["volume_anomaly"]["column_with_anomaly"]

    logger.info("Set index as `date`")
    data_volume = data_volume.set_index("date")
    data_trend = data_trend.set_index("date")

    logger.info("Sort dataframes by index")
    data_volume = data_volume.sort_index()
    data_trend = data_trend.sort_index()

    logger.info("Add to Trend DataFrame column with anomaly")
    data_trend[column_with_anomaly] = data_volume[column_with_anomaly]

    logger.info("Reset index")
    data_trend.reset_index(inplace=True)

    path = config["data"]["result_with_trend_and_anomaly"]
    logger.info(f"Writing data to path: {path}")
    data_trend.to_feather(path)


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--config", dest="config", required=True)
    args = args_parser.parse_args()
    concat(config_path=args.config)
