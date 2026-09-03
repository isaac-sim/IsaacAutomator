#!/usr/bin/env python3

import contextlib
import io
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import click

from src.python.config import c as config
from src.python.deploy_command import DeployCommand


class Test_DeploymentNameCallback(unittest.TestCase):
    def test_valid_names(self):
        for name in ["a", "abc", "abc-123", "0", "x" * 32]:
            self.assertEqual(DeployCommand.deployment_name_callback(None, None, name), name)

    def test_uppercase_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "ABC")

    def test_underscore_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "abc_def")

    def test_empty_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "")

    def test_too_long_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.deployment_name_callback(None, None, "x" * 33)


class Test_IngressCidrsCallback(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(DeployCommand.ingress_cidrs_callback(None, None, None))

    def test_empty_returns_empty(self):
        self.assertEqual(DeployCommand.ingress_cidrs_callback(None, None, ""), "")

    def test_special_values(self):
        for value in ["auto", "myip", "myip/8", "myip/16", "myip/24", "mynet", "nvidia"]:
            self.assertEqual(
                DeployCommand.ingress_cidrs_callback(None, None, value),
                value,
            )

    def test_valid_cidr(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "10.0.0.0/16"),
            "10.0.0.0/16",
        )

    def test_multiple_values(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "myip, 10.0.0.0/8"),
            "myip,10.0.0.0/8",
        )

    def test_invalid_cidr_rejected(self):
        with self.assertRaises(click.BadParameter):
            DeployCommand.ingress_cidrs_callback(None, None, "not-a-cidr")

    def test_case_normalized(self):
        self.assertEqual(
            DeployCommand.ingress_cidrs_callback(None, None, "MyIP"),
            "myip",
        )


class Test_GitRefCallback(unittest.TestCase):
    """Tests for DeployCommand.git_ref_callback (NVBugs 6380502)."""

    @staticmethod
    def _param(name="isaacsim"):
        return SimpleNamespace(name=name)

    def _call(self, value, name="isaacsim"):
        return DeployCommand.git_ref_callback(None, self._param(name), value)

    def test_skip_values_never_touch_network(self):
        # 'no'/empty/None mean "don't install" - returned unchanged, no ls-remote
        for value in [None, "", "no", "No", " no ", "NO"]:
            with mock.patch.object(subprocess, "run") as run:
                self.assertEqual(self._call(value), value)
                run.assert_not_called()

    def test_commit_sha_accepted_without_network(self):
        # a raw sha cannot be matched by ls-remote, so it is accepted as-is
        for sha in ["045ca8b", "045ca8b59622b99a408092124377c66346e8d9c2"]:
            with mock.patch.object(subprocess, "run") as run:
                self.assertEqual(self._call(sha), sha)
                run.assert_not_called()

    def test_existing_ref_passes(self):
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="abc123\trefs/tags/v6.0.1\n"),
        ):
            self.assertEqual(self._call("v6.0.1"), "v6.0.1")

    def test_missing_ref_rejected(self):
        with mock.patch.object(subprocess, "run", return_value=SimpleNamespace(stdout="")):
            with self.assertRaises(click.BadParameter):
                self._call("v6.0.1.0")

    def test_isaacsim_message_hints_three_part_tag(self):
        with mock.patch.object(subprocess, "run", return_value=SimpleNamespace(stdout="")):
            with self.assertRaises(click.BadParameter) as cm:
                self._call("v6.0.1.0", name="isaacsim")
        self.assertIn("v6.0.1", str(cm.exception))

    def test_network_error_warns_but_does_not_block(self):
        for err in [OSError("git missing"), subprocess.TimeoutExpired("git", 30)]:
            with mock.patch.object(subprocess, "run", side_effect=err):
                self.assertEqual(self._call("v6.0.1"), "v6.0.1")

    def test_repo_selected_per_param_name(self):
        cases = {
            "isaacsim": config["isaacsim_git_repo"],
            "isaaclab": config["isaaclab_git_repo"],
            "isaaclab_arena": config["isaaclab_arena_git_repo"],
        }
        for name, repo in cases.items():
            with mock.patch.object(
                subprocess, "run",
                return_value=SimpleNamespace(stdout="hit\n"),
            ) as run:
                self._call("some-ref", name=name)
                # repo url is the 4th element of the git ls-remote argv
                self.assertIn(repo, run.call_args.args[0])

    def test_unknown_param_name_passes_through(self):
        with mock.patch.object(subprocess, "run") as run:
            self.assertEqual(self._call("whatever", name="other"), "whatever")
            run.assert_not_called()

    def test_debug_traces_the_check_to_stderr(self):
        ctx = SimpleNamespace(params={"debug": True}, meta={}, command=None)
        buf = io.StringIO()
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="abc\trefs/tags/v6.0.1\n", stderr=""),
        ):
            with contextlib.redirect_stderr(buf):
                DeployCommand.git_ref_callback(ctx, self._param("isaacsim"), "v6.0.1")
        out = buf.getvalue()
        self.assertIn("[git-ref]", out)
        self.assertIn("git ls-remote", out)

    def test_no_debug_is_quiet(self):
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        buf = io.StringIO()
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="hit\n", stderr=""),
        ):
            with contextlib.redirect_stderr(buf):
                DeployCommand.git_ref_callback(
                    ctx, self._param("isaaclab"), "release/3.0.0-beta2"
                )
        self.assertEqual(buf.getvalue(), "")

    def test_latest_resolves_to_newest(self):
        out = "".join(
            f"x\t{r}\n" for r in ["refs/tags/v6.0.0", "refs/tags/v6.0.1"]
        )
        buf = io.StringIO()
        # _call passes ctx=None -> debug off; the resolved version must still print
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout=out, stderr="")
        ):
            with contextlib.redirect_stdout(buf):
                self.assertEqual(self._call("latest", name="isaacsim"), "v6.0.1")
        self.assertIn("v6.0.1", buf.getvalue())  # shown even without --debug

    def test_latest_unresolvable_raises(self):
        buf = io.StringIO()
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout="", stderr="")
        ):
            with contextlib.redirect_stdout(buf):
                with self.assertRaises(click.BadParameter):
                    self._call("latest", name="isaacsim")


