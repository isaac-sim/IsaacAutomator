# Development Guidelines

This repository the code for the terraform, ansible and packer. Guidelines might slightly differ, but have common parts.

## Formatting

- Please enable EditorConfig plugin in your editor and it'll take care of indentation and other basic formatting.
- Terraform files should be formatted with `terraform fmt`.
- Look at how thing are done in the existing code and follow the same style.

## GIT Guidelines

Use the following GIT workflow to keep history linear. First, check out a new branch:

```sh
git fetch -v -p origin
git checkout -b new-feature origin/master
```

Then, sync-up the code daily to stay up to date with the main branch:

```sh
git fetch -v origin
git rebase origin/master
git push origin +new-feature
```

If you have your own commits on master, do the following while pulling updates:

```sh
git pull --rebase origin/master
```

Make sure your branch is properly rebased on top of the current `origin/master` and has no merge commits.
