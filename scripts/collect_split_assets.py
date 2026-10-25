#!/usr/bin/env python3
"""Collect existing PHP producer ZIPs offline; this is not a v2 package builder."""

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from urllib.parse import urlsplit
import zipfile


_DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.I)
_CORE = re.compile(
    r"php-(?:(?P<role>devel-pack|debug-pack|test-pack)-)?(?P<version>.+?)-"
    r"(?P<nts>nts-)?Win32-(?P<toolset>(?:vs|vc)\d+)-(?P<arch>x64|x86)\.zip", re.I)
_MODULE = re.compile(r"php_.+-(?P<thread>nts|ts)-(?:vs|vc)\d+-(?P<arch>x86_64|x64|x86)\.zip", re.I)
_RECEIPT_SCHEMA = "servbay.php-extension-consumed-core.v1"
_CONTEXT_KEYS = {
    "producer", "display_version", "source_ref", "build_version", "build_branch",
    "arch", "thread_safe", "core_runtime_filename", "core_devel_filename",
}


def _relative_path(name):
    if (not isinstance(name, str) or not name or "\\" in name
            or any(ord(char) < 32 or char in '<>:"|?*' for char in name)
            or any(part in {"", ".", ".."} or part.endswith((".", " ")) or _DEVICE.match(part)
                   for part in name.split("/"))):
        raise ValueError(f"Unsafe Windows relative path: {name!r}")
    return name


def _namespace(entries):
    nodes, explicit = {}, set()
    for name, directory in entries:
        _relative_path(name)
        key = name.casefold()
        if key in explicit:
            raise ValueError("Duplicate archive or artifact path: " + name)
        explicit.add(key)
        parts = name.split("/")
        for index in range(1, len(parts) + 1):
            path = "/".join(parts[:index])
            key = path.casefold()
            node = (path, directory if index == len(parts) else True)
            if key in nodes and nodes[key] != node:
                raise ValueError("Archive or artifact path collision: " + path)
            nodes[key] = node


def _text(value, field):
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise ValueError("Expected nonempty text for " + field)
    return value


def _public_url(value):
    _text(value, "extension URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.hostname.lower() == "localhost"):
        raise ValueError("Extension URL must be a public HTTPS reference without credentials/query/fragment")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        if "." not in parsed.hostname:
            raise ValueError("Extension URL must use a public hostname")
    else:
        if not address.is_global:
            raise ValueError("Extension URL must use a public address")


def _validate_inputs(context, selected):
    if not isinstance(context, dict) or set(context) != _CONTEXT_KEYS:
        raise ValueError("build_context requires exactly the documented fields")
    producer = context["producer"]
    if (not isinstance(producer, dict) or set(producer) != {"repository", "commit", "run_id", "run_attempt"}
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", str(producer.get("repository", "")))
            or not re.fullmatch(r"[a-fA-F0-9]{40}", str(producer.get("commit", "")))
            or any(type(producer.get(key)) is not int or producer[key] < 1 for key in ("run_id", "run_attempt"))):
        raise ValueError("Invalid explicit producer repository/commit/run identity")
    for key in ("display_version", "source_ref", "build_version", "build_branch"):
        # prepare deliberately leaves BUILD_BRANCH empty for release tags.
        if key == "build_branch" and context[key] == "":
            continue
        _text(context[key], key)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+~-]*", context[key]):
            raise ValueError("Invalid public build reference: " + key)
    _relative_path(context["display_version"])
    if "/" in context["display_version"]:
        raise ValueError("display_version must fit the producer artifact name")
    if context["arch"] not in ("x64", "x86") or context["thread_safe"] not in ("nts", "ts"):
        raise ValueError("Unsupported producer architecture or thread_safe value")
    for key in ("core_runtime_filename", "core_devel_filename"):
        if "/" in _relative_path(context[key]):
            raise ValueError("Core filenames must be artifact top-level basenames")
    if not isinstance(selected, list):
        raise ValueError("selected_extensions must be the prepare job's JSON list")
    names = set()
    for extension in selected:
        if not isinstance(extension, dict) or set(extension) != {"name", "url", "ref", "args", "libs"}:
            raise ValueError("Selected extensions require name/url/ref/args/libs")
        name = extension["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_-]*", name) or name.casefold() in names:
            raise ValueError("Invalid or duplicate selected extension name")
        names.add(name.casefold())
        _public_url(extension["url"])
        _text(extension["ref"], "extension ref")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+~-]*", extension["ref"]):
            raise ValueError("Invalid public extension ref")
        for key in ("args", "libs"):
            if not isinstance(extension[key], str) or any(ord(char) < 32 for char in extension[key]):
                raise ValueError("Requested args/libs must be strings without control characters")