class Test_SplitRepoAndRef(unittest.TestCase):
    """Tests for the repo/ref splitter (NVBugs 6696514)."""

    def test_plain_refs_are_not_repos(self):
        for ref in ["v6.0.1", "release/3.0.0-beta2", "main", "045ca8b", "no", ""]:
            self.assertEqual(DeployCommand.split_repo_and_ref(ref), (None, ref))

    def test_none_passes_through(self):
        self.assertEqual(DeployCommand.split_repo_and_ref(None), (None, None))

    def test_bare_repo_url_has_no_ref(self):
        # exactly what QA pasted at the prompt in the bug report
        url = "https://github.com/isaac-sim/IsaacSim-Internal"
        self.assertEqual(DeployCommand.split_repo_and_ref(url), (url, None))

    def test_repo_at_ref(self):
        self.assertEqual(
            DeployCommand.split_repo_and_ref(
                "https://github.com/isaac-sim/IsaacSim-Internal@v6.1.0-rc20"
            ),
            ("https://github.com/isaac-sim/IsaacSim-Internal", "v6.1.0-rc20"),
        )

    def test_scp_like_ssh_url_is_not_split_on_its_own_at(self):
        url = "git@github.com:isaac-sim/IsaacSim-Internal.git"
        self.assertEqual(DeployCommand.split_repo_and_ref(url), (url, None))

    def test_ssh_url_with_port_is_not_split_on_userinfo(self):
        # "ssh://git@host:22/..." - the "@" belongs to the userinfo, not a ref
        url = "ssh://git@gitlab.nvidia.com:22/isaac/sim.git"
        self.assertEqual(DeployCommand.split_repo_and_ref(url), (url, None))
        self.assertEqual(
            DeployCommand.split_repo_and_ref(url + "@main"), (url, "main")
        )

    def test_credentials_in_url_are_not_split_on_userinfo(self):
        url = "https://svc:token123@github.com/isaac-sim/IsaacSim-Internal.git"
        self.assertEqual(DeployCommand.split_repo_and_ref(url), (url, None))
        self.assertEqual(DeployCommand.split_repo_and_ref(url + "@v6.1.0"),
                         (url, "v6.1.0"))

    def test_ref_containing_at_is_preserved(self):
        # the split happens at the FIRST "@" of the path, so the ref stays intact
        self.assertEqual(
            DeployCommand.split_repo_and_ref("https://github.com/o/r.git@user@branch"),
            ("https://github.com/o/r.git", "user@branch"),
        )

    def test_scp_like_ssh_url_with_ref(self):
        self.assertEqual(
            DeployCommand.split_repo_and_ref(
                "git@github.com:isaac-sim/IsaacSim-Internal.git@v6.1.0"
            ),
            ("git@github.com:isaac-sim/IsaacSim-Internal.git", "v6.1.0"),
        )

    def test_ssh_scheme_url(self):
        self.assertEqual(
            DeployCommand.split_repo_and_ref("ssh://git@gitlab.nvidia.com/x/y.git@main"),
            ("ssh://git@gitlab.nvidia.com/x/y.git", "main"),
        )


