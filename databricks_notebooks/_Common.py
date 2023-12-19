# Databricks notebook source
# Common utilities

# COMMAND ----------

def assert_widget(value, name):
    if len(value.rstrip())==0:
        raise RuntimeError(f"ERROR: '{name}' widget is required")

# COMMAND ----------

def mk_local_path(path):
    return path.replace("dbfs:","/dbfs")

# COMMAND ----------

def dump_as_json(dct, output_file=None, sort_keys=None):
    import json
    content = json.dumps(dct, sort_keys=sort_keys, indent=2)
    print(content)
    if output_file:
        output_file = mk_local_path(output_file)
        print(">> output_file:",output_file)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

# COMMAND ----------

import mlflow

def show_mlflow_uris(msg):
    print(f"{msg}:")
    print("  mlflow.get_tracking_uri:", mlflow.get_tracking_uri())
    print("  mlflow.get_registry_uri:", mlflow.get_registry_uri())

# COMMAND ----------

def split_model_uri(model_uri):  
    toks = model_uri.split("/")
    return toks[1], toks[2]

# COMMAND ----------


def is_unity_catalog_model(model_name):
    return "." in model_name
    
def activate_unity_catalog(model_name):
    if model_name.startswith("models:/"):
        model_name = split_model_uri(model_name)[0]
    if is_unity_catalog_model(model_name):
        mlflow.set_registry_uri("databricks-uc")
        show_mlflow_uris("After Unity Catalog activation")
    else:
        mlflow.set_registry_uri("databricks")

# COMMAND ----------

def get_columns(lst):
    if len(lst) == 0:
        return 0
    mx, idx = 0, 0
    for j,m in enumerate(lst): 
        if len(m.keys()) > mx:
            mx = len(m.keys())
            idx = j
    return list(lst[idx].keys())

# COMMAND ----------

from pyspark.sql.functions import *

def adjust_timestamps(df, create_ts, update_ts):
    return df \
        .withColumn(create_ts,from_unixtime(col(create_ts)/1000, "yyyy-MM-dd hh:mm:ss")) \
        .withColumn(update_ts,from_unixtime(col(update_ts)/1000, "yyyy-MM-dd hh:mm:ss"))

# COMMAND ----------

def to_dataframe(lst, create_ts="creation_timestamp", update_ts="last_updated_timestamp"):
    """ 
    Default '_ts' arguments are for registered models and model versions. 
    For experiments they are: 'creation_time' and 'last_update_time'. :(
    """
    columns = get_columns(lst)
    print(f"Columns: {columns}")
    df = spark.read.json(sc.parallelize(lst)).select(columns)
    return adjust_timestamps(df, create_ts, update_ts)

# COMMAND ----------

import os
print("Versions:")
print(f"  MLflow version: {mlflow.__version__}")
print(f"  DBR version: {os.environ.get('DATABRICKS_RUNTIME_VERSION')}")
