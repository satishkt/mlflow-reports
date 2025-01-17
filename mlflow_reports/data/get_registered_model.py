import click
from mlflow_reports.client import mlflow_client
from mlflow_reports.common import MlflowReportsException
from mlflow_reports.common import mlflow_utils
from mlflow_reports.common import permissions_utils
from mlflow_reports.common.click_options import(
    opt_registered_model,
    opt_get_versions,
    opt_get_latest_versions,
    opt_get_run,
    opt_get_permissions,
    opt_artifact_max_level,
    opt_get_raw,
    opt_silent,
    opt_output_file
)
from mlflow_reports.data import get_run, get_model_version
from mlflow_reports.data import data_utils, link_utils


def get(
        model_name,
        get_run = False,
        artifact_max_level = -1,
        get_versions = False,
        get_latest_versions = False,
        get_permissions = False,
        get_raw = False,
    ):
    if get_raw:
        return mlflow_client.get_registered_model(model_name)

    reg_model = mlflow_utils.get_registered_model(model_name, get_permissions)
    dct = { "registered_model": reg_model }
    dct["versions"] = enrich(reg_model, get_permissions, get_versions)
    if get_run:
        _get_runs(dct, artifact_max_level)
    if not get_latest_versions:
        reg_model.pop("latest_versions", None)
    return dct


def enrich(reg_model, get_permissions=False, get_versions=False, enrich_versions=False):
    model_name = reg_model["name"]
    reg_model["tags"] = mlflow_utils.mk_tags_dict(reg_model.get("tags"))
    data_utils.adjust_ts(reg_model, [ "creation_timestamp", "last_updated_timestamp" ])
    data_utils.adjust_uc(reg_model)
    link_utils.add_registered_model_links(reg_model)

    # get all versions
    if get_versions:
        versions = mlflow_client.search_model_versions(filter=f"name = '{model_name}'")
        versions = list(versions)
        if enrich_versions:
            for vr in versions:
                get_model_version.enrich(vr)

        if not mlflow_utils.is_unity_catalog_model(model_name):
            for vr in reg_model.get("latest_versions",[]):
                get_model_version.enrich(vr)
    else:
        versions = []
    if get_permissions and mlflow_utils.is_calling_databricks():
        permissions_utils.add_model_permissions(reg_model)
    return versions


def _get_runs(dct, artifact_max_level):
    runs = {}
    for vr in dct.get("versions"):
        try:
            runs[vr["version"]] = get_run.get(vr["run_id"], artifact_max_level=artifact_max_level)
        except MlflowReportsException as e:
            msg = { "model": vr["name"], "version": vr["version"], "run_id": vr["run_id"] }
            print(f'ERROR: Cannot get version run: {msg}. Exception: {e}')
    dct["version_runs"] = runs


@click.command()
@opt_registered_model
@opt_get_run
@opt_artifact_max_level
@opt_get_versions
@opt_get_latest_versions
@opt_get_permissions
@opt_get_raw
@opt_silent
@opt_output_file
def main(registered_model,
        get_run,
        artifact_max_level,
        get_versions,
        get_latest_versions,
        get_permissions,
        get_raw,
        silent,
        output_file
    ):
    print("Options:")
    for k,v in locals().items():
        print(f"  {k}: {v}")
    dct = get(
        model_name = registered_model,
        get_run = get_run,
        artifact_max_level = artifact_max_level,
        get_versions = get_versions,
        get_latest_versions = get_latest_versions,
        get_permissions = get_permissions,
        get_raw = get_raw,
    )
    data_utils.dump_object(dct, output_file, silent)


if __name__ == "__main__":
    main()
