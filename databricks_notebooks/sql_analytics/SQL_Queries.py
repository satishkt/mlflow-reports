# Databricks notebook source
# MAGIC %md ## SQL Queries for MLflow models and versions tables
# MAGIC
# MAGIC ##### Overview
# MAGIC
# MAGIC * Analytics queries for the registed models and model versions database.
# MAGIC * To create the database, see the [Create_MLflow_Database]($Create_MLflow_Database) notebook.
# MAGIC
# MAGIC ##### Widgets
# MAGIC * `Database` - full path name such as `my_catalog.mlflow_uc`.

# COMMAND ----------

# MAGIC %md ### Setup

# COMMAND ----------

dbutils.widgets.text("Database", "")
database_name = dbutils.widgets.get("Database")
print("database_name:", database_name)

# COMMAND ----------

spark.sql(f"use {database_name}")

# COMMAND ----------

# MAGIC %md ### Describe tables

# COMMAND ----------

# MAGIC %md ##### Describe registered models table

# COMMAND ----------

# MAGIC %sql describe models

# COMMAND ----------

# MAGIC %md ##### Describe model versions table

# COMMAND ----------

# MAGIC %sql describe versions

# COMMAND ----------

# MAGIC %md ##### Counts

# COMMAND ----------

# MAGIC %sql select count(*) as num_models from models

# COMMAND ----------

# MAGIC %sql select count(*) as num_versions from versions

# COMMAND ----------

# MAGIC %md ### Registered models queries

# COMMAND ----------

# MAGIC %md #### Show number of models per user

# COMMAND ----------

# MAGIC %sql select user_id, count(*) as num_models from models group by user_id order by num_models desc

# COMMAND ----------

# MAGIC %md #### Show number of models per user

# COMMAND ----------

# MAGIC %sql select user_id, count(*) as num_models from models group by user_id order by num_models desc

# COMMAND ----------

# MAGIC %md #### Sort by `user_id`

# COMMAND ----------

# MAGIC %sql select user_id, * from models order by user_id, name

# COMMAND ----------

# MAGIC %md #### Sort by latest `creation_timestamp`

# COMMAND ----------

# MAGIC %sql select * from models order by creation_timestamp desc

# COMMAND ----------

# MAGIC %md #### Sort by earliest `creation_timestamp`

# COMMAND ----------

# MAGIC %sql select * from models order by creation_timestamp

# COMMAND ----------

# MAGIC %md ### Model versions queries

# COMMAND ----------

# MAGIC %sql select user_id, count(*) as num_versions from versions group by user_id order by num_versions desc

# COMMAND ----------

# MAGIC %sql select user_id, * from versions order by user_id, name

# COMMAND ----------

# MAGIC %sql select * from versions order by creation_timestamp desc

# COMMAND ----------

# MAGIC %sql select * from versions order by creation_timestamp