class Test_GitRepoOverride(unittest.TestCase):
    """--<component>-git-repo and inline <repo>@<ref> overrides (NVBugs 6696514)."""

    @staticmethod
    def _param(name="isaacsim"):
        return SimpleNamespace(name=name)

    def test_repo_callback_normalizes_empty(self):
        for value in [None, "", "   "]:
            self.assertEqual(DeployCommand.git_repo_callback(None, None, value), "")

    def test_repo_callback_strips(self):
        self.assertEqual(
            DeployCommand.git_repo_callback(None, None, "  https://x/y.git "),
            "https://x/y.git",
        )

    def test_explicit_override_is_used_for_validation(self):
        internal = "https://github.com/isaac-sim/IsaacSim-Internal"
        ctx = SimpleNamespace(params={"debug": False, "isaacsim_git_repo": internal}, meta={}, command=None)
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="abc\trefs/tags/v6.1.0\n", stderr=""),
        ) as run:
            DeployCommand.git_ref_callback(ctx, self._param("isaacsim"), "v6.1.0")
        self.assertIn(internal, run.call_args.args[0])
        self.assertNotIn(config["isaacsim_git_repo"], run.call_args.args[0])

    def test_inline_repo_at_ref_sets_repo_and_returns_ref(self):
        internal = "https://github.com/isaac-sim/IsaacSim-Internal"
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="abc\trefs/tags/v6.1.0\n", stderr=""),
        ) as run:
            out = DeployCommand.git_ref_callback(
                ctx, self._param("isaacsim"), f"{internal}@v6.1.0"
            )
        self.assertEqual(out, "v6.1.0")
        self.assertEqual(ctx.meta["isaac_repo_overrides"]["isaacsim"], internal)
        self.assertIn(internal, run.call_args.args[0])

    def test_bare_repo_url_resolves_latest_from_that_repo(self):
        # the exact bug repro: a bare internal URL at the ref prompt
        internal = "https://github.com/isaac-sim/IsaacSim-Internal"
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        out_refs = "".join(
            f"x\t{r}\n" for r in ["refs/tags/v6.0.9", "refs/tags/v6.1.0"]
        )
        buf = io.StringIO()
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout=out_refs, stderr=""),
        ) as run:
            with contextlib.redirect_stdout(buf):
                out = DeployCommand.git_ref_callback(
                    ctx, self._param("isaacsim"), internal
                )
        self.assertEqual(out, "v6.1.0")
        self.assertEqual(ctx.meta["isaac_repo_overrides"]["isaacsim"], internal)
        self.assertIn(internal, run.call_args.args[0])

    def test_error_message_points_at_the_override_option(self):
        # click.BadParameter reads ctx.command when building the message
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout="", stderr="")
        ):
            with self.assertRaises(click.BadParameter) as cm:
                DeployCommand.git_ref_callback(ctx, self._param("isaacsim"), "v9.9.9")
        msg = str(cm.exception)
        self.assertIn("--isaacsim-git-repo", msg)
        self.assertIn("<repo url>@<ref>", msg)

    def test_arena_option_name_is_dashed_in_message(self):
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout="", stderr="")
        ):
            with self.assertRaises(click.BadParameter) as cm:
                DeployCommand.git_ref_callback(
                    ctx, self._param("isaaclab_arena"), "v9.9.9"
                )
        self.assertIn("--isaaclab-arena-git-repo", str(cm.exception))

    def test_default_repo_used_when_no_override(self):
        ctx = SimpleNamespace(params={"debug": False}, meta={}, command=None)
        with mock.patch.object(
            subprocess, "run",
            return_value=SimpleNamespace(stdout="abc\trefs/tags/v6.0.1\n", stderr=""),
        ) as run:
            DeployCommand.git_ref_callback(ctx, self._param("isaacsim"), "v6.0.1")
        self.assertIn(config["isaacsim_git_repo"], run.call_args.args[0])

    def test_no_still_skips_even_with_override(self):
        ctx = SimpleNamespace(params={"debug": False, "isaacsim_git_repo": "https://x/y"}, meta={}, command=None)
        with mock.patch.object(subprocess, "run") as run:
            self.assertEqual(
                DeployCommand.git_ref_callback(ctx, self._param("isaacsim"), "no"), "no"
            )
            run.assert_not_called()


