"""Offline producer asset collection, using real ZIP bytes and no native execution."""

import copy
import hashlib
import io
import json
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import collect_split_assets as collector


def digest(data):
    return hashlib.sha256(data).hexdigest()


def zip_bytes(entries):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, content in entries:
                archive.writestr(name, content)
    return stream.getvalue()


class CollectSplitAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.core = self.root / "core"
        self.extensions = self.root / "extensions"
        self.output = self.root / "output"
        self.core.mkdir()
        self.extensions.mkdir()
        self.context = {
            "producer": {"repository": "ServBay/PHP-Windows-Portable", "commit": "a" * 40,
                         "run_id": 123, "run_attempt": 2},
            "display_version": "8.4.27.1", "source_ref": "8.4.27",
            "build_version": "8.4.27", "build_branch": "8.4", "arch": "x64",
            "thread_safe": "nts", "core_runtime_filename": "php-8.4.27-nts-Win32-vs17-x64.zip",
            "core_devel_filename": "php-devel-pack-8.4.27-nts-Win32-vs17-x64.zip",
        }
        self.selected = [
            {"name": "redis", "url": "https://github.com/phpredis/phpredis", "ref": "6.3.0",
             "args": "--enable-redis", "libs": ""},
            {"name": "http", "url": "https://pecl.php.net/package/pecl_http", "ref": "4.3.1",
             "args": "", "libs": "zlib,curl"},
        ]
        self.runtime = self.core / self.context["core_runtime_filename"]
        self.runtime.write_bytes(zip_bytes([("php.exe", b"native-core"),
                                            ("ext/php_curl.dll", b"built-in-extension")]))
        self.devel = self.core / self.context["core_devel_filename"]
        self.devel.write_bytes(zip_bytes([("php-devel-pack/include/main/php.h", b"core-header")]))
        (self.core / "php-8.4.27-src.zip").write_bytes(zip_bytes([("main/php.h", b"pre-patch-source")]))
        for selected, package in zip(self.selected, ("redis", "pecl_http")):
            group = self.group(selected["name"])
            group.mkdir()
            filename = f"php_{package}-{selected['ref']}-8.4-nts-vs17-x86_64.zip"
            (group / filename).write_bytes(zip_bytes([
                (filename[:-4] + ".dll", selected["name"].encode()),
                (filename[:-4] + ".pdb", b"symbols"),
                ("lib-dependency.dll", b"dependency"), ("config/settings.xml", b"<config/>"),
            ]))
            (group / "logs").mkdir()
            (group / "logs" / filename).write_bytes(zip_bytes([("build.txt", b"log-not-module")]))

    def group(self, name):
        return self.extensions / f"extension-{name}-{self.context['display_version']}-{self.context['arch']}-{self.context['thread_safe']}"

    def consumption_receipt(self, name):
        selected = next(item for item in self.selected if item["name"] == name)
        group = self.group(name)
        output = next(group.glob("*.zip"))
        runtime = self.runtime.read_bytes()
        devel = self.devel.read_bytes()
        return {
            "schema": "servbay.php-extension-consumed-core.v1",
            "extension": {"name": name, "package_name": (
                "pecl_http" if name == "http" else name), "ref": selected["ref"],
                "requested_ref": selected["ref"]},
            "request": {"php_version": "8.4", "arch": "x64", "arch_canonical": "x86_64",
                        "ts": "nts", "vs_version": "vs17", "vs_toolset": "14.44.35207"},
            "inputs": {
                "runtime": {"role": "runtime", "filename": self.runtime.name,
                            "bytes": len(runtime), "sha256": digest(runtime), "source": "local"},
                "devel": {"role": "devel", "filename": self.devel.name,
                          "bytes": len(devel), "sha256": digest(devel), "source": "primary",
                          "url": "https://downloads.php.net/~windows/releases/" + self.devel.name},
            },
            "output": {"filename": output.name, "bytes": output.stat().st_size,
                       "sha256": digest(output.read_bytes())},
            "producer": copy.deepcopy(self.context["producer"]),
        }

    def write_consumption_receipt(self, name, receipt=None):
        receipt = receipt if receipt is not None else self.consumption_receipt(name)
        (self.group(name) / "consumed-core.json").write_text(json.dumps(receipt))
        return receipt

    def collect(self):
        return collector.collect_split_assets(self.core, self.extensions, self.selected, self.context, self.output)

    def assert_rejected(self, pattern=None):
        with self.assertRaises(ValueError) as caught:
            self.collect()
        if pattern:
            self.assertRegex(str(caught.exception), pattern)
        self.assertFalse((self.output / "split-assets.json").exists())

    def test_collects_exact_original_assets_members_and_requested_inputs(self):
        result = self.collect()
        self.assertEqual(result, json.loads((self.output / "split-assets.json").read_text()))
        self.assertEqual(result["schema"], "servbay.php-split-assets.v1")
        self.assertEqual(result["build_context"], self.context)
        self.assertEqual(result["selected_extensions"], self.selected)
        self.assertFalse(result["publishable_v2"])
        self.assertEqual(result["native_evidence"]["status"], "pending")
        self.assertEqual(len(result["assets"]), 7)
        self.assertEqual({p.name for p in self.output.iterdir()},
                         {a["filename"] for a in result["assets"]} | {"split-assets.json"})
        for asset in result["assets"]:
            parent = self.core if asset["source_artifact"] == "php-build-artifacts-x64-nts" else self.extensions / asset["source_artifact"]
            original = (parent / asset["source_path"]).read_bytes()
            self.assertEqual((self.output / asset["filename"]).read_bytes(), original)
            self.assertEqual(asset["sha256"], digest(original))
            self.assertEqual(asset["bytes"], len(original))
            self.assertEqual(asset["original_filename"], Path(asset["source_path"]).name)
            with zipfile.ZipFile(io.BytesIO(original)) as archive:
                expected = [{"path": info.filename, "type": "file", "bytes": info.file_size,
                             "sha256": digest(archive.read(info))} for info in archive.infolist()]
            self.assertEqual(asset["members"], expected)
        runtime = next(a for a in result["assets"] if a["role"] == "core-runtime")
        self.assertIn("ext/php_curl.dll", [m["path"] for m in runtime["members"]])
        module = next(a for a in result["assets"] if a["role"] == "extension-runtime" and a["extension"] == "http")
        self.assertTrue(module["original_filename"].startswith("php_pecl_http-"))
        self.assertTrue(any(m["path"].startswith("php_pecl_http-") for m in module["members"]))
        self.assertEqual(len([a for a in result["assets"] if a["role"] == "extension-log"]), 2)
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_ts_filename_has_no_ts_token_for_core(self):
        self.context["thread_safe"] = "ts"
        for key, path in (("core_runtime_filename", self.runtime), ("core_devel_filename", self.devel)):
            name = self.context[key].replace("-nts-Win32-", "-Win32-")
            path.rename(path.with_name(name))
            self.context[key] = name
        for old in list(self.extensions.iterdir()):
            new = old.with_name(old.name[:-3] + "ts")
            old.rename(new)
            for path in list(new.rglob("*.zip")):
                path.rename(path.with_name(path.name.replace("-nts-", "-ts-")))
        self.assertEqual(len(self.collect()["assets"]), 7)

    def test_release_tag_build_branch_is_empty(self):
        for key, path in (("core_runtime_filename", self.runtime), ("core_devel_filename", self.devel)):
            name = path.name.replace("8.4.27", "8.2.35").replace("vs17", "vs16")
            path.rename(path.with_name(name))
            self.context[key] = name
        for path in list(self.extensions.iterdir()):
            path.rename(path.with_name(path.name.replace("8.4.27.1", "8.2.35")))
        self.context.update(display_version="8.2.35", source_ref="8.2.35", build_version="8.2.35")
        self.context["build_branch"] = ""
        self.assertEqual(self.collect()["build_context"]["build_branch"], "")

    def test_core_only_collection_and_auxiliary_roles(self):
        self.selected = []
        self.extensions = self.root / "empty-extensions"
        self.extensions.mkdir()
        for name in ("php-debug-pack-8.4.27-nts-Win32-vs17-x64.zip",
                     "php-test-pack-8.4.27.zip", "php-build-notes.zip"):
            (self.core / name).write_bytes(zip_bytes([("notes.txt", name.encode())]))
        roles = {a["role"] for a in self.collect()["assets"]}
        self.assertEqual(roles, {"core-runtime", "core-devel", "core-source", "core-debug", "core-test", "core-ancillary"})

    def test_logs_are_audit_assets_never_runtime(self):
        group = self.group("redis")
        (group / "logs" / "compiler.txt").write_bytes(b"compiler output")
        result = self.collect()
        log = next(a for a in result["assets"] if a["source_path"] == "logs/compiler.txt")
        self.assertEqual(log["role"], "extension-log")
        self.assertEqual(log["sha256"], digest(b"compiler output"))
        self.assertNotIn("members", log)

    def test_valid_consumption_receipt_is_frozen_as_evidence_and_clears_only_its_own_gap(self):
        receipt = self.write_consumption_receipt("redis")
        result = self.collect()
        evidence = [asset for asset in result["assets"]
                    if asset["role"] == "extension-consumption-evidence"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["extension"], "redis")
        self.assertEqual(evidence[0]["source_path"], "consumed-core.json")
        self.assertEqual(evidence[0]["sha256"], digest(json.dumps(receipt).encode()))
        self.assertEqual((self.output / evidence[0]["filename"]).read_text(), json.dumps(receipt))
        self.assertIn("extension_consumed_core_hashes", result["native_evidence"]["missing"])
        self.assertEqual(result["extension_consumption"]["status"], "partial")
        self.assertEqual([entry["extension"] for entry in result["extension_consumption"]["validated"]],
                         ["redis"])

    def test_all_consumption_receipts_clear_only_the_consumed_core_gap(self):
        for selected in self.selected:
            self.write_consumption_receipt(selected["name"])
        result = self.collect()
        self.assertEqual(result["extension_consumption"]["status"], "complete")
        self.assertNotIn("extension_consumed_core_hashes", result["native_evidence"]["missing"])
        self.assertEqual(set(result["native_evidence"]["missing"]), {
            "core_abi", "actual_toolchain", "crt_imports", "resolved_action_commit",
            "native_module_load"})
        self.assertFalse(result["publishable_v2"])

    def test_pull_request_ref_keeps_request_identity_separate_from_normalized_output(self):
        selected = self.selected[0]
        selected["ref"] = "refs/pull/123/merge"
        path = next(self.group("redis").glob("*.zip"))
        renamed = path.with_name(path.name.replace("6.3.0", "123"))
        path.rename(renamed)
        receipt = self.consumption_receipt("redis")
        receipt["extension"]["ref"] = "123"
        self.write_consumption_receipt("redis", receipt)
        result = self.collect()
        evidence = next(asset for asset in result["assets"]
                        if asset["role"] == "extension-consumption-evidence")
        self.assertEqual(evidence["consumption_receipt"]["extension"], {
            "name": "redis", "package_name": "redis", "ref": "123",
            "requested_ref": "refs/pull/123/merge"})

    def test_consumption_receipt_field_mismatches_are_rejected(self):
        mutations = {
            "runtime-sha": lambda value: value["inputs"]["runtime"].update(sha256="0" * 64),
            "devel-bytes": lambda value: value["inputs"]["devel"].update(bytes=0),
            "output-sha": lambda value: value["output"].update(sha256="f" * 64),
            "output-name": lambda value: value["output"].update(filename="php_other.zip"),
            "extension": lambda value: value["extension"].update(name="other"),
            "ref": lambda value: value["extension"].update(ref="other"),
            "requested-ref": lambda value: value["extension"].update(requested_ref="other"),
            "package-name": lambda value: value["extension"].update(package_name="other"),
            "arch": lambda value: value["request"].update(arch="x86"),
            "thread": lambda value: value["request"].update(ts="ts"),
            "toolset": lambda value: value["request"].update(vs_version="vs16"),
            "run": lambda value: value["producer"].update(run_attempt=9),
            "role": lambda value: value["inputs"]["runtime"].update(role="devel"),
            "local-url": lambda value: value["inputs"]["runtime"].update(
                url="https://downloads.php.net/~windows/releases/" + self.runtime.name),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                value = self.consumption_receipt("redis")
                mutate(value)
                self.write_consumption_receipt("redis", value)
                self.assert_rejected()

    def test_consumption_receipt_json_is_strict(self):
        path = self.group("redis") / "consumed-core.json"
        valid = self.consumption_receipt("redis")
        encoded = json.dumps(valid)
        schema_field = '"schema": "servbay.php-extension-consumed-core.v1"'
        self.assertEqual(encoded.count(schema_field), 1)
        path.write_text(encoded.replace(schema_field, schema_field + ',' + schema_field))
        self.assert_rejected()
        wrong_schema = copy.deepcopy(valid)
        wrong_schema["schema"] = "other"
        path.write_text(json.dumps(wrong_schema))
        self.assert_rejected()
        path.write_text('{"schema":"x"')
        self.assert_rejected()
        path.write_text(json.dumps(dict(valid, unexpected=True)))
        self.assert_rejected()

    def test_unknown_extension_top_level_file_is_still_rejected(self):
        (self.group("redis") / "notes.txt").write_text("unexpected")
        self.assert_rejected()

    def test_consumption_evidence_does_not_expose_the_input_root(self):
        self.write_consumption_receipt("redis")
        result = self.collect()
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_missing_runtime(self):
        self.runtime.rename(self.root / "held.zip")
        self.assert_rejected()

    def test_missing_devel(self):
        self.devel.rename(self.root / "held.zip")
        self.assert_rejected()

    def test_missing_selected_module(self):
        self.group("redis").rename(self.root / "held")
        self.assert_rejected()

    def test_extra_module_group(self):
        (self.extensions / "extension-unknown-8.4.27.1-x64-nts").mkdir()
        self.assert_rejected()

    def test_duplicate_core_candidate(self):
        (self.core / self.runtime.name.replace("8.4.27", "8.4.28")).write_bytes(self.runtime.read_bytes())
        self.assert_rejected()

    def test_duplicate_devel_candidate(self):
        (self.core / self.devel.name.replace("8.4.27", "8.4.28")).write_bytes(self.devel.read_bytes())
        self.assert_rejected()

    def test_multiple_module_payloads(self):
        (self.group("redis") / "extra.zip").write_bytes(zip_bytes([("php_extra.dll", b"extra")]))
        self.assert_rejected()

    def test_module_logs_cannot_substitute_missing_payload(self):
        next(self.group("redis").glob("*.zip")).rename(self.root / "held.zip")
        self.assert_rejected()

    def test_wrong_declared_core_role(self):
        self.context["core_runtime_filename"] = self.context["core_devel_filename"]
        self.assert_rejected()

    def test_core_arch_and_thread_must_match_context(self):
        for old, new in (("x64", "x86"), ("-nts-Win32", "-Win32")):
            with self.subTest(new=new):
                self.output = self.root / ("output-" + new)
                name = self.runtime.name.replace(old, new)
                target = self.runtime.with_name(name)
                self.runtime.rename(target)
                self.context["core_runtime_filename"] = name
                try:
                    self.assert_rejected()
                finally:
                    target.rename(self.runtime)
                    self.context["core_runtime_filename"] = self.runtime.name

    def test_core_pair_must_describe_same_build(self):
        target = self.devel.with_name(self.devel.name.replace("vs17", "vs18"))
        self.devel.rename(target)
        self.context["core_devel_filename"] = target.name
        self.assert_rejected()

    def test_module_arch_and_thread_must_match_context(self):
        path = next(self.group("redis").glob("*.zip"))
        for old, new in (("x86_64", "x86"), ("-nts-", "-ts-")):
            with self.subTest(new=new):
                self.output = self.root / ("output-" + new)
                target = path.with_name(path.name.replace(old, new))
                path.rename(target)
                try:
                    self.assert_rejected()
                finally:
                    target.rename(path)

    def test_nested_bundle_cannot_impersonate_core_runtime(self):
        self.runtime.write_bytes(zip_bytes([("artifacts/" + self.runtime.name, b"nested-runtime")]))
        self.assert_rejected()

    def test_runtime_member_must_be_a_file(self):
        self.runtime.write_bytes(zip_bytes([("php.exe/", b"")]))
        self.assert_rejected()

    def test_zip_namespace_and_member_types(self):
        fixtures = {
            "traversal": [("../php.exe", b"a")], "absolute": [("/php.exe", b"a")],
            "drive": [("C:/php.exe", b"a")], "backslash": [("ext\\php.dll", b"a")],
            "case": [("ext/php.dll", b"a"), ("EXT/php.dll", b"b")],
            "duplicate": [("php.exe", b"a"), ("php.exe", b"b")],
            "file-parent": [("ext", b"a"), ("ext/php.dll", b"b")],
            "directory-file": [("ext/", b""), ("ext", b"a")],
            "device": [("CON.dll", b"a")], "trailing-space": [("foo ", b"a")],
            "ads": [("foo:bar", b"a")], "empty-part": [("ext//php.dll", b"a")],
        }
        for label, entries in fixtures.items():
            with self.subTest(label=label):
                self.output = self.root / ("output-" + label)
                content = entries if label == "duplicate" else [("php.exe", b"valid-core")] + entries
                self.runtime.write_bytes(zip_bytes(content))
                self.assert_rejected()
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o600, stat.S_IFCHR | 0o600):
            with self.subTest(mode=mode):
                self.output = self.root / ("output-" + str(mode))
                info = zipfile.ZipInfo("php.exe")
                info.create_system = 3
                info.external_attr = mode << 16
                self.runtime.write_bytes(zip_bytes([(info, b"target")]))
                self.assert_rejected()

    def test_member_namespace_checks_apply_to_every_zip_role(self):
        paths = [self.devel, self.core / "php-8.4.27-src.zip",
                 next(self.group("redis").glob("*.zip")), next((self.group("http") / "logs").glob("*.zip"))]
        for index, path in enumerate(paths):
            with self.subTest(path=path.name):
                self.output = self.root / ("output-" + str(index))
                original = path.read_bytes()
                with zipfile.ZipFile(io.BytesIO(original)) as archive:
                    entries = [(info.filename, archive.read(info)) for info in archive.infolist()]
                path.write_bytes(zip_bytes(entries + [("../unsafe.txt", b"unsafe")]))
                try:
                    self.assert_rejected()
                finally:
                    path.write_bytes(original)

    def test_same_module_zip_basename_does_not_collide(self):
        redis_path = next(self.group("redis").glob("*.zip"))
        http_path = next(self.group("http").glob("*.zip"))
        http_path.rename(http_path.with_name(redis_path.name))
        result = self.collect()
        modules = [a for a in result["assets"] if a["role"] == "extension-runtime"]
        self.assertEqual(modules[0]["original_filename"], modules[1]["original_filename"])
        self.assertNotEqual(modules[0]["filename"], modules[1]["filename"])
        self.assertNotEqual(modules[0]["sha256"], modules[1]["sha256"])

    def test_output_asset_corruption_prevents_receipt(self):
        original = collector.shutil.copyfile
        def corrupt_output(source, target, *args, **kwargs):
            value = original(source, target, *args, **kwargs)
            if Path(target).parent == self.output:
                Path(target).write_bytes(b"corrupt output")
            return value
        with mock.patch.object(collector.shutil, "copyfile", side_effect=corrupt_output):
            self.assert_rejected()

    def test_corrupt_crc_rejected_in_every_zip_role(self):
        paths = [self.runtime, self.devel, self.core / "php-8.4.27-src.zip",
                 next(self.group("redis").glob("*.zip")), next((self.group("http") / "logs").glob("*.zip"))]
        for index, path in enumerate(paths):
            with self.subTest(path=path.name):
                self.output = self.root / ("output-" + str(index))
                original = path.read_bytes()
                damaged = bytearray(original)
                offset = 30 + struct.unpack_from("<H", damaged, 26)[0] + struct.unpack_from("<H", damaged, 28)[0]
                damaged[offset] ^= 0x01
                path.write_bytes(damaged)
                try:
                    self.assert_rejected()
                finally:
                    path.write_bytes(original)

    def test_encrypted_flag_is_rejected(self):
        damaged = bytearray(self.runtime.read_bytes())
        for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            offset = 0
            while (offset := damaged.find(signature, offset)) >= 0:
                damaged[offset + flag_offset] |= 1
                offset += 4
        self.runtime.write_bytes(damaged)
        self.assert_rejected()

    def test_safe_unicode_and_explicit_directories_are_preserved(self):
        self.runtime.write_bytes(zip_bytes([("php.exe", b"core"), ("说明/", b""), ("说明/使用.txt", b"readme")]))
        runtime = next(a for a in self.collect()["assets"] if a["role"] == "core-runtime")
        self.assertIn({"path": "说明/", "type": "directory", "bytes": 0, "sha256": digest(b"")}, runtime["members"])

    def test_input_symlink_is_rejected(self):
        moved = self.root / "held.zip"
        self.runtime.rename(moved)
        self.runtime.symlink_to(moved)
        self.assert_rejected()

    def test_unknown_nested_core_payload_is_rejected(self):
        (self.core / "unexpected").mkdir()
        (self.core / "unexpected" / "hidden.zip").write_bytes(zip_bytes([("hidden", b"x")]))
        self.assert_rejected()

    def test_input_changed_during_validation_never_gets_receipt(self):
        original = zipfile.ZipFile
        changed = False
        def mutate_then_open(*args, **kwargs):
            nonlocal changed
            if not changed:
                changed = True
                self.runtime.write_bytes(zip_bytes([("php.exe", b"mutated-after-freeze")]))
            return original(*args, **kwargs)
        with mock.patch.object(collector.zipfile, "ZipFile", side_effect=mutate_then_open):
            self.assert_rejected()

    def test_existing_output_is_never_changed(self):
        self.output.mkdir()
        sentinel = self.output / "keep"
        sentinel.write_bytes(b"existing")
        self.assert_rejected()
        self.assertEqual(sentinel.read_bytes(), b"existing")

    def test_output_inside_inputs_is_rejected(self):
        self.output = self.core / "output"
        self.assert_rejected()

    def test_invalid_or_secret_context_is_rejected(self):
        original = copy.deepcopy(self.context)
        for patch in ({"arch": "arm64"}, {"thread_safe": True}, {"token": "secret"},
                      {"producer": dict(original["producer"], commit="main")},
                      {"producer": dict(original["producer"], run_id=0)}):
            with self.subTest(patch=patch):
                self.context = dict(original, **patch)
                self.assert_rejected()

    def test_invalid_selected_extensions_are_rejected(self):
        original = copy.deepcopy(self.selected)
        for patch in ({"args": []}, {"libs": []}, {"url": "https://secret@github.com/a/b"},
                      {"url": "https://github.com/a/b?token=secret"}, {"name": "../redis"}):
            with self.subTest(patch=patch):
                self.selected = [dict(original[0], **patch), original[1]]
                self.assert_rejected()
        self.selected = [original[0], original[0]]
        self.assert_rejected()

    def test_cli_produces_same_public_index(self):
        context = self.root / "context.json"
        selected = self.root / "selected.json"
        context.write_text(json.dumps(self.context))
        selected.write_text(json.dumps(self.selected))
        result = subprocess.run([sys.executable, str(Path(collector.__file__)),
                                 "--core-artifacts", str(self.core), "--extension-artifacts", str(self.extensions),
                                 "--selected-extensions", str(selected), "--build-context", str(context),
                                 "--output-dir", str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads((self.output / "split-assets.json").read_text())["assets"]), 7)


if __name__ == "__main__":
    unittest.main()
