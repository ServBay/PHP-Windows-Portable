#!/usr/bin/env python3
"""Prepare an explicit Release file list from this run's original producer assets."""

import argparse
import json
import os
from pathlib import Path
import sys

try:
    from . import collect_split_assets as collector
except ImportError:
    import collect_split_assets as collector


_CONTEXT_ENV = "SPLIT_BUILD_CONTEXT_JSON"
_SELECTED_ENV = "SPLIT_SELECTED_EXTENSIONS_JSON"
_REQUEST_KEYS = collector._CONTEXT_KEYS - {"core_runtime_filename", "core_devel_filename"}


def _release_path(path):
    value = str(path)
    # softprops splits files on commas and interprets each entry as a glob pattern.
    if not value or any(ord(char) < 32 or char in ",*?[]{}!\\" for char in value):
        raise ValueError("Release file paths must be literal, single-line paths without commas or glob syntax")
    return value


def prepare_split_release(core_artifacts, extension_artifacts, output_dir):
    """Collect validated assets and emit files only after the exact index is verified."""
    context = json.loads(os.environ[_CONTEXT_ENV])
    selected = json.loads(os.environ[_SELECTED_ENV])
    # Match the build action's empty request when these optional inputs are absent.
    if isinstance(selected, list):
        for extension in selected:
            if isinstance(extension, dict):
                for key in ("args", "libs"):
                    extension.setdefault(key, "")
    if not isinstance(context, dict) or set(context) != _REQUEST_KEYS:
        raise ValueError("Release context requires exactly the documented request fields")
    producer = context.get("producer")
    if isinstance(producer, dict):
        # GitHub exposes run identity as decimal strings; collector records integers.
        for key in ("run_id", "run_attempt"):
            value = producer.get(key)
            if isinstance(value, str) and value.isascii() and value.isdecimal():
                producer[key] = int(value)
    github_output = os.environ["GITHUB_OUTPUT"]
    if not github_output:
        raise ValueError("GITHUB_OUTPUT must identify the Actions output file")
    output = Path(output_dir)
    _release_path(output)
    core = Path(core_artifacts)
    for role, field in (("runtime", "core_runtime_filename"), ("devel-pack", "core_devel_filename")):
        candidates = [path.name for path in core.iterdir()
                      if (identity := collector._core_identity(path.name)) and identity["role"] == role]
        if len(candidates) != 1:
            raise ValueError("Exactly one original core " + role + " ZIP is required")
        context[field] = candidates[0]
    receipt = collector.collect_split_assets(core, extension_artifacts, selected, context, output)
    index = output / "split-assets.json"
    if json.loads(index.read_text(encoding="utf-8")) != receipt:
        raise ValueError("Release index differs from the collector receipt")
    paths = [index] + [output / asset["filename"] for asset in receipt["assets"]]
    if set(output.iterdir()) != set(paths) or not all(path.is_file() for path in paths):
        raise ValueError("Release directory must contain exactly the indexed files")
    files = [_release_path(path) for path in paths]
    delimiter = "SPLIT_ASSET_FILES"
    while delimiter in files:
        delimiter += "_"
    with Path(github_output).open("a", encoding="utf-8") as stream:
        stream.write("files<<" + delimiter + "\n" + "\n".join(files) + "\n" + delimiter + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-artifacts", required=True)
    parser.add_argument("--extension-artifacts", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        prepare_split_release(args.core_artifacts, args.extension_artifacts, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        # JSON values can contain secrets or host paths; do not echo request data.
        print("Split Release preparation failed (" + type(error).__name__ + "); no files output emitted", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
