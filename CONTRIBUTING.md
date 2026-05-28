# Contributing to LisHABM

Thanks for your interest in contributing! LisHABM is a small academic
project maintained by a two-person team, so this guide is short on purpose:
just enough to keep the codebase consistent and the workflow predictable.

If anything here is unclear or out of date, open an issue or a PR.

## Code of Conduct

This project follows our [Code of Conduct](./CODE_OF_CONDUCT.md).
By participating you are expected to uphold it. Report concerns
to [antonio.mf97@gmail.com](mailto:antonio.mf97@gmail.com).

---

## 1. Development setup

```bash
git clone https://github.com/antoniomf97/LisHABM.git
cd LisHABM

python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pre-commit install
```

The last command installs the pre-commit hooks, which run automatically on
every `git commit`. They handle trailing whitespace, end-of-file fixing,
YAML validation, merge-conflict markers, and Ruff lint + format.

To run all hooks manually against every tracked file:

```bash
pre-commit run --all-files
```

---

## 2. Code style

The project uses **[Ruff](https://docs.astral.sh/ruff/)** for linting and
formatting, configured in [pyproject.toml](pyproject.toml):

- Line length: **100**
- Lint rules: `E` (pycodestyle errors), `F` (pyflakes), `I` (import sorting)

Run locally:

```bash
ruff check .
ruff format .
```

Pre-commit will do this for you, but running it manually is faster while
iterating.

---

## 3. Type checking

The package is type-checked with **mypy** in `strict` mode (see
`[tool.mypy]` in `pyproject.toml`). All new code in `engine/` and
`orchestration/` should pass:

```bash
mypy
```

Tests are exempt from `disallow_untyped_defs`, so test helpers don't need
exhaustive annotations.

---

## 4. Tests

Tests are written with **pytest** and split into two layers:

- [tests/unit/](tests/unit/) — fast, isolated, no I/O or external deps
- [tests/integration/](tests/integration/) — exercise multiple modules
  together, may read/write `data/` fixtures

Run everything:

```bash
pytest
```

Run a single file or test:

```bash
pytest tests/unit/test_clock.py
pytest tests/unit/test_clock.py::test_advances_by_one_tick
```

**Please add tests for any new functionality.** A unit test for new logic
and, where relevant, an integration test that exercises the module's public
surface.

---

## 5. Commit signing

All commits to this repository must be **cryptographically signed** with
SSH. If you don't yet have an SSH key, generate one (skip this step if you
already have an `~/.ssh/id_ed25519` you want to reuse):

```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```

Accept the default path (`~/.ssh/id_ed25519`) and optionally set a
passphrase. This produces two files:

- `~/.ssh/id_ed25519`     — your **private** key (never share)
- `~/.ssh/id_ed25519.pub` — your **public** key (safe to share)

Then configure Git to sign with it:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

Add the public key as a **signing key** in your GitHub account: *Settings
→ SSH and GPG keys → New SSH key → Key type: "Signing Key"*. Paste the
full contents of `~/.ssh/id_ed25519.pub`.

**Optional:** For local verification of signatures (`git log --show-signature`), maintain
an `~/.ssh/allowed_signers` file with one line per trusted signer:

```
your.email@example.com ssh-ed25519 AAAA...full-key-blob
```

and point Git at it:

```bash
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
```

> **Important:** the key blob in `allowed_signers` must be **byte-identical**
> to the one in your `.pub` file (no truncation, no CRLF endings).

---

## 6. Branch and PR workflow

We use a simple **feature-branch + pull request** model:

1. **Create a branch** off `master`. We use the convention
   `<your_initials>/<short-description>` so it's always clear who owns a
   branch:
   ```bash
   git checkout -b af/market-clearing
   git checkout -b rd/scheduler-deadlock
   git checkout -b af/contributing-guide
   ```

2. **Commit in small, signed, logical units.** Each commit message should
   make sense on its own. A reasonable shape:

   ```
   Short, imperative subject (max ~72 chars)

   Optional body explaining the *why*, wrapped at ~80 chars. The diff
   already shows the *what*.
   ```

3. **Push and open a PR** against `master`. The [PR template](.github/pull_request_template.md)
   asks for a summary, testing notes, and a short checklist. Please fill
   them in.

4. **Get a review.** Because of [CODEOWNERS](.github/CODEOWNERS), the other maintainer is auto-requested. At least one approval is required before merge. Address review comments with follow-up commits (don't force-push during review, it makes re-review harder).

5. **Merge.** Squash-merge is preferred for small PRs (keeps `master` linear
   and readable); regular merge commits are fine for larger feature branches with meaningful intermediate history.

6. **Delete the branch** after merging.

Direct pushes to `master` should be avoided, even for "tiny" changes. You must run them through a PR to keep CI and review consistent.

---

## 7. Reporting issues

The repository provides four issue templates under
[`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/):

- **Bug report** - something is broken or behaves unexpectedly
- **Feature request** - a new capability or enhancement
- **Documentation report** - missing, wrong, or unclear docs
- **Infrastructure report** - tooling, CI, build, packaging

Please pick the closest one rather than opening a blank issue. For
open-ended questions or design discussion, use
[GitHub Discussions](https://github.com/antoniomf97/LisHABM/discussions)
instead of an issue.

