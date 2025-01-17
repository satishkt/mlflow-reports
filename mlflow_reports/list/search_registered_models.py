"""
Search for registered models
"""

import numpy as np
import pandas as pd

from mlflow_reports.common import mlflow_utils
from . import list_utils


def search(filter=None, get_tags_and_aliases=False, unity_catalog=False):
    """
    :return: Returns registered models as list of Dicts.
    """
    mlflow_utils.use_unity_catalog(unity_catalog)
    models = mlflow_utils.search_registered_models(filter, get_tags_and_aliases)
    print(f"Found {len(models)} registered models")
    models = sorted(models, key=lambda x: x["name"])
    return models


def to_pandas_df(models, prefix=None, tags_and_aliases_as_string=False):
    if len(models) == 0:
        return pd.DataFrame()
    if prefix:
        models = [ m for m in models if m["name"].startswith(prefix)]
    models = sorted(models, key=lambda x: x["name"])
    for model in models:
        list_utils.kv_list_to_dict(model, "tags", mlflow_utils.mk_tags_dict, tags_and_aliases_as_string)
        list_utils.kv_list_to_dict(model, "aliases", mlflow_utils.mk_aliases_dict, tags_and_aliases_as_string)
        model.pop("latest_versions", None)

    df = pd.DataFrame.from_dict(models)
    df = df.replace(np.nan, "", regex=True)
    list_utils.to_datetime(df, ["creation_timestamp", "last_updated_timestamp"])
    return df
