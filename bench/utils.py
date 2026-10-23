import os
import sys
import tomllib
import json
from pathlib import Path


def get_project_root():
    return Path(__file__).resolve().parent.parent


def load_config(config_path=None):
    if config_path is None:
        config_path = get_project_root() / "bench" / "config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def ensure_dirs(config=None):
    root = get_project_root()
    results_dir = root / (config["paths"]["results_dir"] if config else "results")
    dirs = [
        results_dir / "raw" / "hyperfine",
        results_dir / "raw" / "resource_monitor",
        results_dir / "raw" / "gc_logs",
        results_dir / "raw" / "steps",
        results_dir / "parsed",
        results_dir / "charts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_java_home(config):
    return Path(config["java"]["java_home"])


def get_program_args(config, scenario_id, threads=None):
    """Scenario `args` with {input} -> generator_output; {threads} is kept (hyperfine) unless given."""
    scenario = config["scenarios"][scenario_id]
    args = []
    for arg in scenario.get("args", []):
        arg = arg.replace("{input}", scenario.get("generator_output", ""))
        if threads is not None:
            arg = arg.replace("{threads}", str(threads))
        args.append(arg)
    return args


def get_java_command(config, scenario_id, threads=None):
    java_exe = get_java_home(config) / "bin" / "java.exe"
    jar_path = get_project_root() / config["scenarios"][scenario_id]["java_jar"]
    jvm_args = config["java"]["jvm_args"]
    return [str(java_exe)] + jvm_args + ["-jar", str(jar_path)] + get_program_args(config, scenario_id, threads)


def get_java_command_with_gc(config, scenario_id, gc_log_path, threads=None):
    java_exe = get_java_home(config) / "bin" / "java.exe"
    jar_path = get_project_root() / config["scenarios"][scenario_id]["java_jar"]
    jvm_args = config["java"]["jvm_args"]
    gc_flag = f"-Xlog:gc*:file={gc_log_path}:time,uptime,level,tags"
    return ([str(java_exe)] + jvm_args + [gc_flag, "-jar", str(jar_path)]
            + get_program_args(config, scenario_id, threads))


def get_rust_command(config, scenario_id, threads=None):
    rust_bin = get_project_root() / config["scenarios"][scenario_id]["rust_binary"]
    return [str(rust_bin)] + get_program_args(config, scenario_id, threads)


def get_command(config, scenario_id, lang, threads=None):
    if lang == "java":
        return get_java_command(config, scenario_id, threads)
    return get_rust_command(config, scenario_id, threads)


def get_thread_variants(scenario, key):
    """[(threads, file_suffix)]: one unsuffixed variant for single-threaded scenarios,
    otherwise one per value of `key` ("threads" or "resource_threads")."""
    if "threads" not in scenario:
        return [(None, "")]
    return [(p, f"_p{p}") for p in scenario.get(key, [])]


def get_steps_output(scenario, lang, threads):
    """Project-relative path of the per-step JSON the program writes, or None."""
    template = scenario.get("steps_output")
    if not template:
        return None
    return template.replace("{lang}", lang).replace("{threads}", str(threads))


def get_javac_exe(config):
    return str(get_java_home(config) / "bin" / "javac.exe")


def get_jar_exe(config):
    return str(get_java_home(config) / "bin" / "jar.exe")


def get_scenarios(config):
    return {k: v for k, v in config["scenarios"].items()}


def results_path(config, *parts):
    return get_project_root() / config["paths"]["results_dir"] / Path(*parts)


def save_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