class Test_RepoUrlValidation(unittest.TestCase):
    """The repo lands in an ini-style ansible inventory, so it must be a clean token."""

    @staticmethod
    def _param():
        return SimpleNamespace(name="isaacsim_git_repo")

    def test_valid_urls_accepted(self):
        for url in [
            "https://github.com/isaac-sim/IsaacSim-Internal",
            "https://github.com/o/r.git",
            "git@github.com:o/r.git",
            "ssh://git@gitlab.nvidia.com:22/isaac/sim.git",
            "http://internal.example/x.git",
        ]:
            self.assertEqual(
                DeployCommand.git_repo_callback(None, self._param(), url), url
            )

    def test_inventory_breaking_values_rejected(self):
        ctx = SimpleNamespace(params={}, meta={}, command=None)
        for bad in [
            'https://h/r.git"\ninjected_var="pwned',   # ini injection
            "https://h/r.git ; rm -rf /",              # whitespace / shell-ish
            'https://h/r.git"',                        # stray quote
            "not-a-url",
            "../../etc/passwd",
        ]:
            with self.assertRaises(click.BadParameter):
                DeployCommand.validate_repo_url(ctx, self._param(), bad)

    def test_empty_means_default(self):
        for value in [None, "", "   "]:
            self.assertEqual(
                DeployCommand.git_repo_callback(None, self._param(), value), ""
            )

    def test_redaction_hides_credentials(self):
        self.assertEqual(
            DeployCommand.redact_repo("https://svc:ghp_SECRET@github.com/o/r.git"),
            "https://***@github.com/o/r.git",
        )
        # a bare token (no user:) is the common PAT form and must be masked too
        self.assertEqual(
            DeployCommand.redact_repo("https://ghp_SECRET@github.com/o/r.git"),
            "https://***@github.com/o/r.git",
        )
        # nothing to redact - left alone
        self.assertEqual(
            DeployCommand.redact_repo("https://github.com/o/r.git"),
            "https://github.com/o/r.git",
        )
        # "git@host:path" is an ssh url, not credentials
        self.assertEqual(
            DeployCommand.redact_repo("git@github.com:o/r.git"),
            "git@github.com:o/r.git",
        )

    def test_shell_metacharacters_rejected(self):
        # the arena role interpolates the repo into a shell command
        ctx = SimpleNamespace(params={}, meta={}, command=None)
        for bad in [
            "https://h/x.git$(touch /tmp/pwned)",
            "https://h/x.git`id`",
            "https://h/x.git;id",
            "https://h/x.git|id",
            "https://h/x.git&&id",
            "https://h/x.git${IFS}",
            "https://h/x\x00.git",
        ]:
            with self.assertRaises(click.BadParameter):
                DeployCommand.validate_repo_url(ctx, self._param(), bad)

    def test_legitimate_url_forms_accepted(self):
        for url in [
            "file:///srv/git/repo.git",     # local mirror / air-gapped
            "/srv/git/repo.git",            # local path
            "git+ssh://git@h/o/r.git",
            "HTTPS://h/o/r.git",            # scheme is case-insensitive
            "https://h/o/r.git/",           # trailing slash
        ]:
            self.assertEqual(
                DeployCommand.git_repo_callback(None, self._param(), url), url
            )

    def test_token_in_either_userinfo_field_is_masked(self):
        # a PAT can sit in the first field ("<token>:x-oauth-basic@") or the second
        for url in [
            "https://ghp_TOPSECRET:x-oauth-basic@github.com/o/r.git",
            "https://ghp_TOPSECRET@github.com/o/r.git",
            "https://svc:ghp_TOPSECRET@github.com/o/r.git",
            "https://ghp_TOPSECRET:@github.com/o/r.git",
        ]:
            self.assertNotIn("TOPSECRET", DeployCommand.redact_repo(url))

    def test_subprocess_error_text_does_not_leak_a_token(self):
        # str(TimeoutExpired) embeds the whole argv, repo url included
        secret = "https://ghp_TOPSECRET@github.com/o/r.git"
        ctx = SimpleNamespace(
            params={}, meta={}, command=None, resilient_parsing=False
        )
        buf = io.StringIO()
        err = subprocess.TimeoutExpired(["git", "ls-remote", secret], 30)
        with mock.patch.object(subprocess, "run", side_effect=err):
            with contextlib.redirect_stderr(buf):
                DeployCommand.git_ref_callback(
                    ctx, SimpleNamespace(name="isaacsim"), f"{secret}@v1.2.3"
                )
        self.assertNotIn("TOPSECRET", buf.getvalue())

    def test_ref_not_found_error_does_not_leak_a_token(self):
        ctx = SimpleNamespace(params={}, meta={}, command=None)
        secret = "https://ghp_TOPSECRET@github.com/o/r.git"
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout="", stderr="")
        ):
            with self.assertRaises(click.BadParameter) as cm:
                DeployCommand.git_ref_callback(
                    ctx, SimpleNamespace(name="isaacsim"), f"{secret}@v9.9.9"
                )
        self.assertNotIn("ghp_TOPSECRET", str(cm.exception))
        self.assertIn("***", str(cm.exception))

    def test_error_message_does_not_leak_a_token(self):
        ctx = SimpleNamespace(params={}, meta={}, command=None)
        with self.assertRaises(click.BadParameter) as cm:
            DeployCommand.validate_repo_url(
                ctx, self._param(), "https://svc:ghp_SECRET@h/r.git bad"
            )
        self.assertNotIn("ghp_SECRET", str(cm.exception))


