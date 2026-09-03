# region copyright
# Copyright 2023-2026 NVIDIA Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# endregion

"""
Base deploy- command
"""

import os
import re
import shutil
import subprocess
import sys

import click
import randomname
from pwgen import pwgen

from click.core import ParameterSource

from src.python.config import c as config
from src.python.debug import debug_break  # noqa
from src.python.utils import (
    colorize_error,
    colorize_info,
    colorize_prompt,
    get_my_public_ip,
    subnet_from_ip,
)


class _IsaacRefOption(click.core.Option):
    """
    The ref option for an Isaac component.

    When the matching --<component>-git-repo carried a "<repo url>@<ref>", that ref is
    used instead of prompting: the prompt happens before any callback runs, so the value
    has to be supplied at consume time (NVBugs 6696514).
    """

    def consume_value(self, ctx, opts):
        # check the stash BEFORE delegating: the base implementation prompts, and a
        # prompt the user never has to answer is just noise
        stashed = ctx.meta.get(DeployCommand._REF_META_KEY, {}).get(self.name)
        if stashed and self.name not in opts:
            return stashed, ParameterSource.COMMANDLINE
        return super().consume_value(ctx, opts)


class DeployCommand(click.core.Command):
    """
    Defines common cli options for "deploy-*" commands.
    """

    def make_context(self, info_name, args, parent=None, **extra):
        """
        Allow deployment name as an unnamed first argument.
        e.g. ./deploy-aws mydeployment is equivalent to ./deploy-aws --deployment-name mydeployment
        """
        args = list(args)
        if (
            args
            and not args[0].startswith("-")
            and "--deployment-name" not in args
            and "--dn" not in args
        ):
            args = ["--deployment-name", args[0]] + args[1:]
        return super().make_context(info_name, args, parent=parent, **extra)

    @staticmethod
    def deployment_name_callback(ctx, param, value):
        # validate
        if not re.match("^[a-z0-9\\-]{1,32}$", value):
            raise click.BadParameter(
                colorize_error(
                    "Only lower case letters, numbers and '-' are allowed."
                    + f" Length should be between 1 and 32 characters ({len(value)} provided)."
                )
            )

        return value

    def ingress_cidrs_callback(ctx, param, value):
        """
        Called after parsing --ingress-cidrs option
        """

        # allow special values
        if value is None or value == "":
            return value

        # split by commas
        value = value.split(",")

        # strip spaces, convert to lower case
        value = [v.strip().lower() for v in value]

        # validate each CIDR block
        for cidr in value:
            if cidr not in [
                "",
                "auto",
                "myip",
                "myip/8",
                "myip/16",
                "myip/24",
                "mynet",
                "nvidia",
                None,
            ] and not re.match(r"^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$", cidr):
                raise click.BadParameter(colorize_error(f"Invalid CIDR block: {cidr}"))

        return ",".join(value)

    # human-readable app names for the --isaacsim/--isaaclab/--isaaclab-arena options
    _APP_NAMES = {
        "isaacsim": "Isaac Sim",
        "isaaclab": "Isaac Lab",
        "isaaclab_arena": "Isaac Lab Arena",
    }

    # release-version comparison ranks: a stable release outranks any of its
    # prereleases; among prereleases dev < alpha < beta < rc.
    _PRE_RANK = {"dev": 0, "alpha": 1, "a": 1, "beta": 2, "b": 2, "rc": 3, "c": 3}

    @staticmethod
    def _version_key(ver):
        """
        Sort key for a release version string ("6.0.1", "3.0.0-beta2", "6.0.0-dev2").
        Returns None when the string is not a recognizable version. Higher key = newer:
        stable sorts above its own prereleases; numeric components dominate.
        """
        m = re.match(r"^(\d+(?:\.\d+)*)(?:[-.]?([A-Za-z]+)\.?(\d+)?)?$", ver)
        if not m:
            return None
        nums = tuple(int(x) for x in m.group(1).split("."))
        nums = nums + (0,) * (4 - len(nums)) if len(nums) < 4 else nums
        pre = m.group(2)
        if pre is None:
            return (nums, 1, 0, 0)  # stable
        return (nums, 0, DeployCommand._PRE_RANK.get(pre.lower(), -1),
                int(m.group(3)) if m.group(3) else 0)

    @staticmethod
    def _resolve_latest_ref(repo, dbg):
        """
        Auto-detect the latest release ref in `repo`: the highest version across its
        tags and release/* branches (prereleases included). On a version tie a
        release/* branch wins over a tag (matches how Lab/Arena are tracked). Returns
        the ref to check out (e.g. "v6.0.1" or "release/0.2.1"), or None if none found.
        """
        cmd = ["git", "ls-remote", "--tags", "--heads", repo]
        safe = DeployCommand.redact_repo(repo)
        dbg("latest: resolving latest release for " + safe)
        dbg("running: " + " ".join(cmd).replace(repo, safe))
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            env=DeployCommand._git_env(),
        )
        if result.stderr.strip():
            dbg("stderr: " + result.stderr.strip())

        best = None  # (version_key, is_branch, ref)
        for line in result.stdout.splitlines():
            ref = line.split("\t")[-1].strip()
            if ref.endswith("^{}"):  # peeled tag line, skip
                continue
            if ref.startswith("refs/tags/"):
                name = ref[len("refs/tags/"):]
                ver, is_branch = name.lstrip("v"), False
            elif ref.startswith("refs/heads/release/"):
                name = ref[len("refs/heads/"):]
                ver, is_branch = name[len("release/"):], True
            else:
                continue
            key = DeployCommand._version_key(ver)
            if key is None:
                dbg(f"candidate {name}: version '{ver}' unparseable - skipping")
                continue
            dbg(f"candidate {name}: version {ver}")
            cand = (key, is_branch, name)
            if best is None or cand[:2] > best[:2]:
                best = cand

        if best is None:
            dbg("latest: no release tags or release/* branches found")
            return None
        dbg(f"latest: selected {best[2]}")
        return best[2]

    # option name -> the config key holding that component's default git repo
    _REPO_KEYS = {
        "isaacsim": "isaacsim_git_repo",
        "isaaclab": "isaaclab_git_repo",
        "isaaclab_arena": "isaaclab_arena_git_repo",
    }

    # where an inline "<repo url>@<ref>" override is stashed during parsing (ctx.meta,
    # so no option's default can overwrite it - see git_ref_callback)
    _REPO_META_KEY = "isaac_repo_overrides"

    # a ref recovered from a "<repo url>@<ref>" passed to --<component>-git-repo
    _REF_META_KEY = "isaac_ref_from_repo_option"

    def invoke(self, ctx):
        """
        Fold any inline "<repo url>@<ref>" override into the final parameters, so the
        deployer (and the Ansible inventory it renders) sees the same repo the ref was
        validated against, no matter what order the options were given in.
        """
        own = {p.name for p in self.params}
        for name, repo in ctx.meta.get(DeployCommand._REPO_META_KEY, {}).items():
            key = f"{name}_git_repo"
            if key in own:
                ctx.params[key] = repo

        # Validate here rather than in the option callback: the repo options are eager
        # (the ref check needs them early), and an eager callback would reject a bad url
        # before --help could print. invoke() runs only when the command really executes.
        for name in DeployCommand._REPO_KEYS:
            key = f"{name}_git_repo"
            repo = ctx.params.get(key)
            if repo:
                DeployCommand.validate_repo_url(ctx, None, repo)

        return super().invoke(ctx)

    @staticmethod
    def _git_env():
        """
        Environment for local `git` calls: never stop to ask for credentials.

        Without this, a private repository whose credentials are missing or wrong makes
        git ask for a username and password - on a terminal, or through a GUI dialog
        from an askpass program or credential helper - and wait there. QA sat on that
        for over two hours (NVBugs 6696514). With this, git fails immediately and the
        deploy reports a real message instead.

        A credential helper that works non-interactively (the GitHub CLI, below) is
        still used, so a private repository verifies for real rather than being
        reported as missing.
        """
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        # Blank, do NOT remove: git reads GIT_ASKPASS, then core.askpass from the user's
        # gitconfig, then SSH_ASKPASS, and uses the first one that is SET. An empty value
        # is set-but-disabled and stops that search; removing the variable instead lets a
        # desktop core.askpass (a GUI password dialog) take over and block forever.
        env["GIT_ASKPASS"] = ""
        env["SSH_ASKPASS"] = ""

        # The credential helper is a separate path that askpass does not cover, and a
        # blocking helper hangs the same way. credential.helper is MULTI-VALUED, so
        # adding an entry only appends to whatever the user already configured - their
        # helper would still run first. An empty value RESETS the list, so emit that
        # first and the real helper after it.
        #
        # Prefer the GitHub CLI: it is how an operator is already authenticated locally,
        # so a private/internal repo verifies for real instead of failing as "not
        # found". Reset only when gh is missing (e.g. inside the container), which fails
        # fast rather than prompting.
        # Append to any config the caller injected this way (a proxy, an internal CA):
        # clobbering it breaks exactly the repos that need it.
        try:
            count = int(env.get("GIT_CONFIG_COUNT", "0") or 0)
        except ValueError:
            count = 0
        count = max(count, 0)

        entries = [("credential.helper", ""), ("core.askpass", "")]
        gh = shutil.which("gh")
        if gh:
            # absolute path: the helper runs through `sh`, which may not inherit a PATH
            # that contains gh
            entries.append(("credential.helper", f"!{gh} auth git-credential"))
        for offset, (key, value) in enumerate(entries):
            env[f"GIT_CONFIG_KEY_{count + offset}"] = key
            env[f"GIT_CONFIG_VALUE_{count + offset}"] = value
        env["GIT_CONFIG_COUNT"] = str(count + len(entries))
        return env

    @staticmethod
    def _looks_like_repo_url(value):
        """
        True if `value` names a git repository rather than a ref: an http(s)/git/ssh URL
        or the scp-like form git@host:org/repo. Refs never contain "://" and cannot
        carry a "host:path", so this stays unambiguous.
        """
        value = value.strip()
        return bool(
            re.match(r"^(https?|git|ssh)://", value)
            or re.match(r"^[\w.-]+@[\w.-]+:", value)
        )

    @staticmethod
    def redact_repo(repo):
        """
        Hide any credentials embedded in a repo url before it is shown to the user or
        written to disk:
          "https://user:token@host/x.git" -> "https://***@host/x.git"
          "https://token@host/x.git"      -> "https://***@host/x.git"
        A repo url is echoed in errors and stored in the deployment's meta.json, and a
        token must never land in either.
        """
        if not repo:
            return repo
        # Mask the entire userinfo: a token can be in either field
        # ("user:token@", "token@", "token:x-oauth-basic@"), so keeping any part of
        # it risks leaking the secret. The scp form "git@host:path" is not
        # credentials, so only "scheme://" urls are touched.
        return re.sub(r"(://)[^/@]+@", r"\1***@", str(repo))

    @staticmethod
    def _same_repo(a, b):
        """
        True if two repo urls point at the same place, ignoring a trailing "/" and a
        ".git" suffix, so cosmetic differences are not reported as a conflict.
        """
        def norm(u):
            u = str(u).strip().rstrip("/")
            return u[:-4] if u.endswith(".git") else u
        return norm(a) == norm(b)

    @staticmethod
    def split_repo_and_ref(value):
        """
        Split an Isaac component option value into (repo, ref).

        Accepts a plain ref ("v6.0.1" -> (None, "v6.0.1")), an inline repo override
        ("<repo url>@<ref>" -> (repo, ref)), or a bare repo URL with no ref
        ("<repo url>" -> (repo, None); the caller substitutes its default ref).
        Returns (None, value) for anything that is not a repo, so plain refs are
        untouched. NVBugs 6696514: QA pasted an internal repo URL at the ref prompt.

        The split is structural, not a plain "last @": a url can legitimately contain
        "@" in its userinfo ("ssh://git@host:22/x.git", "https://user:token@host/x.git"),
        so only an "@" in the final path segment separates the ref. A ref that itself
        contains "@" needs the explicit --<component>-git-repo option.
        """
        if value is None:
            return None, value
        text = str(value).strip()
        if not DeployCommand._looks_like_repo_url(text):
            return None, value

        # find where the repo path starts, so userinfo "@" is never mistaken for a
        # ref separator: after "scheme://host" for urls, after "host:" for scp form
        m = re.match(r"^(https?|git|ssh)://[^/]*", text)
        path_start = m.end() if m else text.find(":") + 1

        at = text.find("@", path_start)
        if at != -1:
            repo, ref = text[:at].strip(), text[at + 1:].strip()
            return (repo or None), (ref or None)
        return text, None

    # A repo url must be a single clean token. It is written into the ini-style ansible
    # inventory and used by roles that shell out, so anything that could break out of
    # either (whitespace, quotes, backslashes, shell metacharacters, control chars) is
    # rejected. The roles also shell-quote it, so this is the outer of two layers.
    _REPO_URL_FORBIDDEN = re.compile(r"[\s\"'\\$`;|&<>(){}\x00-\x1f]")
    _REPO_URL_RE = re.compile(
        r"^(?:"
        r"(?:https?|ssh|git|git\+ssh|file)://[^/]*/\S*"  # scheme://[host]/path
        r"|[\w.-]+@[\w.-]+:\S+"                          # scp-like host:path
        r"|/\S+"                                         # absolute local path
        r")$",
        re.IGNORECASE,
    )

    @staticmethod
    def git_repo_callback(ctx, param, value):
        """
        Normalize an explicit repo override (--isaacsim-git-repo and friends): empty
        means "use the default repo from config". Validation happens in invoke() - these
        options are eager, and rejecting here would pre-empt --help.

        This option takes a repository, but users reasonably pass the same
        "<repo url>@<ref>" form the ref option accepts. Split it here rather than
        cloning the ref as part of the url, and stash the ref for the matching ref
        option - this callback is eager, so it runs before that option prompts
        (NVBugs 6696514).
        """
        if value is None or not str(value).strip():
            return ""
        value = str(value).strip()

        repo, ref = DeployCommand.split_repo_and_ref(value)
        if repo and ref and ctx is not None:
            name = param.name[: -len("_git_repo")]
            ctx.meta.setdefault(DeployCommand._REF_META_KEY, {})[name] = ref
            return repo
        return value

    @staticmethod
    def validate_repo_url(ctx, param, repo):
        """
        Reject a repo url that is not a single clean token. Raises click.BadParameter.
        """
        if (
            DeployCommand._REPO_URL_FORBIDDEN.search(repo)
            or not DeployCommand._REPO_URL_RE.match(repo)
        ):
            raise click.BadParameter(
                colorize_error(
                    f"invalid git repository url: '{DeployCommand.redact_repo(repo)}'."
                    " Expected something like https://github.com/org/repo.git or"
                    " git@github.com:org/repo.git"
                ),
                ctx=ctx, param=param,
            )
        return repo

    @staticmethod
    def git_ref_callback(ctx, param, value):
        """
        Validate an Isaac component git ref (--isaacsim / --isaaclab / --isaaclab-arena).

        'no' or empty means "don't install", so skip the check. "latest" auto-detects the
        latest release. Otherwise confirm the ref actually exists in the repo, so a bad
        value fails fast here with a clear message instead of dying deep in the Ansible git
        checkout (NVBugs 6380502: a 4-part product version like v6.0.1.0 was passed, but the
        release tag is the 3-part v6.0.1).

        The repo checked is the component default, unless overridden by the matching
        --<component>-git-repo option or by an inline "<repo url>@<ref>" value; that is
        how a fork or an internal repo is deployed (NVBugs 6696514).
        """
        # --debug (parsed before these options) turns on a trace of the check
        debug = (
            bool(ctx and ctx.params.get("debug"))
            or os.environ.get("DEBUG", "0") == "1"
            or "--debug" in sys.argv
        )

        def dbg(msg):
            if debug:
                click.echo(colorize_info(f"* [git-ref] {param.name}: {msg}"), err=True)

        # skip when not installing / no value
        if value is None or str(value).strip().lower() in ("", "no"):
            dbg(f"value {value!r} means 'do not install' - skipping ref check")
            return value

        repo_key = DeployCommand._REPO_KEYS.get(param.name)
        if repo_key is None:
            dbg("no repo mapped for this option - skipping ref check")
            return value

        # an inline "<repo url>@<ref>" (or a bare repo url) overrides the repo for this
        # component. It is stashed in ctx.meta, NOT ctx.params: params is owned by the
        # --<component>-git-repo option, whose own default would overwrite it depending
        # on click's parameter processing order (and hence silently clone the public
        # repo). ctx.meta belongs to no option, so the override always survives.
        inline_repo, inline_ref = DeployCommand.split_repo_and_ref(value)
        if inline_repo:
            DeployCommand.validate_repo_url(ctx, param, inline_repo)
            # two different repos for one component is a mistake, not a precedence
            # question - say so instead of silently picking one
            explicit = (
                ctx.params.get(f"{param.name}_git_repo") if ctx is not None else None
            )
            if explicit and not DeployCommand._same_repo(explicit, inline_repo):
                opt = "--" + param.name.replace("_", "-") + "-git-repo"
                raise click.BadParameter(
                    colorize_error(
                        f"conflicting repositories for {param.name}:"
                        f" {opt} says '{DeployCommand.redact_repo(explicit)}' but the"
                        f" ref says '{DeployCommand.redact_repo(inline_repo)}'."
                        " Pass the repository only once."
                    ),
                    ctx=ctx, param=param,
                )
            value = inline_ref if inline_ref else "latest"
            if ctx is not None:
                ctx.meta.setdefault(DeployCommand._REPO_META_KEY, {})[
                    param.name
                ] = inline_repo
            dbg(
                f"repo override from value: {DeployCommand.redact_repo(inline_repo)}"
                f" (ref {value!r})"
            )

        # Resolution order: inline "<repo>@<ref>" -> explicit --<component>-git-repo ->
        # config default. The explicit option may not be parsed yet (click processes
        # options in invocation order), so read it from ctx.params only as a fallback.
        repo = inline_repo
        if not repo and ctx is not None:
            repo = ctx.meta.get(DeployCommand._REPO_META_KEY, {}).get(param.name)
        if not repo and ctx is not None:
            repo = ctx.params.get(f"{param.name}_git_repo")
        if not repo:
            repo = config[repo_key]
        dbg(f"using repo {DeployCommand.redact_repo(repo)}")

        # "latest" -> resolve the latest release ref and use that
        if value.strip().lower() == "latest":
            try:
                resolved = DeployCommand._resolve_latest_ref(repo, dbg)
            except (OSError, subprocess.SubprocessError) as e:
                raise click.BadParameter(
                    colorize_error(
                        f"could not auto-detect the latest {param.name} release"
                        f" from {DeployCommand.redact_repo(repo)}"
                        f" ({str(e).replace(repo, DeployCommand.redact_repo(repo))})."
                        " Pass an explicit git ref or 'no'."
                    ),
                    ctx=ctx, param=param,
                )
            if not resolved:
                raise click.BadParameter(
                    colorize_error(
                        f"could not auto-detect the latest {param.name} release"
                        f" from {DeployCommand.redact_repo(repo)}."
                        " Pass an explicit git ref or 'no'."
                    ),
                    ctx=ctx, param=param,
                )
            app = DeployCommand._APP_NAMES.get(param.name, param.name)
            click.echo(colorize_info(
                f"* Detected latest release for {app}: {resolved}"
            ))
            return resolved

        # a raw commit sha is a valid ref but cannot be matched by ls-remote; let it pass
        if re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
            dbg(f"'{value}' looks like a commit sha - accepting without ls-remote")
            return value

        cmd = ["git", "ls-remote", "--quiet", repo,
               value, f"refs/tags/{value}", f"refs/heads/{value}"]
        safe_repo = DeployCommand.redact_repo(repo)
        dbg(f"checking ref '{value}' in {safe_repo}")
        dbg("running: " + " ".join(cmd).replace(repo, safe_repo))
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                env=DeployCommand._git_env(),
            )
        except (OSError, subprocess.SubprocessError) as e:
            # network/git problem: warn but do not block the deploy on it
            # str(e) embeds the whole argv, including the repo url and any token
            reason = str(e).replace(repo, safe_repo)
            click.echo(colorize_error(
                f"Warning: could not verify {param.name} ref '{value}'"
                f" ({reason}). Continuing."
            ), err=True)
            return value

        found = result.stdout.strip()
        if debug:
            if result.stderr.strip():
                dbg("stderr: " + result.stderr.strip())
            dbg("matched refs:\n" + found if found else "no matching refs returned")

        if not found:
            opt = "--" + param.name.replace("_", "-") + "-git-repo"
            raise click.BadParameter(
                colorize_error(
                    f"git ref '{value}' was not found in"
                    f" {DeployCommand.redact_repo(repo)}."
                    " Pass a valid tag, branch, or commit, or 'no' to skip."
                    f" To install from a different repository (a fork or an internal"
                    f" one), pass {opt} <repo url>, or give the ref as"
                    " <repo url>@<ref>."
                ),
                ctx=ctx, param=param,
            )

        dbg(f"ref '{value}' OK")
        return value

    def param_index(self, param_name):
        """
        Return index of parameter with given name.
        Useful for inserting new parameters at a specific position.
        """
        return list(
            filter(
                lambda param: param[1].name == param_name,
                enumerate(self.params),
            )
        )[0][0]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # add common options

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--debug/--no-debug",),
                default=os.environ.get("DEBUG", "0") == "1",
                show_default=True,
                help="Enable debug output.",
            ),
        )

        # --prefix
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--prefix",),
                default=config["default_prefix"],
                show_default=True,
                help="Prefix for all cloud resources.",
            ),
        )

        # --from-image/--not-from-image
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--from-image/--not-from-image",),
                default=False,
                show_default=True,
                help="Deploy from pre-built image, from bare OS otherwise.",
            ),
        )

        # --in-china
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--in-china",),
                type=click.Choice(["auto", "yes", "no"]),
                prompt=False,
                default="auto",
                show_default=True,
                help="Is deployment in China? (Local mirrors will be used.)",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--deployment-name", "--dn"),
                prompt=colorize_prompt(
                    '* Deployment Name (lower case letters, numbers and "-")'
                ),
                default=randomname.get_name,
                callback=DeployCommand.deployment_name_callback,
                show_default="<randomly generated>",
                help="Name of the deployment. Used to identify the created cloud resources and files.",
            ),
        )

        # ingress cidr blocks
        help = (
            "CIDR blocks for ingress traffic on the created VM, "
            + f'comma separated. Type "myip" to use your public IP ({get_my_public_ip(verbose="--debug" in sys.argv or os.environ.get("DEBUG", "0") == "1")}). '
            + "Add /8, /16, or /24 to specify the subnet mask."
        )
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ingress-cidrs",),
                default=config["default_ingress_cidrs"],
                show_default=True,
                type=str,
                help=help + ".",
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.ingress_cidrs_callback,
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--existing",),
                type=click.Choice(
                    ["ask", "repair", "modify", "replace", "run_ansible"]
                ),
                default="ask",
                show_default=True,
                help="""What to do if deployment already exists:
                \n* 'repair' will try to fix broken deployment without applying new user parameters.
                \n* 'modify' will update user selected parameters and attempt to update existing cloud resources.
                \n* 'replace' will attempt to delete old deployment's cloud resources first.
                \n* 'run_ansible' will re-run Ansible playbooks.""",
            ),
        )

        # --isaacsim-git-repo / --isaaclab-git-repo / --isaaclab-arena-git-repo
        # Install a component from a fork or an internal repo instead of the public
        # default (NVBugs 6696514). Declared before the ref options below so the repo is
        # known when the ref is validated (click parses options in declaration order).
        # Not prompted: the default (public repo) is right for almost every deploy.
        for opt_name, cfg_key, app in (
            ("--isaacsim-git-repo", "isaacsim_git_repo", "Isaac Sim"),
            ("--isaaclab-git-repo", "isaaclab_git_repo", "Isaac Lab"),
            ("--isaaclab-arena-git-repo", "isaaclab_arena_git_repo", "Isaac Lab Arena"),
        ):
            self.params.insert(
                len(self.params),
                click.core.Option(
                    (opt_name,),
                    default="",
                    show_default=f"{config[cfg_key]}",
                    # eager so the repo is known before the ref option is validated,
                    # whatever order the two were given in on the command line
                    is_eager=True,
                    callback=DeployCommand.git_repo_callback,
                    help=f"Git repository to install {app} from. Defaults to"
                    f" {config[cfg_key]}. Use this (or the <repo url>@<ref> form) to"
                    " deploy from a fork or an internal repository. A private"
                    " repository must be reachable from the deployed instance.",
                ),
            )

        # --isaacsim
        help = ('Install Isaac Sim? Valid values: "latest" (newest release), "no", a git ref at https://github.com/isaac-sim/IsaacSim, or "<repo url>@<ref>"'
                + ' to use a fork or an internal repository')
        self.params.insert(
            len(self.params),
            _IsaacRefOption(
                ("--isaacsim",),
                help=help,
                default=config["default_isaacsim_git_checkpoint"],
                show_default=True,
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.git_ref_callback,
            ),
        )

        # --isaaclab
        help = ('Install Isaac Lab? Valid values: "latest" (newest release), "no", a git ref at https://github.com/isaac-sim/IsaacLab, or "<repo url>@<ref>"'
                + ' to use a fork or an internal repository')
        self.params.insert(
            len(self.params),
            _IsaacRefOption(
                ("--isaaclab",),
                help=help,
                default=config["default_isaaclab_git_checkpoint"],
                show_default=True,
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.git_ref_callback,
            ),
        )

        # --isaaclab-arena
        help = ('Install Isaac Lab Arena? Valid values: "latest" (newest release), "no", a git ref at https://github.com/isaac-sim/IsaacLab-Arena, or "<repo url>@<ref>"'
                + ' to use a fork or an internal repository')
        self.params.insert(
            len(self.params),
            _IsaacRefOption(
                ("--isaaclab-arena",),
                help=help,
                default=config["default_isaaclab_arena_git_checkpoint"],
                show_default=True,
                prompt=colorize_prompt("* " + help),
                callback=DeployCommand.git_ref_callback,
            ),
        )

        # --demos
        demo_names = ", ".join(sorted(config["demos"].keys()))
        help = (
            'Out-of-the-box demos to install as desktop shortcuts. Valid values: "no", '
            + f"or a comma-separated list of: {demo_names}. "
            + "A demo auto-enables the apps it depends on (e.g. Isaac Sim / Isaac Lab)."
        )
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--demos",),
                help=help,
                default=config["default_demos"],
                show_default=True,
            ),
        )

        # [DEV]
        # private git repo for Isaac Lab
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--isaaclab-private-git",),
                default="",
                help="[DEV] Private git repo for Isaac Sim Lab.",
                hidden=True,
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--vnc-password",),
                default=lambda: pwgen(10),
                help="Password for VNC access to DRIVE Sim/Isaac Sim/etc.",
                show_default="<randomly generated>",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--system-user-password",),
                default=lambda: pwgen(10),
                help="System user password",
                show_default="<randomly generated>",
            ),
        )

        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ssh-port",),
                default=config["default_ssh_port"],
                help="SSH port for connecting to the deployed machines.",
                show_default=True,
            ),
        )

        # --ssh-user
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--ssh-user",),
                default=config["default_ssh_user"],
                help="OS username on the deployed instances.",
                show_default=True,
            ),
        )

        # --upload/--no-upload
        self.params.insert(
            len(self.params),
            click.core.Option(
                ("--upload/--no-upload",),
                prompt=False,
                default=True,
                show_default=True,
                help=f"Upload user data from \"{config['uploads_dir']}\" to cloud "
                + f"instances (to \"{config['default_remote_uploads_dir']}\")?",
            ),
        )