def _hash_file(path):
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Input changed while hashing: " + path.name)
    return {"bytes": size, "sha256": digest.hexdigest()}


def _inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Artifact input must be a real directory")
    entries, files = [], {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        mode = path.lstat()
        if stat.S_ISDIR(mode.st_mode):
            entries.append((name, True))
        elif stat.S_ISREG(mode.st_mode) and mode.st_nlink == 1:
            entries.append((name, False))
            files[name] = _hash_file(path)
        else:
            raise ValueError("Artifact links and special files are unsupported: " + name)
    _namespace(entries)
    return entries, files


def _core_identity(filename):
    match = _CORE.fullmatch(filename)
    if not match:
        return None
    return {"role": match["role"] or "runtime", "version": match["version"],
            "toolset": match["toolset"].lower(), "arch": match["arch"].lower(),
            "thread_safe": "nts" if match["nts"] else "ts"}


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field: " + key)
        result[key] = value
    return result


def _json_receipt(path):
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream, object_pairs_hook=_json_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as error:
        raise ValueError("Cannot read extension consumption receipt: " + path.name) from error
    if not isinstance(value, dict):
        raise ValueError("Extension consumption receipt must be a JSON object")
    return value


def _sha256(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("Invalid SHA256 for " + field)
    return value


def _positive_int(value, field):
    if type(value) is not int or value < 1:
        raise ValueError("Expected positive integer for " + field)
    return value


def _receipt_input(value, role, expected):
    keys = {"role", "filename", "bytes", "sha256", "source"}
    if not isinstance(value, dict) or not keys.issubset(value) or set(value) - keys - {"url"}:
        raise ValueError("Invalid " + role + " consumption input")
    if value["role"] != role or value["filename"] != expected["filename"]:
        raise ValueError("Consumption input role/filename mismatch: " + role)
    if type(value["bytes"]) is not int or value["bytes"] != expected["bytes"]:
        raise ValueError("Consumption input bytes mismatch: " + role)
    if _sha256(value["sha256"], role) != expected["sha256"]:
        raise ValueError("Consumption input SHA256 mismatch: " + role)
    source = value["source"]
    if source not in ("local", "primary", "fallback"):
        raise ValueError("Consumption input source is unsupported: " + role)
    if source == "local":
        if "url" in value:
            raise ValueError("Local consumption input must not contain a URL: " + role)
    else:
        _public_url(value.get("url"))
        if not value["url"].endswith("/" + expected["filename"]):
            raise ValueError("Consumption input URL does not end with its selected filename: " + role)
    return {key: value[key] for key in ("role", "filename", "bytes", "sha256", "source", "url")
            if key in value}


def _validate_consumption_receipt(value, selected, context, runtime, devel, output):
    """Return a path-free normalized receipt after binding every digest and identity."""
    if set(value) != {"schema", "extension", "request", "inputs", "output", "producer"}:
        raise ValueError("Extension consumption receipt has unexpected or missing fields")
    if value["schema"] != _RECEIPT_SCHEMA:
        raise ValueError("Unsupported extension consumption receipt schema")

    extension = value["extension"]
    if (not isinstance(extension, dict)
            or set(extension) != {"name", "package_name", "ref", "requested_ref"}):
        raise ValueError("Invalid consumption receipt extension identity")
    if (extension["name"] != selected["name"]
            or extension["requested_ref"] != selected["ref"]):
        raise ValueError("Consumption receipt does not describe the selected extension")
    _text(extension["ref"], "normalized extension ref")
    _text(extension["package_name"], "extension package_name")

    request = value["request"]
    request_keys = {"php_version", "arch", "arch_canonical", "ts", "vs_version", "vs_toolset"}
    if not isinstance(request, dict) or set(request) != request_keys:
        raise ValueError("Invalid consumption receipt request")
    php_version = request["php_version"]
    if (not isinstance(php_version, str)
            or not re.fullmatch(r"(?:master|\d+\.\d+)", php_version)
            or (php_version != "master" and not context["source_ref"].startswith(php_version + "."))):
        raise ValueError("Consumption receipt PHP series does not match the producer build")
    if request["arch"] != context["arch"] or request["ts"] != context["thread_safe"]:
        raise ValueError("Consumption receipt architecture/thread does not match the build context")
    if request["arch_canonical"] != {"x64": "x86_64", "x86": "x86"}[context["arch"]]:
        raise ValueError("Consumption receipt canonical architecture is wrong")
    toolset = _core_identity(context["core_runtime_filename"])["toolset"]
    if request["vs_version"] != toolset:
        raise ValueError("Consumption receipt Visual Studio family does not match core filenames")
    _text(request["vs_toolset"], "requested VS toolset")

    inputs = value["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != {"runtime", "devel"}:
        raise ValueError("Consumption receipt requires exactly runtime and devel inputs")
    receipt_runtime = _receipt_input(inputs["runtime"], "runtime", runtime)
    receipt_devel = _receipt_input(inputs["devel"], "devel", devel)

    if value["producer"] != context["producer"]:
        raise ValueError("Consumption receipt producer identity does not match the build context")

    receipt_output = value["output"]
    if (not isinstance(receipt_output, dict)
            or set(receipt_output) != {"filename", "bytes", "sha256"}
            or receipt_output["filename"] != output["filename"]
            or type(receipt_output["bytes"]) is not int
            or receipt_output["bytes"] != output["bytes"]
            or _sha256(receipt_output["sha256"], "extension output") != output["sha256"]):
        raise ValueError("Consumption receipt output does not match the packaged extension ZIP")
    expected_prefix = "php_" + extension["package_name"] + "-" + extension["ref"] + "-"
    if not receipt_output["filename"].casefold().startswith(expected_prefix.casefold()):
        raise ValueError("Consumption receipt package identity does not match the output filename")
    return {
        "schema": _RECEIPT_SCHEMA,
        "extension": {"name": extension["name"], "package_name": extension["package_name"],
                      "ref": extension["ref"], "requested_ref": extension["requested_ref"]},
        "request": {key: request[key] for key in sorted(request_keys)},
        "inputs": {"runtime": receipt_runtime, "devel": receipt_devel},
        "output": {"filename": receipt_output["filename"], "bytes": receipt_output["bytes"],
                   "sha256": receipt_output["sha256"]},
        "producer": {key: context["producer"][key]
                     for key in ("repository", "commit", "run_id", "run_attempt")},
    }


def _select_assets(core_inventory, extension_inventory, selected, context):
    core_entries, core_files = core_inventory
    extension_entries, extension_files = extension_inventory
    if any(directory or "/" in name or not name.lower().endswith(".zip") for name, directory in core_entries):
        raise ValueError("Core artifact must contain original top-level ZIPs")
    candidates = {role: [] for role in ("runtime", "devel-pack")}
    for name in core_files:
        identity = _core_identity(name)
        if identity and identity["role"] in candidates:
            candidates[identity["role"]].append(name)
    runtime, devel = context["core_runtime_filename"], context["core_devel_filename"]
    if candidates != {"runtime": [runtime], "devel-pack": [devel]}:
        raise ValueError("Exactly the declared core runtime and devel ZIPs are required")
    identities = [_core_identity(runtime), _core_identity(devel)]
    for identity in identities:
        if any(identity[key] != context[key] for key in ("arch", "thread_safe")):
            raise ValueError("Core filename architecture/thread does not match build context")
    if any(identities[0][key] != identities[1][key] for key in ("version", "toolset")):
        raise ValueError("Core runtime and devel filenames describe different builds")

    core_artifact = f"php-build-artifacts-{context['arch']}-{context['thread_safe']}"
    assets = []
    for name in core_files:
        if name == runtime:
            role = "core-runtime"
        elif name == devel:
            role = "core-devel"
        elif name.startswith("php-") and name.endswith("-src.zip"):
            role = "core-source"
        elif name.startswith("php-debug-pack-"):
            role = "core-debug"
        elif name.startswith("php-test-pack-"):
            role = "core-test"
        else:
            role = "core-ancillary"
        assets.append({"role": role, "source_artifact": core_artifact, "source_path": name,
                       "original_filename": name, "filename": role + "--" + name})

    groups = {f"extension-{item['name']}-{context['display_version']}-{context['arch']}-{context['thread_safe']}": item["name"]
              for item in selected}
    actual_groups = {name for name, directory in extension_entries if "/" not in name and directory}
    if actual_groups != set(groups) or any("/" not in name and not directory for name, directory in extension_entries):
        raise ValueError("Extension artifact groups do not exactly match selected extensions")
    evidence = {}
    for group, name in groups.items():
        files = [path[len(group) + 1:] for path in extension_files if path.startswith(group + "/")]
        payloads = [path for path in files if "/" not in path and path.lower().endswith(".zip")]
        if len(payloads) != 1:
            raise ValueError("Extension requires one top-level runtime ZIP: " + name)
        payload = payloads[0]
        match = _MODULE.fullmatch(payload)
        if not match or match["thread"].lower() != context["thread_safe"] or {"x86_64": "x64"}.get(match["arch"].lower(), match["arch"].lower()) != context["arch"]:
            raise ValueError("Extension runtime filename has wrong architecture/thread: " + name)
        consumption_files = [path for path in files if "/" not in path and path.casefold() == "consumed-core.json"]
        if len(consumption_files) > 1:
            raise ValueError("Extension requires at most one consumption receipt: " + name)
        consumption = consumption_files[0] if consumption_files else None
        for path, directory in extension_entries:
            if path.startswith(group + "/"):
                relative = path[len(group) + 1:]
                if (relative != payload and relative != consumption and relative != "logs"
                        and not relative.startswith("logs/")):
                    raise ValueError("Unexpected extension artifact entry: " + relative)
                if relative == "logs" and not directory:
                    raise ValueError("Extension logs must be a directory")
        for relative in files:
            if relative == payload:
                role = "extension-runtime"
            elif relative == consumption:
                role = "extension-consumption-evidence"
            else:
                role = "extension-log"
            # Preserve the complete relative path in the receipt. A stable ordinal
            # prevents collisions between nested logs having the same basename.
            suffix = ("consumption--" if role == "extension-consumption-evidence"
                      else f"{len(assets):04d}--" if role == "extension-log" else "")
            assets.append({"role": role, "extension": name, "source_artifact": group,
                           "source_path": relative, "original_filename": Path(relative).name,
                           "filename": f"{role}--{name}--{suffix}{Path(relative).name}"})
            if role == "extension-consumption-evidence":
                evidence[name] = assets[-1]
    _namespace([(asset["filename"], False) for asset in assets])
    return assets, evidence


def _zip_members(path):
    try:
        with zipfile.ZipFile(path) as archive:
            entries, members = [], []
            infos = archive.infolist()
            for info in infos:
                if info.orig_filename != info.filename:
                    raise ValueError("Truncated ZIP filename")
                directory = info.is_dir()
                name = info.filename[:-1] if directory else info.filename
                entries.append((name, directory))
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode) if info.create_system == 3 else 0
                if (info.flag_bits & 1 or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or (kind and (kind == stat.S_IFDIR) != directory)
                        or (bool(info.external_attr & 0x10) and not directory)):
                    raise ValueError("ZIP links, special, encrypted or conflicting member types are unsupported")
            _namespace(entries)
            for info in infos:
                digest, size = hashlib.sha256(), 0
                with archive.open(info) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                        size += len(block)
                if size != info.file_size or (info.is_dir() and size):
                    raise ValueError("ZIP member size does not match its type or header")
                members.append({"path": info.filename, "type": "directory" if info.is_dir() else "file",
                                "bytes": size, "sha256": digest.hexdigest()})
            if not any(member["type"] == "file" for member in members):
                raise ValueError("ZIP has no regular payload files")
            return members
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError) as error:
        raise ValueError("Cannot validate ZIP " + path.name + ": " + str(error)) from error


def collect_split_assets(core_artifacts, extension_artifacts, selected_extensions, build_context, output_dir):
    """Freeze and inventory exact producer assets, then write split-assets.json last."""
    # Snapshot caller-owned JSON too, so a subsequent mutation cannot alter the
    # receipt independently from the identity that selected the original assets.
    context = json.loads(json.dumps(build_context))
    selected = json.loads(json.dumps(selected_extensions))
    _validate_inputs(context, selected)
    core, extensions, output = Path(core_artifacts), Path(extension_artifacts), Path(output_dir)
    if output.exists() or output.is_symlink():
        raise ValueError("Output directory must be new")
    if any(root.resolve() == output.resolve() or root.resolve() in output.resolve().parents for root in (core, extensions)):
        raise ValueError("Output directory must be outside the inputs")
    if core.resolve() == extensions.resolve() or core.resolve() in extensions.resolve().parents or extensions.resolve() in core.resolve().parents:
        raise ValueError("Core and extension artifact directories must be separate")
    inventories = (_inventory(core), _inventory(extensions))
    assets, evidence_assets = _select_assets(*inventories, selected, context)
    with tempfile.TemporaryDirectory(prefix="php-split-assets-") as temporary:
        frozen = Path(temporary)
        # Freeze every selected file before inspecting any ZIP. Later reads and
        # output copies use this immutable task-owned snapshot, never the inputs.
        for asset in assets:
            is_core = asset["role"].startswith("core-")
            root = core if is_core else extensions / asset["source_artifact"]
            key = asset["source_path"] if is_core else asset["source_artifact"] + "/" + asset["source_path"]
            expected = inventories[0 if is_core else 1][1][key]
            target = frozen / asset["filename"]
            shutil.copyfile(root / asset["source_path"], target)
            if _hash_file(target) != expected:
                raise ValueError("Input changed while freezing: " + asset["source_path"])
            asset.update(expected)
        for asset in assets:
            if asset["original_filename"].lower().endswith(".zip"):
                asset["members"] = _zip_members(frozen / asset["filename"])
                files = [member["path"] for member in asset["members"] if member["type"] == "file"]
                if asset["role"] == "core-runtime" and "php.exe" not in files:
                    raise ValueError("Original core runtime ZIP must contain top-level php.exe")
                if asset["role"] == "core-devel" and not any(Path(name).name == "php.h" for name in files):
                    raise ValueError("Original devel ZIP must contain php.h")
                if asset["role"] == "extension-runtime" and not any("/" not in name and name.lower().startswith("php_") and name.lower().endswith(".dll") for name in files):
                    raise ValueError("Original extension runtime ZIP must contain a top-level PHP DLL")
        selected_by_name = {item["name"]: item for item in selected}
        outputs_by_name = {asset["extension"]: asset for asset in assets
                           if asset["role"] == "extension-runtime"}
        runtime_input = next(asset for asset in assets if asset["role"] == "core-runtime")
        devel_input = next(asset for asset in assets if asset["role"] == "core-devel")
        runtime_binding = {"filename": runtime_input["original_filename"],
                           "bytes": runtime_input["bytes"], "sha256": runtime_input["sha256"]}
        devel_binding = {"filename": devel_input["original_filename"],
                         "bytes": devel_input["bytes"], "sha256": devel_input["sha256"]}
        validated_consumption = []
        for name, evidence in evidence_assets.items():
            raw = _json_receipt(frozen / evidence["filename"])
            output_asset = outputs_by_name[name]
            output_binding = {"filename": output_asset["original_filename"],
                              "bytes": output_asset["bytes"], "sha256": output_asset["sha256"]}
            validated = _validate_consumption_receipt(
                raw, selected_by_name[name], context, runtime_binding, devel_binding,
                output_binding)
            evidence["consumption_receipt"] = validated
            validated_consumption.append({
                "extension": name,
                "evidence_sha256": evidence["sha256"],
                "runtime_core_sha256": validated["inputs"]["runtime"]["sha256"],
                "devel_core_sha256": validated["inputs"]["devel"]["sha256"],
                "output_sha256": validated["output"]["sha256"],
            })
        if (_inventory(core), _inventory(extensions)) != inventories:
            raise ValueError("Artifact inputs changed during collection")
        missing = ["core_abi", "actual_toolchain", "crt_imports",
                   "resolved_action_commit", "extension_consumed_core_hashes", "native_module_load"]
        if selected and len(validated_consumption) == len(selected):
            missing.remove("extension_consumed_core_hashes")
        consumption_status = ("complete" if selected and len(validated_consumption) == len(selected)
                              else "partial" if validated_consumption else "unavailable")
        receipt = {
            "schema": "servbay.php-split-assets.v1", "publishable_v2": False,
            "build_context": context, "selected_extensions": selected,
            "native_evidence": {
                "status": "pending", "missing": missing,
            },
            "extension_consumption": {"status": consumption_status,
                                      "validated": validated_consumption},
            "source_archive_semantics": "core-source is the producer's pre-patch source archive, not a patched source snapshot",
            "assets": assets,
        }
        output.mkdir()
        for asset in assets:
            target = output / asset["filename"]
            shutil.copyfile(frozen / asset["filename"], target)
        for asset in assets:
            target = output / asset["filename"]
            if _hash_file(target) != {key: asset[key] for key in ("bytes", "sha256")}:
                raise ValueError("Output asset differs from frozen input: " + asset["filename"])
        with (output / "split-assets.json").open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-artifacts", required=True)
    parser.add_argument("--extension-artifacts", required=True)
    parser.add_argument("--selected-extensions", required=True, help="prepare job's selected JSON file")
    parser.add_argument("--build-context", required=True, help="explicit producer/build JSON file")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        with Path(args.selected_extensions).open(encoding="utf-8") as stream:
            selected = json.load(stream)
        with Path(args.build_context).open(encoding="utf-8") as stream:
            context = json.load(stream)
        receipt = collect_split_assets(args.core_artifacts, args.extension_artifacts, selected, context, args.output_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Asset collection failed: {error}\n")
    print(f"Collected {len(receipt['assets'])} original assets; native/ABI evidence pending")


if __name__ == "__main__":
    main()