class Test_RepoOverrideThroughRealCli(unittest.TestCase):
    """
    End-to-end through actual click parsing (NVBugs 6696514).

    These drive a real command rather than a hand-built ctx, because the earlier
    ctx.params approach only worked on some click versions and only when the repo
    option preceded the ref option on the command line.
    """

    INTERNAL = "https://github.com/isaac-sim/IsaacSim-Internal"
    BASE = [
        "--deployment-name", "t", "--isaaclab", "no", "--isaaclab-arena", "no",
        "--ingress-cidrs", "myip", "--existing", "replace", "--no-upload",
    ]

    def _run(self, args):
        """Invoke a DeployCommand, returning (final params, repos git was asked about)."""
        seen = []
        captured = {}

        @click.command(cls=DeployCommand)
        def cmd(**kwargs):
            captured.update(kwargs)

        def fake_run(argv, **kwargs):
            seen.append(argv)
            return SimpleNamespace(stdout="abc\trefs/tags/v6.1.0\n", stderr="")

        with mock.patch.object(subprocess, "run", fake_run):
            with contextlib.redirect_stdout(io.StringIO()):
                cmd.main(args + self.BASE, standalone_mode=False)
        # the repo is the first non-flag argument after "git ls-remote"
        queried = [
            next(x for x in a[2:] if not x.startswith("-"))
            for a in seen
            if a[:2] == ["git", "ls-remote"]
        ]
        return captured, queried

    def test_bare_internal_url_at_the_ref_prompt(self):
        # the exact input from the bug report
        params, queried = self._run(["--isaacsim", self.INTERNAL])
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertEqual(params["isaacsim"], "v6.1.0")  # resolved via "latest"

    def test_inline_repo_at_ref(self):
        params, queried = self._run(["--isaacsim", f"{self.INTERNAL}@v6.1.0"])
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertEqual(params["isaacsim"], "v6.1.0")
        self.assertIn(self.INTERNAL, queried)

    def test_explicit_option_before_ref(self):
        params, queried = self._run(
            ["--isaacsim-git-repo", self.INTERNAL, "--isaacsim", "v6.1.0"]
        )
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertIn(self.INTERNAL, queried)

    def test_explicit_option_after_ref_still_wins(self):
        # click processes options in invocation order; the repo option is eager so
        # command-line order must not change the outcome
        params, queried = self._run(
            ["--isaacsim", "v6.1.0", "--isaacsim-git-repo", self.INTERNAL]
        )
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertIn(self.INTERNAL, queried)
        self.assertNotIn(config["isaacsim_git_repo"], queried)

    def test_default_repo_unchanged_when_no_override(self):
        params, queried = self._run(["--isaacsim", "v6.0.1"])
        self.assertEqual(params["isaacsim_git_repo"], "")
        self.assertIn(config["isaacsim_git_repo"], queried)

    def test_conflicting_repos_rejected(self):
        with self.assertRaises(click.BadParameter):
            self._run([
                "--isaacsim-git-repo", "https://github.com/o/other.git",
                "--isaacsim", f"{self.INTERNAL}@v6.1.0",
            ])

    def test_cosmetic_repo_variants_are_not_a_conflict(self):
        # same repo, differing only by ".git" / trailing slash
        params, _ = self._run([
            "--isaacsim-git-repo", self.INTERNAL + ".git",
            "--isaacsim", f"{self.INTERNAL}@v6.1.0",
        ])
        self.assertTrue(params["isaacsim_git_repo"])

    def test_same_repo_twice_is_fine(self):
        params, _ = self._run([
            "--isaacsim-git-repo", self.INTERNAL,
            "--isaacsim", f"{self.INTERNAL}@v6.1.0",
        ])
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)

    def test_invalid_repo_url_rejected_at_cli(self):
        with self.assertRaises(click.BadParameter):
            self._run(["--isaacsim-git-repo", "not a url", "--isaacsim", "v6.1.0"])

    def test_validation_not_bypassed_by_a_help_shaped_value(self):
        # validation must not be skippable by putting "--help" anywhere in argv
        with self.assertRaises(click.BadParameter):
            self._run([
                "--isaacsim-git-repo", "https://h/x.git; rm -rf /",
                "--isaacsim", "no",
                "--deployment-name", "--help",
            ])

    def test_help_still_works_with_an_invalid_repo_url(self):
        # the repo options are eager, so validation must not pre-empt --help
        @click.command(cls=DeployCommand)
        def cmd(**kwargs):
            pass

        for args in (
            ["--help", "--isaacsim-git-repo", "bad url"],
            ["--isaacsim-git-repo", "bad url", "--help"],
        ):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    cmd.main(args, standalone_mode=False)
                except SystemExit:
                    pass  # click exits after printing help in some versions
            self.assertIn("--help", buf.getvalue())

    def test_lab_and_arena_have_the_same_override(self):
        # BASE pins --isaaclab/--isaaclab-arena to "no", so drive this one directly
        seen = []
        captured = {}

        @click.command(cls=DeployCommand)
        def cmd(**kwargs):
            captured.update(kwargs)

        def fake_run(argv, **kwargs):
            seen.append(argv)
            return SimpleNamespace(stdout="abc\trefs/tags/v1.0.0\n", stderr="")

        with mock.patch.object(subprocess, "run", fake_run):
            with contextlib.redirect_stdout(io.StringIO()):
                cmd.main([
                    "--isaacsim", "no",
                    "--isaaclab-git-repo", "https://github.com/o/lab.git",
                    "--isaaclab", "v1.0.0",
                    "--isaaclab-arena", "no",
                    "--deployment-name", "t", "--ingress-cidrs", "myip",
                    "--existing", "replace", "--no-upload",
                ], standalone_mode=False)

        queried = [
            next(x for x in a[2:] if not x.startswith("-"))
            for a in seen
            if a[:2] == ["git", "ls-remote"]
        ]
        self.assertEqual(captured["isaaclab_git_repo"], "https://github.com/o/lab.git")
        self.assertEqual(queried, ["https://github.com/o/lab.git"])


