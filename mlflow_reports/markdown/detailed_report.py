import sys
import click
import copy
from mdutils.mdutils import MdUtils

from mlflow_reports.mlflow_model import mlflow_model_manager as model_manager
from mlflow_reports.common import mlflow_utils, io_utils
from mlflow_reports.common.click_options import(
    opt_model_uri,
    opt_output_file,
    opt_get_permissions
)
from mlflow_reports.markdown.report_factory import ReportFactory, TAG_COLUMNS
from mlflow_reports.markdown.local_utils import newline_tweak, is_primitive

max_artifact_level = sys.maxsize


def build_report(model_uri, get_permissions, output_file, show_as_json=False, show_manifest=False):
    """
    Main entry point for report
    """
    data = model_manager.get(model_uri, get_permissions)

    card = MdUtils(file_name=output_file, title=f"MLflow Model: _{model_uri}_")
    rf = ReportFactory(card)

    _build_overview_model(rf.wf, data, show_manifest)
    _build_model_info(rf, data.get("mlflow_model"), show_as_json, 1)
    if data.get("registered_model"):
        _build_registered_model(rf, data.get("registered_model"))
    if data.get("model_version"):
        _build_model_version(rf.wf, data.get("model_version"))
    if data.get("run"):
        _build_run(rf, data.get("run"))
    if data.get("experiment"):
        _build_experiment(rf, data.get("experiment"))

    card.new_table_of_contents(table_title="Contents", depth=2)
    card.create_md_file()

    return data


def _build_overview_model(wf, data, show_manifest):
    wf.card.new_header(level=1, title="Model Overview")

    run_id = data.get("mlflow_model").get("run_id")
    flavor = get_native_flavor_adjusted(data.get("mlflow_model").get("flavors"))
    model_artifacts_size = _calc_model_size(run_id, data.get("mlflow_model")["artifact_path"])

    utc_time = data.get("mlflow_model").get("utc_time_created")
    utc_time_created = utc_time.split(".")[0]
    manifest = data.get("manifest")
    dct_mlflow_model = {
        "model_uri": manifest.get("model_uri"),
        "flavor": flavor.get("flavor"),
        "flavor_version": flavor.get("version"),
        "mlflow_version": data.get("mlflow_model").get("mlflow_version"),
        "size_bytes": f"{model_artifacts_size:,}",
        "databricks_runtime": data.get("mlflow_model").get("databricks_runtime",""),
        "time_created": utc_time_created
    }

    wf.build_table(dct_mlflow_model, "MLflow Model", level=0)

    _build_mlflow_model_uris(wf, manifest)

    if show_manifest:
        dct = copy.deepcopy(manifest)
        dct.pop("model_uris",None)
        wf.build_table(dct, "Manifest", level=0)


def _calc_model_size(run_id, model_artifact_path): 
    model_artifacts = mlflow_utils.build_artifacts(run_id, model_artifact_path, max_artifact_level)
    return model_artifacts["summary"]["num_bytes"]


def _build_mlflow_model_uris(wf, manifest): 
    dct = manifest.get("model_uris")
    run_uri = dct.get("run_uri")
    wf.build_table(dct, "MLflow Model URIs", level=0, columns=["URI type","URI"])


def get_native_flavor_adjusted(flavors):
    if len(flavors.keys()) == 1:
        return get_native_flavor_adjusted_fs(flavors)
    else:
        assert len(flavor.keys()) == 2
        return get_native_flavor_adjusted_std(flavors)


def get_native_flavor_adjusted_fs(flavors):
    """ 
    If feature store model with two MLmodel files. One flavor in top-leve MLmodel. 
    Actual flavor is in data/feature_store. TODO.
    """
    keys = list(flavors.keys())
    flavor = flavors.get(keys[0])
    dct = { 
        "flavor": flavor.get("loader_module"),
        "version": ""
    }
    return dct


def get_native_flavor_adjusted_std(flavors):
    """ 
    If standard model with one MLmodel file. 
    """
    keys = list(flavors.keys())
    pyfunc, native = flavors.get(keys[0]), flavors.get(keys[1])
    keys = list(flavors.keys())
    if keys[1] == "python_function":
        tmp = pyfunc  
        pyfunc = native
        native = tmp
    
    native = copy.deepcopy(native)
    
    matches = [ (k,v) for k,v in native.items() if k.endswith("_version") ]
    kv = matches[0]
    version = native.pop(kv[0], None)
        
    flavor_name = pyfunc.get("loader_module")
        
    flavor = { **{ "flavor": flavor_name, "version": version }, **native }
    return flavor 


def _build_model_info(rf, model_info, show_as_json=True, level=1, title="MLflow Model"):
    """
    Build MLflow model info section
    """
    def _build_model_info_details(wf, model_info, level):
        dct = { k:v for k,v in model_info.items() if is_primitive(v) }
        wf.mk_list_as_table(dct, title="Details", level=level)

    rf.wf.card.new_header(level=level, title=title)
    _build_model_info_details(rf.wf, model_info, level+1)

    rf.build_flavors(model_info.get("flavors"), level=level+2, show_as_json=show_as_json)
    
    rf.build_signature(model_info.get("signature"), level=level+1)
    rf.build_saved_input_example_info(model_info.get("saved_input_example_info"), level=level+1)

