"""Release wiring and offline helper behavior using real producer-shaped ZIPs."""

import copy
import hashlib
import json
import os
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_collect_split_assets as fixtures


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/prepare_split_release.py"
CONTEXT_ENV = "SPLIT_BUILD_CONTEXT_JSON"
SELECTED_ENV = "SPLIT_SELECTED_EXTENSIONS_JSON"


class PrepareSplitReleaseTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.CollectSplitAssetsTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root, self.core, self.extensions, self.output = (
            fixture.root, fixture.core, fixture.extensions, fixture.output)
        self.context = {key: value for key, value in fixture.context.items()
                        if key not in ("core_runtime_filename", "core_devel_filename")}
        self.context["build_branch"] = ""
        self.selected = copy.deepcopy(fixture.selected)
        self.github_output = self.root / "github-output"
        self.github_output.write_text("existing=keep\n")

    def run_helper(self, extra_env=None, output=None):
        environment = dict(os.environ, **{
            CONTEXT_ENV: json.dumps(self.context), SELECTED_ENV: json.dumps(self.selected),
            "GITHUB_OUTPUT": str(self.github_output), "PYTHONDONTWRITEBYTECODE": "1",
        })
        environment.update(extra_env or {})
        return subprocess.run([sys.executable, str(HELPER), "--core-artifacts", str(self.core),
                               "--extension-artifacts", str(self.extensions),
                               "--output-dir", str(output or self.output)],
                              env=environment, capture_output=True, text=True)

    def assert_rejected(self, extra_env=None, output=None):
        result = self.run_helper(extra_env, output)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.github_output.read_text(), "existing=keep\n")
        return result

    def files_output(self):
        lines = self.github_output.read_text().splitlines()
        self.assertEqual(lines[0], "existing=keep")
        self.assertTrue(lines[1].startswith("files<<"))
        delimiter = lines[1].split("<<", 1)[1]
        self.assertEqual(lines[-1], delimiter)
        self.assertNotIn(delimiter, lines[2:-1])
        return lines[2:-1]

    def test_real_assets_index_hashes_and_exact_release_files(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        index = self.output / "split-assets.json"
        receipt = json.loads(index.read_text())
        expected_context = dict(self.context, **{
            "core_runtime_filename": self.fixture.runtime.name,
            "core_devel_filename": self.fixture.devel.name,
        })
        self.assertEqual(receipt["build_context"], expected_context)
        self.assertEqual(receipt["selected_extensions"], self.selected)
        self.assertFalse(receipt["publishable_v2"])
        self.assertEqual(len(receipt["assets"]), 7)
        self.assertEqual(self.files_output(), [str(index)] + [str(self.output / asset["filename"])
                                                            for asset in receipt["assets"]])
        self.assertEqual({path.name for path in self.output.iterdir()},
                         {"split-assets.json"} | {asset["filename"] for asset in receipt["assets"]})
        for asset in receipt["assets"]:
            source_root = self.core if asset["role"].startswith("core-") else self.extensions / asset["source_artifact"]
            original = (source_root / asset["source_path"]).read_bytes()
            self.assertEqual((self.output / asset["filename"]).read_bytes(), original)
            self.assertEqual(asset["bytes"], len(original))
            self.assertEqual(asset["sha256"], hashlib.sha256(original).hexdigest())
        http = [asset for asset in receipt["assets"] if asset.get("extension") == "http"]
        self.assertEqual({asset["role"] for asset in http}, {"extension-runtime", "extension-log"})
        self.assertTrue(all("pecl_http" in asset["original_filename"] for asset in http))
        self.assertEqual(http[0]["original_filename"], http[1]["original_filename"])
        self.assertNotEqual(http[0]["sha256"], http[1]["sha256"])

    def test_actions_null_optional_build_branch_uses_empty_release_default(self):
        self.context["build_branch"] = None
        self.context["producer"].update(run_id="123", run_attempt="2")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.output / "split-assets.json").read_text())
        self.assertEqual(receipt["build_context"]["build_branch"], "")
        self.assertEqual(len(receipt["assets"]), 7)
        self.assertEqual(self.files_output(), [str(self.output / "split-assets.json")] +
                         [str(self.output / asset["filename"]) for asset in receipt["assets"]])
        for asset in receipt["assets"]:
            original_root = (self.core if asset["role"].startswith("core-")
                             else self.extensions / asset["source_artifact"])
            original = (original_root / asset["source_path"]).read_bytes()
            self.assertEqual((self.output / asset["filename"]).read_bytes(), original)
            self.assertEqual(asset["sha256"], hashlib.sha256(original).hexdigest())

    def test_explicit_empty_and_development_master_branch_are_preserved(self):
        for branch in ("", "master", "8.4"):
            with self.subTest(branch=branch):
                self.context["build_branch"] = branch
                self.github_output.write_text("existing=keep\n")
                output = self.root / ("branch-" + (branch or "empty"))
                result = self.run_helper(output=output)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads((output / "split-assets.json").read_text())
                self.assertEqual(receipt["build_context"]["build_branch"], branch)

    def test_invalid_non_null_branch_is_not_defaulted(self):
        for branch in (False, 0, [], {}, " ", "master\n"):
            with self.subTest(branch=branch):
                self.assert_rejected({CONTEXT_ENV: json.dumps(dict(self.context, build_branch=branch))})

    def test_required_context_fields_and_missing_branch_stay_required(self):
        for key in self.context:
            with self.subTest(missing=key):
                context = dict(self.context)
                del context[key]
                self.assert_rejected({CONTEXT_ENV: json.dumps(context)})
            if key != "build_branch":
                with self.subTest(null=key):
                    self.assert_rejected({CONTEXT_ENV: json.dumps(dict(self.context, **{key: None}))})

    def test_github_decimal_run_strings_are_recorded_as_positive_integers(self):
        self.context["producer"].update(run_id="123", run_attempt="2")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        producer = json.loads((self.output / "split-assets.json").read_text())["build_context"]["producer"]
        self.assertEqual(producer["run_id"], 123)
        self.assertEqual(producer["run_attempt"], 2)
        self.assertIs(type(producer["run_id"]), int)
        self.assertIs(type(producer["run_attempt"]), int)

    def test_wrong_run_identity_types_are_rejected_without_defaults(self):
        for value in (True, 1.5, "one", "", None, 0):
            with self.subTest(value=value):
                context = copy.deepcopy(self.context)
                context["producer"]["run_id"] = value
                self.assert_rejected({CONTEXT_ENV: json.dumps(context)})

    def test_ts_and_x86_identity_comes_from_actual_original_names(self):
        for path in self.core.glob("*.zip"):
            path.rename(path.with_name(path.name.replace("-nts-", "-").replace("vs17", "vc15").replace("x64", "x86")))
        for group in list(self.extensions.iterdir()):
            for path in list(group.rglob("*.zip")):
                path.rename(path.with_name(path.name.replace("-nts-", "-ts-").replace("vs17", "vc15").replace("x86_64", "x86")))
            group.rename(group.with_name(group.name.replace("x64-nts", "x86-ts")))
        self.context.update(arch="x86", thread_safe="ts")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads((self.output / "split-assets.json").read_text())["build_context"]
        self.assertEqual(context["core_runtime_filename"], "php-8.4.27-Win32-vc15-x86.zip")
        self.assertEqual(context["core_devel_filename"], "php-devel-pack-8.4.27-Win32-vc15-x86.zip")

    def test_workflow_command_runs_from_separate_checkout_and_preserves_merged_files(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/build.yml").read_text())
        step = next(step for step in workflow["jobs"]["create-release"]["steps"] if step.get("id") == "split-assets")
        (self.root / "producer-source").symlink_to(ROOT, target_is_directory=True)
        inputs = self.root / "split-inputs"
        inputs.mkdir()
        self.core.rename(inputs / "core")
        self.extensions.rename(inputs / "extensions")
        merged = self.root / "release-assets"
        merged.mkdir()
        # The split step must not alter any of the original v1 Release assets.
        original_assets = {"php-8.4.27.1-windows-x64" + suffix: ("original" + suffix).encode()
                           for suffix in (".zip", ".zip.sha256", ".7z", ".7z.sha256")}
        for name, content in original_assets.items():
            (merged / name).write_bytes(content)
        self.context["build_branch"] = None  # Actual Actions context for stable/testing.
        environment = dict(os.environ, **{CONTEXT_ENV: json.dumps(self.context),
            SELECTED_ENV: json.dumps(self.selected), "GITHUB_OUTPUT": str(self.github_output)})
        command = shlex.split(step["run"])
        result = subprocess.run([sys.executable] + command[1:], cwd=self.root,
                                env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path.name: path.read_bytes() for path in merged.iterdir()}, original_assets)
        receipt = json.loads((self.root / "split-release-assets/split-assets.json").read_text())
        self.assertEqual(len(receipt["assets"]), 7)
        self.assertEqual(self.files_output(), ["split-release-assets/split-assets.json"] +
                         ["split-release-assets/" + asset["filename"] for asset in receipt["assets"]])

    def test_custom_extension_without_libs_matches_existing_action_empty_default(self):
        self.selected[0].pop("libs")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = json.loads((self.output / "split-assets.json").read_text())["selected_extensions"]
        self.assertEqual(selected, [dict(self.selected[0], libs=""), self.selected[1]])

    def test_custom_extension_without_args_matches_existing_action_empty_default(self):
        self.selected[1].pop("args")
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        selected = json.loads((self.output / "split-assets.json").read_text())["selected_extensions"]
        self.assertEqual(selected, [self.selected[0], dict(self.selected[1], args="")])

    def test_missing_core_runtime_is_rejected(self):
        self.fixture.runtime.rename(self.root / "held.zip")
        self.assert_rejected()

    def test_missing_devel_is_rejected(self):
        self.fixture.devel.rename(self.root / "held.zip")
        self.assert_rejected()

    def test_duplicate_runtime_identity_is_rejected(self):
        (self.core / self.fixture.runtime.name.replace("vs17", "vs18")).write_bytes(self.fixture.runtime.read_bytes())
        self.assert_rejected()

    def test_duplicate_devel_identity_is_rejected(self):
        (self.core / self.fixture.devel.name.replace("vs17", "vs18")).write_bytes(self.fixture.devel.read_bytes())
        self.assert_rejected()

    def test_wrong_architecture_or_thread_is_rejected(self):
        for patch in ({"arch": "x86"}, {"thread_safe": "ts"}):
            with self.subTest(patch=patch):
                self.assert_rejected({CONTEXT_ENV: json.dumps(dict(self.context, **patch))})

    def test_missing_selected_module_is_rejected(self):
        self.fixture.group("http").rename(self.root / "held-module")
        self.assert_rejected()

    def test_invalid_context_json_schema_and_unknown_fields_are_rejected(self):
        for value in ("{", "[]", json.dumps(dict(self.context, secret="private")),
                      json.dumps(dict(self.context, producer={"repository": "local"})),
                      json.dumps(dict(self.context, core_runtime_filename=self.fixture.runtime.name))):
            with self.subTest(value=value):
                self.assert_rejected({CONTEXT_ENV: value})

    def test_invalid_selected_json_schema_and_args_libs_are_rejected(self):
        for value in ("{", "{}", json.dumps([dict(self.selected[0], args=[])]),
                      json.dumps([dict(self.selected[0], libs=[])])):
            with self.subTest(value=value):
                self.assert_rejected({SELECTED_ENV: value})

    def test_corrupt_zip_is_rejected_before_success_output(self):
        self.fixture.runtime.write_bytes(b"not a ZIP")
        self.assert_rejected()

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        (self.output / "sentinel").write_bytes(b"keep")
        self.assert_rejected()
        self.assertEqual((self.output / "sentinel").read_bytes(), b"keep")

    def test_release_glob_metacharacters_in_output_path_are_rejected(self):
        self.assert_rejected(output=self.root / "release[1]")

    def test_release_glob_metacharacters_in_asset_are_rejected(self):
        log = self.fixture.group("http") / "logs" / "build[1].log"
        log.write_bytes(b"log")
        self.assert_rejected()

    def test_release_comma_in_real_log_is_rejected_without_success_output(self):
        log = self.fixture.group("http") / "logs" / "build,1.log"
        log.write_bytes(b"real-build-log")
        self.assert_rejected()
        receipt = json.loads((self.output / "split-assets.json").read_text())
        asset = next(asset for asset in receipt["assets"]
                     if asset.get("extension") == "http" and asset["source_path"] == "logs/build,1.log")
        self.assertEqual(asset["role"], "extension-log")
        self.assertEqual((self.output / asset["filename"]).read_bytes(), b"real-build-log")

    def test_receipt_mismatch_or_unindexed_file_does_not_emit_success(self):
        from scripts import prepare_split_release as helper
        original = helper.collector.collect_split_assets
        for kind in ("index", "extra"):
            with self.subTest(kind=kind):
                output = self.root / kind
                def alter(*args, **kwargs):
                    receipt = original(*args, **kwargs)
                    if kind == "index":
                        (output / "split-assets.json").write_text("{}")
                    else:
                        (output / "future.txt").write_text("unlisted")
                    return receipt
                environment = {CONTEXT_ENV: json.dumps(self.context),
                               SELECTED_ENV: json.dumps(self.selected), "GITHUB_OUTPUT": str(self.github_output)}
                with mock.patch.dict(os.environ, environment), mock.patch.object(helper.collector, "collect_split_assets", side_effect=alter):
                    with self.assertRaises(ValueError):
                        helper.prepare_split_release(self.core, self.extensions, output)
                self.assertEqual(self.github_output.read_text(), "existing=keep\n")


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load((ROOT / ".github/workflows/build.yml").read_text())
        self.release = self.workflow["jobs"]["create-release"]
        self.steps = self.release["steps"]

    def test_prepare_modes_keep_release_empty_branch_and_development_master(self):
        prepare = self.workflow["jobs"]["prepare"]
        self.assertEqual(prepare["outputs"]["build-branch"], "${{ steps.version.outputs.build-branch }}")
        step = next(step for step in prepare["steps"] if step.get("id") == "version")
        for mode, branch in (("stable", ""), ("testing", ""), ("development", "master")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                values = {"version_type": mode, "stable_version": "8.4.27", "testing_tag": "php-8.6.0RC5",
                          "dev_commit": "", "dev_version": "8.6.0-dev-latest", "thread_safe": "nts", "arch": "x64"}
                script = step["run"]
                for key, value in values.items():
                    script = script.replace("${{ github.event.inputs." + key + " }}", value)
                self.assertNotIn("${{", script)
                output = Path(directory) / "github-output"
                result = subprocess.run(["/bin/bash", "-e", "-c", script], capture_output=True, text=True,
                                        env=dict(os.environ, GITHUB_OUTPUT=str(output)))
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = dict(line.split("=", 1) for line in output.read_text().splitlines())
                self.assertEqual(actual["build-branch"], branch)
                self.assertEqual(actual["build-version"], {"stable": "8.4.27", "testing": "8.6.0RC5",
                                                          "development": "master"}[mode])

    def test_existing_release_contract_and_original_merged_files_are_preserved(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "write"})
        self.assertEqual(self.release["needs"], ["prepare", "build-php", "build-extensions", "package-php-complete"])
        self.assertEqual(self.release["if"], "github.event.inputs.create_release == 'true' &&\nalways() &&\n!cancelled() &&\nneeds.build-php.result == 'success'\n")
        self.assertEqual(self.steps[0]["uses"], "actions/download-artifact@v4")
        self.assertEqual(self.steps[0]["with"], {"name": "php-${{ needs.prepare.outputs.php-version }}-windows-${{ github.event.inputs.arch }}", "path": "release-assets"})
        release = next(step for step in self.steps if step.get("uses") == "softprops/action-gh-release@v1")
        base = "release-assets/php-${{ needs.prepare.outputs.php-version }}-windows-${{ github.event.inputs.arch }}"
        self.assertEqual(release["with"]["files"].splitlines(), [base + suffix for suffix in (".zip", ".zip.sha256", ".7z", ".7z.sha256")] + ["${{ steps.split-assets.outputs.files }}"])
        self.assertEqual(release["with"]["tag_name"], "php-${{ needs.prepare.outputs.php-version }}-${{ github.event.inputs.arch }}-${{ github.event.inputs.thread_safe }}")
        self.assertEqual(release["env"], {"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"})

    def test_split_download_identity_checkout_python_and_safe_context_wiring(self):
        checkout = next(step for step in self.steps if step.get("uses") == "actions/checkout@v4")
        self.assertEqual(checkout["with"]["ref"], "${{ github.sha }}")
        self.assertEqual(checkout["with"]["path"], "producer-source")
        checkout_path = Path(checkout["with"]["path"])
        for step in self.steps:
            if step.get("uses") == "actions/download-artifact@v4":
                download_path = Path(step["with"]["path"])
                self.assertNotEqual(checkout_path, download_path)
                self.assertNotIn(checkout_path, download_path.parents)
                self.assertNotIn(download_path, checkout_path.parents)
        python = next(step for step in self.steps if step.get("uses") == "actions/setup-python@v5")
        self.assertEqual(python["with"]["python-version"], "3.13")
        downloads = [step["with"] for step in self.steps if step.get("uses") == "actions/download-artifact@v4"]
        self.assertEqual(downloads[1], {"name": "php-build-artifacts-${{ github.event.inputs.arch }}-${{ github.event.inputs.thread_safe }}", "path": "split-inputs/core"})
        self.assertEqual(downloads[2], {"pattern": "extension-*-${{ needs.prepare.outputs.php-version }}-${{ github.event.inputs.arch }}-${{ github.event.inputs.thread_safe }}", "path": "split-inputs/extensions", "merge-multiple": False})
        prepare = next(step for step in self.steps if step.get("id") == "split-assets")
        self.assertEqual(prepare["run"].split(), ["python", "producer-source/scripts/prepare_split_release.py", "--core-artifacts", "split-inputs/core", "--extension-artifacts", "split-inputs/extensions", "--output-dir", "split-release-assets"])
        self.assertEqual(prepare["env"][SELECTED_ENV], "${{ needs.prepare.outputs.extensions-json }}")
        expression_values = {
            "github.repository": "ServBay/PHP-Windows-Portable", "github.sha": "a" * 40,
            "github.run_id": "123", "github.run_attempt": "2",
            "needs.prepare.outputs.php-version": "8.4.27.1", "needs.prepare.outputs.source-ref": "8.4.27",
            "needs.prepare.outputs.build-version": "8.4.27", "needs.prepare.outputs.build-branch": "",
            "github.event.inputs.arch": "x64", "github.event.inputs.thread_safe": "nts",
        }
        encoded = prepare["env"][CONTEXT_ENV]
        for expression, value in expression_values.items():
            encoded = encoded.replace("${{ toJSON(" + expression + ") }}", json.dumps(value))
        self.assertEqual(json.loads(encoded), {
            "producer": {"repository": "ServBay/PHP-Windows-Portable", "commit": "a" * 40, "run_id": "123", "run_attempt": "2"},
            "display_version": "8.4.27.1", "source_ref": "8.4.27", "build_version": "8.4.27", "build_branch": "", "arch": "x64", "thread_safe": "nts",
        })
        self.assertLess(self.steps.index(checkout), self.steps.index(prepare))
        self.assertLess(self.steps.index(python), self.steps.index(prepare))
        self.assertLess(self.steps.index(prepare), next(i for i, step in enumerate(self.steps) if step.get("uses") == "softprops/action-gh-release@v1"))


if __name__ == "__main__":
    unittest.main()