class Test_InventoryRendering(unittest.TestCase):
    """The repo must survive into the ansible inventory (NVBugs 6696514)."""

    TEMPLATE = Path(__file__).resolve().parents[1] / "ansible" / "inventory.template"

    def _render(self, overrides):
        params = dict(
            cloud="aws", in_china="false", ssh_port=22, vnc_password="x",
            deployment_name="d", isaaclab="no", isaacsim="v6.1.0",
            isaaclab_private_git="", system_user_password="p", isaaclab_arena="no",
            demos="no", isaac_workstation_ip="1.2.3.4", config=config,
        )
        params.update(overrides)
        # mirrors Deployer.create_ansible_inventory's default backfill
        for key in ("isaacsim_git_repo", "isaaclab_git_repo",
                    "isaaclab_arena_git_repo"):
            if not str(params.get(key) or "").strip():
                params[key] = config[key]
        return self.TEMPLATE.read_text().format(**params)

    def test_defaults_used_when_no_override(self):
        out = self._render({})
        self.assertIn(f'isaacsim_git_repo="{config["isaacsim_git_repo"]}"', out)
        self.assertIn(f'isaaclab_git_repo="{config["isaaclab_git_repo"]}"', out)

    def test_override_reaches_the_inventory(self):
        internal = "https://github.com/isaac-sim/IsaacSim-Internal"
        out = self._render({"isaacsim_git_repo": internal})
        self.assertIn(f'isaacsim_git_repo="{internal}"', out)
        # the other components keep their defaults
        self.assertIn(f'isaaclab_git_repo="{config["isaaclab_git_repo"]}"', out)

    def test_legacy_state_without_the_new_keys_still_renders(self):
        # a deployment saved by an older release has no *_git_repo params at all;
        # --existing repair/run_ansible re-renders from it and must not KeyError
        out = self._render({})
        self.assertIn("isaacsim_git_repo=", out)


class Test_VersionKeyAndResolve(unittest.TestCase):
    """Tests for the auto-detect helpers (NVBugs 6380502 follow-up)."""

    def test_version_key_ordering(self):
        vk = DeployCommand._version_key
        self.assertGreater(vk("6.0.1"), vk("6.0.0"))
        self.assertGreater(vk("6.0.0"), vk("6.0.0-dev2"))
        self.assertGreater(vk("3.0.0-beta2"), vk("3.0.0-beta"))
        self.assertGreater(vk("3.0.0-beta2"), vk("2.3.2"))
        self.assertGreater(vk("3.0.0"), vk("3.0.0-beta2"))
        self.assertIsNone(vk("not-a-version"))

    @staticmethod
    def _resolve(refs):
        out = "".join(
            f"0000000000000000000000000000000000000000\t{r}\n" for r in refs
        )
        with mock.patch.object(
            subprocess, "run", return_value=SimpleNamespace(stdout=out, stderr="")
        ):
            return DeployCommand._resolve_latest_ref("repo", lambda m: None)

    def test_resolve_sim_like_tags_only(self):
        self.assertEqual(
            self._resolve([
                "refs/tags/v5.1.0", "refs/tags/v6.0.0-dev2", "refs/tags/v6.0.0",
                "refs/tags/v6.0.1", "refs/tags/v6.0.1^{}",
            ]),
            "v6.0.1",
        )

    def test_resolve_lab_like_branch_wins_tie(self):
        self.assertEqual(
            self._resolve([
                "refs/tags/v2.3.2", "refs/tags/v3.0.0-beta2",
                "refs/heads/release/2.3.0", "refs/heads/release/3.0.0-beta2",
                "refs/heads/main",
            ]),
            "release/3.0.0-beta2",
        )

    def test_resolve_arena_like_branches_only(self):
        self.assertEqual(
            self._resolve([
                "refs/heads/release/0.1.0", "refs/heads/release/0.2.0",
                "refs/heads/release/0.2.1", "refs/heads/main",
            ]),
            "release/0.2.1",
        )

    def test_resolve_none_when_no_releases(self):
        self.assertIsNone(self._resolve(["refs/heads/main", "refs/heads/develop"]))