def _build_registered_model(rf, registered_model):
    rf.card.new_header(level=1, title="Registered Model")
        
    dct = { k:v for k,v in registered_model.items() if is_primitive(v) }
    newline_tweak(dct) 
    rf.wf.build_table(dct, "Details", level=2)
    
    tags = registered_model.get("tags")
    _build_tags(rf.wf, tags, level=2)
        
    rf.build_permissions(registered_model.get("permissions"), 2)


def _build_model_version(wf, model_version):
    wf.card.new_header(level=1, title="Registered Model Version")

    dct = { k:v for k,v in model_version.items() if is_primitive(v) }
    newline_tweak(dct)
    wf.build_table(dct, "Details", level=2)
    
    tags = model_version.get("tags")
    wf.build_table(tags, "Tags", level=2)


def _build_run(rf, run):
    """
    Build run datasources
    """
    rf.card.new_header(level=1, title="Run")
    data = run.get("data")
    tags = data.get("tags")

    info = run.get("info")
    newline_tweak(info)
    rf.wf.build_table(info, "Info", level=2)

    params = mlflow_utils.mk_tags_dict(data.get("params"))
    rf.wf.build_table(params, "Params", level=2, columns=["Param","Value"])

    x = mlflow_utils.mk_tags_dict(data.get("metrics"))
    rf.wf.build_table(x, "Metrics", level=2, columns=["Metric","Value"])

    rf.card.new_header(level=2, title="Inputs")
    _build_run_tags(rf, tags)


def _build_run_tags(rf, tags):
    rf.card.new_header(level=2, title="Tags")

    # == system and user tags

    def _strip_tag_prefix(dct, prefix):
        return { k.replace(prefix,""):v for k,v in dct.items() }

    def build_system_tags():
        #dct = _strip_tag_prefix(dct, "mlflow.databricks.")

        sys_tags, user_tags = {}, {}
        git_tags, nb_tags, cluster_tags, src_tags, ws_tags = {}, {}, {}, {}, {}

        for k,v in tags.items():
            if k.startswith("mlflow.databricks.gitRepo"):
                git_tags[k] = v
            elif k.startswith("mlflow.databricks.notebook"):
                nb_tags[k] = v
            elif k.startswith("mlflow.databricks.cluster"):
                cluster_tags[k] = v
            elif k.startswith("mlflow.databricks.w"):
                ws_tags[k] = v
            elif k.startswith("mlflow.source."):
                src_tags[k] = v
            elif k.startswith("mlflow"):
                sys_tags[k] = v
            else:
                user_tags[k] = v

        if git_tags:
            rf.wf.build_table(git_tags, "Git Repo Tags", level=3, **TAG_COLUMNS)
        if nb_tags:
            rf.wf.build_table(nb_tags, "Notebook Tags", level=3, **TAG_COLUMNS)
        if cluster_tags:
            rf.wf.build_table(cluster_tags, "Cluster Tags", level=3, **TAG_COLUMNS)
        if ws_tags:
            rf.wf.build_table(ws_tags, "Workspace Tags", level=3, **TAG_COLUMNS)
        if src_tags:
            rf.wf.build_table(src_tags, "Source Tags", level=3, **TAG_COLUMNS)
        rf.wf.build_table(sys_tags, "Other System Tags", level=3, **TAG_COLUMNS)
        rf.wf.build_table(user_tags, "User Tags", level=3, **TAG_COLUMNS)

    build_system_tags()

    # == exploded tags

    # sparkDatasourceInfo
    rf.wf.card.new_header(level=3, title="Exploded Tags")
    rf.build_sparkDatasourceInfo(tags.get("sparkDatasourceInfo"), 4)
    rf.build_cluster_stuff(tags, 4)


def _build_experiment(rf, experiment):
    rf.wf.card.new_header(level=1, title="Experiment")
    exp_info = experiment.get("experiment")
    if not exp_info:
        exp_info = experiment
    dct = { k:v for k,v in exp_info.items() if is_primitive(v) }
    rf.wf.build_table(dct, "Details", level=2)
    
    tags = exp_info.get("tags")
    _build_tags(rf.wf, tags, level=2)
            
    rf.build_permissions(experiment.get("permissions"), 2)


def _build_tags(wf, tags, level):
    wf.card.new_header(level=level, title="Tags")
    if not tags:
        wf.mk_not_present()
        return
    sys_tags, user_tags = {}, {}
    for k,v in tags.items():
        if k.startswith("mlflow"):
            sys_tags[k] = v
        else:
            user_tags[k] = v
    wf.build_table(sys_tags, "MLflow System Tags", level=level+1, **TAG_COLUMNS)
    wf.build_table(user_tags, "User Tags", level=level+1, **TAG_COLUMNS)


@click.command()
@opt_model_uri
@click.option("--show-as-json",
     help="Show as JSON selected fields",
     type=bool,
     default=False,
     show_default=True
)   
@click.option("--show-manifest",
     help="Show manifest stanza",
     type=bool,
     default=False,
     show_default=True
)   
@opt_output_file
@click.option("--output-data-file",
     help="Output JSON data file",
     type=str,
     default=None,
     show_default=True
)   
@opt_get_permissions

def main(model_uri, show_as_json, show_manifest, output_file, output_data_file, get_permissions):
    print("Options:")
    for k,v in locals().items():
        print(f"  {k}: {v}")
    data = build_report(model_uri, get_permissions, output_file, show_as_json, show_manifest)
    if (output_data_file):
        io_utils.write_file(output_data_file, data)

if __name__ == "__main__":
    main()
