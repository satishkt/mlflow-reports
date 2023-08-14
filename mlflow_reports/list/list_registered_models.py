"""
List all registered models.
"""

import click
from tabulate import tabulate
from mlflow_reports.client.http_client import get_mlflow_client
from . click_options import (
    opt_filter,
    opt_prefix,
    opt_get_tags_and_aliases,
    opt_tags_and_aliases_as_string,
    opt_unity_catalog,
    opt_max_description,
    opt_output_csv_file,
)
from . import search_registered_models

mlflow_client = get_mlflow_client()


def show(filter,
        prefix,
        get_tags_and_aliases,
        tags_and_aliases_as_string,
        unity_catalog,
        max_description,
        output_csv_file
    ):
    df = search_registered_models.search(filter, prefix, get_tags_and_aliases, tags_and_aliases_as_string, unity_catalog)
    if "description" in df and max_description:
        df["description"] = df["description"].str[:max_description]
    print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
    if output_csv_file:
        with open(output_csv_file, "w", encoding="utf-8") as f:
            df.to_csv(f, index=False)


@click.command()
@opt_filter
@opt_get_tags_and_aliases
@opt_tags_and_aliases_as_string
@opt_unity_catalog
@opt_prefix
@opt_max_description
@opt_output_csv_file

def main(filter, prefix, get_tags_and_aliases, tags_and_aliases_as_string, unity_catalog, max_description, output_csv_file):
    print("Options:")
    for k,v in locals().items():
        print(f"  {k}: {v}")
    show(filter, prefix, get_tags_and_aliases, tags_and_aliases_as_string, unity_catalog, max_description, output_csv_file)

if __name__ == "__main__":
    main()