class Test_RefOnRepoOption(unittest.TestCase):
    """
    "<repo url>@<ref>" passed to --<component>-git-repo (NVBugs 6696514 reopen).

    QA ran `./deploy-aws --isaacsim-git-repo <url>@develop`: the repo option takes a
    repository, so the "@develop" was cloned as part of the url and the ref option still
    prompted.
    """

    INTERNAL = "https://github.com/isaac-sim/IsaacSim-Internal"
    BASE = [
        "--isaaclab", "no", "--isaaclab-arena", "no", "--deployment-name", "t",
        "--ingress-cidrs", "myip", "--existing", "replace", "--no-upload",
    ]

    def _run(self, args):
        seen = []
        captured = {}

        @click.command(cls=DeployCommand)
        def cmd(**kwargs):
            captured.update(kwargs)

        def fake_run(argv, **kwargs):
            seen.append(argv)
            return SimpleNamespace(stdout="x\trefs/heads/develop\n", stderr="")

        with mock.patch.object(subprocess, "run", fake_run):
            with contextlib.redirect_stdout(io.StringIO()):
                cmd.main(args + self.BASE, standalone_mode=False)
        queried = [
            next(x for x in a[2:] if not x.startswith("-"))
            for a in seen if a[:2] == ["git", "ls-remote"]
        ]
        return captured, queried

    def test_ref_is_split_off_and_used(self):
        params, queried = self._run(["--isaacsim-git-repo", f"{self.INTERNAL}@develop"])
        # the ref must not remain glued to the repo url
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertEqual(params["isaacsim"], "develop")
        self.assertEqual(queried, [self.INTERNAL])

    def test_no_prompt_when_ref_comes_from_the_repo_option(self):
        # stdin closed: a prompt here would raise Abort instead of completing
        with mock.patch("click.termui.visible_prompt_func",
                        side_effect=EOFError("would prompt")):
            params, _ = self._run(["--isaacsim-git-repo", f"{self.INTERNAL}@develop"])
        self.assertEqual(params["isaacsim"], "develop")

    def test_explicit_ref_option_wins(self):
        params, _ = self._run([
            "--isaacsim-git-repo", f"{self.INTERNAL}@develop",
            "--isaacsim", "v6.1.0",
        ])
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertEqual(params["isaacsim"], "v6.1.0")

    def test_plain_repo_option_still_prompts_nothing_extra(self):
        params, _ = self._run(["--isaacsim-git-repo", self.INTERNAL, "--isaacsim", "v6.1.0"])
        self.assertEqual(params["isaacsim_git_repo"], self.INTERNAL)
        self.assertEqual(params["isaacsim"], "v6.1.0")

    def test_lab_and_arena_behave_the_same(self):
        for opt, name in (("--isaaclab-git-repo", "isaaclab"),
                          ("--isaaclab-arena-git-repo", "isaaclab_arena")):
            seen = []
            captured = {}

            @click.command(cls=DeployCommand)
            def cmd(**kwargs):
                captured.update(kwargs)

            def fake_run(argv, **kwargs):
                seen.append(argv)
                return SimpleNamespace(stdout="x\trefs/heads/develop\n", stderr="")

            with mock.patch.object(subprocess, "run", fake_run):
                with contextlib.redirect_stdout(io.StringIO()):
                    cmd.main([
                        opt, "https://github.com/o/r.git@develop",
                        "--isaacsim", "no",
                        "--deployment-name", "t", "--ingress-cidrs", "myip",
                        "--existing", "replace", "--no-upload",
                    ] + (["--isaaclab-arena", "no"] if name == "isaaclab" else
                         ["--isaaclab", "no"]), standalone_mode=False)
            self.assertEqual(captured[f"{name}_git_repo"], "https://github.com/o/r.git")
            self.assertEqual(captured[name], "develop")


