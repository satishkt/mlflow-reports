# Databricks notebook source
# MAGIC %md ## List Registered Models
# MAGIC
# MAGIC **Overview**
# MAGIC * List registered models.
# MAGIC
# MAGIC **Widgets**
# MAGIC * `1. Filter` - `filter_string` argument for for [MlflowClient.search_registered_models](https://mlflow.org/docs/latest/python_api/mlflow.client.html#mlflow.client.MlflowClient.search_registered_models). 
# MAGIC   * `name like '%klearn%'`
# MAGIC * `2. Unity Catalog` - Use Unity Catalog.
# MAGIC * `3. Model prefix` - Since UC implementation of `search_registered_models` doesn't support `LIKE` in a filter, show only models starting with this prefix.
# MAGIC   * Note this is client-side logic. 
# MAGIC   * You can just write an SQL query on the Pandas dataframe response as in example below.
# MAGIC * `4. Get tags and aliases` 
# MAGIC * `5. Tags and aliases as string` - Return as string and not Pandas datetime

# COMMAND ----------

# MAGIC %md ### Setup

# COMMAND ----------

# MAGIC %run ../Common

# COMMAND ----------

dbutils.widgets.removeAll()

# COMMAND ----------

dbutils.widgets.text("1. Filter", "")
dbutils.widgets.dropdown("2. Unity Catalog", "no", ["yes", "no"])
dbutils.widgets.text("3. Model prefix (for UC)", "")
dbutils.widgets.dropdown("4. Get tags and aliases", "no", ["yes", "no"])
dbutils.widgets.dropdown("5. Tags and aliases as string", "no", ["yes", "no"])

filter = dbutils.widgets.get("1. Filter")
unity_catalog = dbutils.widgets.get("2. Unity Catalog") == "yes"
model_prefix = dbutils.widgets.get("3. Model prefix (for UC)")
get_tags_and_aliases = dbutils.widgets.get("4. Get tags and aliases") == "yes"
tags_and_aliases_as_string = dbutils.widgets.get("5. Tags and aliases as string") == "yes"

filter = filter or None
model_prefix = model_prefix or None

print("filter:", filter)
print("unity_catalog:", unity_catalog)
print("model_prefix:", model_prefix)
print("get_tags_and_aliases:", get_tags_and_aliases)
print("tags_and_aliases_as_string:", tags_and_aliases_as_string)

# COMMAND ----------

# MAGIC %md ### Search registered models 

# COMMAND ----------

from mlflow_reports.list import search_registered_models

pandas_df = search_registered_models.search(
    filter = filter, 
    unity_catalog = unity_catalog,
    prefix = model_prefix,
    get_tags_and_aliases = get_tags_and_aliases,
    tags_and_aliases_as_string = tags_and_aliases_as_string
)

# COMMAND ----------

# MAGIC %md ### Display Pandas DataFrame

# COMMAND ----------

pandas_df

# COMMAND ----------

# MAGIC %md ### Display as Spark DataFrame

# COMMAND ----------

df = spark.createDataFrame(pandas_df)
display(df)

# COMMAND ----------

# MAGIC %md ### Some SQL queries for registered models

# COMMAND ----------

df.createOrReplaceTempView("models")

# COMMAND ----------

# MAGIC %md #### Sort by `user_id`

# COMMAND ----------

# MAGIC %sql select * from models order by user_id, name

# COMMAND ----------

# MAGIC %md #### Sort by latest `creation_timestamp`

# COMMAND ----------

# MAGIC %sql select * from models order by creation_timestamp desc

# COMMAND ----------

# MAGIC %md #### Sort by earliest `creation_timestamp`

# COMMAND ----------

# MAGIC %sql select * from models order by creation_timestamp