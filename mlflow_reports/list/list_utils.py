import pandas as pd
from tabulate import tabulate
from mlflow_reports.common.timestamp_utils import TS_FORMAT
from mlflow_reports.common import object_utils


def to_datetime(df, column, datetime_as_string=False):
    df[column] = pd.to_datetime(df[column]/1000, unit="s").dt.round("1s")
    if datetime_as_string:
        df[column] = df[column].dt.strftime(TS_FORMAT)


def show_and_write(df, output_csv_file):
    """
    Display dataframe to stdout and write to file.
    """
    print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
    if output_csv_file:
        with open(output_csv_file, "w", encoding="utf-8") as f:
            df.to_csv(f, index=False)


def kv_list_to_dict(model_or_version, key, func, tags_and_aliases_as_string):
    """
    Convert a tag k/v list or alias k/v list to a dict.
    """
    kv_list = model_or_version.get(key)
    if kv_list:
        model_or_version[key] = func(kv_list)
        dct = func(kv_list)
        if tags_and_aliases_as_string:
            dct = object_utils.dict_to_json(dct)
        model_or_version[key] = dct