class Test_GitEnvironment(unittest.TestCase):
    """Local git calls must never block on a credential prompt (NVBugs 6696514)."""

    def test_terminal_prompt_disabled(self):
        self.assertEqual(DeployCommand._git_env()["GIT_TERMINAL_PROMPT"], "0")

    def test_askpass_vars_blanked_not_removed(self):
        # git uses the FIRST of GIT_ASKPASS / core.askpass / SSH_ASKPASS that is SET.
        # An empty value stops that search; removing the variable lets a desktop
        # core.askpass (a GUI dialog) take over and block forever.
        with mock.patch.dict(os.environ, {"GIT_ASKPASS": "/usr/bin/x",
                                          "SSH_ASKPASS": "/usr/bin/y"}):
            env = DeployCommand._git_env()
        self.assertEqual(env["GIT_ASKPASS"], "")
        self.assertEqual(env["SSH_ASKPASS"], "")

    def test_credential_helper_and_askpass_are_pinned(self):
        env = DeployCommand._git_env()
        pinned = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
                  for i in range(int(env["GIT_CONFIG_COUNT"]))}
        self.assertIn("credential.helper", pinned)
        self.assertEqual(pinned["core.askpass"], "")

    def test_existing_git_config_env_is_preserved(self):
        # the caller may inject its own config this way (a proxy, an internal CA);
        # clobbering it breaks exactly the repos that need it
        with mock.patch.dict(os.environ, {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.proxy",
            "GIT_CONFIG_VALUE_0": "http://proxy.example:8080",
        }):
            env = DeployCommand._git_env()
        pinned = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
                  for i in range(int(env["GIT_CONFIG_COUNT"]))}
        self.assertEqual(pinned["http.proxy"], "http://proxy.example:8080")
        self.assertIn("credential.helper", pinned)

    def _assert_no_hang(self, gitconfig_body, label):
        """
        Behavioural: run real git against a gitconfig whose credential path blocks,
        and require it to come back. These are the regressions the env-var assertions
        above cannot catch.
        """
        if not shutil.which("git"):
            self.skipTest("git not available")
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp)
            blocker = home / "blocker.sh"
            marker = home / "ran.log"
            blocker.write_text(f"#!/bin/sh\necho ran >> {marker}\nsleep 30\n")
            blocker.chmod(0o755)
            cfg = home / "gitconfig"
            cfg.write_text(gitconfig_body.format(blocker=blocker))

            env = DeployCommand._git_env()
            env["HOME"] = str(home)
            env["GIT_CONFIG_GLOBAL"] = str(cfg)
            try:
                subprocess.run(
                    ["git", "ls-remote", "--quiet",
                     "https://github.com/isaac-sim/definitely-not-real-xyz", "HEAD"],
                    capture_output=True, text=True, timeout=20, env=env,
                )
            except subprocess.TimeoutExpired:
                self.fail(f"git hung on a blocking {label}")
            self.assertFalse(
                marker.exists(), f"blocking {label} was executed"
            )

    def test_real_git_does_not_hang_on_a_gui_askpass(self):
        self._assert_no_hang("[core]\n\taskpass = {blocker}\n", "core.askpass")

    def test_real_git_does_not_hang_on_a_blocking_credential_helper(self):
        # credential.helper is multi-valued: appending a helper leaves the user's own
        # helper ahead of it in the list, so it still runs first and still hangs
        self._assert_no_hang(
            "[credential]\n\thelper = {blocker}\n", "credential.helper"
        )

    def test_real_git_does_not_hang_with_both_configured(self):
        self._assert_no_hang(
            "[credential]\n\thelper = {blocker}\n[core]\n\taskpass = {blocker}\n",
            "credential.helper + core.askpass",
        )

    def test_real_git_does_not_hang_on_a_per_url_credential_helper(self):
        self._assert_no_hang(
            '[credential "https://github.com"]\n\thelper = {blocker}\n',
            "per-URL credential.helper",
        )

    def test_negative_git_config_count_does_not_clobber_caller_config(self):
        with mock.patch.dict(os.environ, {
            "GIT_CONFIG_COUNT": "-1",
            "GIT_CONFIG_KEY_0": "http.proxy",
            "GIT_CONFIG_VALUE_0": "http://proxy.example:8080",
        }):
            env = DeployCommand._git_env()
        self.assertGreaterEqual(int(env["GIT_CONFIG_COUNT"]), 2)
        pinned = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
                  for i in range(int(env["GIT_CONFIG_COUNT"]))}
        self.assertIn("credential.helper", pinned)

    def test_credential_helper_list_is_reset_before_the_real_helper(self):
        env = DeployCommand._git_env()
        keys = [(env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"])
                for i in range(int(env["GIT_CONFIG_COUNT"]))]
        helpers = [i for i, (k, _) in enumerate(keys) if k == "credential.helper"]
        # the first credential.helper entry must be the empty reset
        self.assertEqual(keys[helpers[0]][1], "")

    @staticmethod
    def _helpers(env):
        """credential.helper values, in the order git will see them."""
        return [env[f"GIT_CONFIG_VALUE_{i}"]
                for i in range(int(env["GIT_CONFIG_COUNT"]))
                if env[f"GIT_CONFIG_KEY_{i}"] == "credential.helper"]

    def test_uses_gh_when_available(self):
        with mock.patch.object(shutil, "which", return_value="/usr/local/bin/gh"):
            helpers = self._helpers(DeployCommand._git_env())
        # reset first, then gh - order matters, the list is multi-valued.
        # gh is referenced by absolute path: the helper runs through sh, which may
        # not inherit a PATH containing gh.
        self.assertEqual(helpers, ["", "!/usr/local/bin/gh auth git-credential"])

    def test_no_helper_when_gh_missing(self):
        with mock.patch.object(shutil, "which", return_value=None):
            helpers = self._helpers(DeployCommand._git_env())
        self.assertEqual(helpers, [""])

    def test_ls_remote_calls_use_the_env(self):
        captured = {}

        def fake_run(argv, **kwargs):
            captured["env"] = kwargs.get("env")
            return SimpleNamespace(stdout="x\trefs/tags/v1\n", stderr="")

        ctx = SimpleNamespace(params={}, meta={}, command=None, resilient_parsing=False)
        with mock.patch.object(subprocess, "run", fake_run):
            DeployCommand.git_ref_callback(ctx, SimpleNamespace(name="isaacsim"), "v1")
        self.assertEqual(captured["env"]["GIT_TERMINAL_PROMPT"], "0")


if __name__ == "__main__":
    unittest.main()
