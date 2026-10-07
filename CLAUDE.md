<!--
Maintainers: Claude Code loads this file into every session in this repo, for everyone on the team.
- Keep it under 200 lines. Every line must be concrete and checkable against the code.
- When a change makes a line false (status, data, mismatch list), fix that line in the same PR.
- Personal preferences go in CLAUDE.local.md (add it to .gitignore) or ~/.claude/CLAUDE.md, not here.
Claude Code strips this comment before the file reaches the model.
-->

# CLAUDE.md — LisHABM

## Role and working rules

You are a senior software developer on this team, focused on Python. These rules apply to every reply and every change.

- **Be efficient with code.** Make the smallest change that fully solves the task. Reuse what exists (config models, `tests/conftest.py` fixtures, the standard library) before writing anything new. No speculative abstractions, options or dependencies. Leave code outside the task untouched: no drive-by refactors, renames, reformatting or comment edits.
- **Be efficient with usage.** Read only the files the task needs, search before opening, run the narrowest test first, and don't repeat a read or a check whose inputs haven't changed. No subagents unless asked.
- **Be concise.** Lead with the answer or the result. No preamble, no restating the request, no recap of what the diff already shows, no closing offers.
- **Be direct and precise.** Give exact names, `path:line`, commands and numbers. Say what you ran and what you did not run. If you don't know, say so. Never guess.
- **Don't propose ideas unless asked.** No unrequested features, refactors, alternatives or next steps. Defects are not ideas: if a bug, failing check, doc/code mismatch or ambiguous requirement affects the task, report it in one line and leave anything out of scope unfixed.
- **Ask instead of assuming** when a requirement is ambiguous or a change would cross a boundary listed below. One question, then wait.

## Project

Agent-based model of the Lisbon Metropolitan Area housing market (households, houses, constructors, sale and rental markets), for academic research and policy/scenario analysis. Repo `github.com/antoniomf97/LisHABM`, distribution `lishabm` v0.1.0, GPL-3.0-or-later. **Early stage:** the config → scheduler → simulator plumbing works; the model itself is stubs. Expect breaking changes.

- The importable packages are top-level `engine` and `orchestration`. There is no `lishabm` module: that name is only the distribution and the CLI.
- `HousingMarketABM` (Julia, Agents.jl, `github.com/Couves-alcatifa/HousingMarketABM`) is a separate, earlier model of the same market. This file does not describe it.

## Commands

Run everything from the repo root: config names and data paths resolve against the cwd.

```bash
python -m venv .venv                 # activate: .venv\Scripts\Activate.ps1 (PowerShell) | source .venv/bin/activate
pip install -e ".[dev]" numpy        # numpy: used only by the data generator, not declared in pyproject
pre-commit install

pytest                               # all tests
pytest tests/unit/test_engine_simulator.py::test_step_advances_clock_by_one
ruff check . && ruff format .        # rules E, F, I; line length 88
mypy                                 # strict; checks engine/ and orchestration/ only
pre-commit run --all-files           # what CI runs: whitespace, yaml, ruff, ruff-format, mypy

lishabm config_template              # config name -> configs/<name>.yaml
python main.py configs/config_template.yaml   # same, explicit path
```

- Venv not active: call its interpreter, e.g. `.venv/Scripts/python -m pytest` (Windows) or `.venv/bin/python -m pytest`.
- With uv, use only `uv pip ...`. Never `uv sync`, `uv run` or `uv add`: they create `uv.lock`, and `uv sync` uninstalls undeclared packages (numpy).

**Done means** `pytest` and `pre-commit run --all-files` both pass.

- CI runs pre-commit on Python 3.11 and pytest on 3.11 and 3.13. Don't use syntax or stdlib features newer than 3.11, even when the local venv is newer.
- Pre-commit pins ruff v0.6.9 and mypy v1.11.0, while `.[dev]` installs the latest of both. If they disagree, pre-commit decides.
- The ruff hooks skip untracked files. For new files, also run `pre-commit run --files <paths>`.

## Architecture

```
configs/<name>.yaml
  -> orchestration/config.py          load_config() -> RunConfig{runs: RunsConfig, engine: EngineConfig}
  -> orchestration/runner.py          run(), main() (CLI entry point `lishabm`)
  -> orchestration/scheduler/pool.py  run_all(): n_runs configs, seed = base seed + run index,
                                      multiprocessing.Pool (n_runs == 1 runs in-process)
  -> engine/core/simulator.py         Simulator(EngineConfig): Clock, random.Random(seed), step(), run()
       -> engine/io/scenario.py       load_scenario() -> Scenario(regions, households, houses, constructors)
       -> engine/modules/{demographics,construction,market}/   empty
```

Boundaries to keep:

- `engine/` never imports `orchestration/`. The Simulator sees only `EngineConfig`: no run name, run count or launch details.
- `orchestration/config.py` is the only place that reads run YAML.
- `engine/io/scenario.py` is the only place that tells real data from synthetic. Everything downstream receives a `Scenario`.
- Each domain module receives only its own config slice (`DemographicsConfig`, `ConstructionConfig`, `MarketConfig`).
- Reproducibility: all simulation randomness comes from `Simulator.rng`. Never use global `random.*` or `np.random.*` state. The same config must give the same set of runs.
- Windows starts pool workers with *spawn*: worker functions must be module-level, and everything a `Simulator` holds must be picklable (finished simulators are returned through the pool).

## Status (verified 2026-10-07 at `2311e7d`)

- **Working:** config schemas and YAML loader, CLI, multi-run scheduler, `Clock`, agent models, synthetic scenario generator (pickle output). Unit tests cover config, clock, simulator, scenario loader, runner and scheduler; none cover `agents.py` or the generator.
- **Stubs:** `Simulator.initialize_scenario` (loads the scenario, then discards it), `Simulator.step` (only advances the clock), `_read_real` and `_read_synthetic` (return an empty `Scenario`; `ScenarioConfig.path` is never read), the module configs (`enabled` only), `OutputConfig` (defined, unused).
- **Empty (`.gitkeep` only):** `engine/modules/*/`, `engine/parallel/`, `tests/integration/`, `scripts/`.
- **Missing, though the docs reference them:** `engine/io/output.py` (snapshot writer driven by `OutputConfig`) and `orchestration/assembler.py` (aggregation across runs). `run()` returns the finished simulators and `main()` discards them, so a run writes nothing.
- **Undecided:** the time unit of a tick. Don't build one in. If a change needs it, stop and ask.

## Agent models — `engine/core/agents.py`

Pydantic v2 models `Region`, `Person`, `Household`, `House`, `Contracts`, `Loan` and `Constructor`, linked into a cyclic object graph (`House.owner` ↔ `Household.houses`, `Contracts.tenant` / `landlord`, `Region.neighborhood`). Consequences:

- `model_dump()` and `model_dump_json()` fail on every linked agent (in the baseline: all but `Person` and `Constructor`) with `Circular reference detected`, or on freshly unpickled objects with `'MockValSer' object is not an instance of 'SchemaSerializer'` (the forward-referencing models are never `model_rebuild()`-ed). Persist with pickle or a flat, ID-based export.
- `repr()`, `str()` and `print()` raise `RecursionError` for every `Household`, `Contracts`, `Loan` and household-owned `House` in the baseline, and return 0.1–1.2 MB of text for a `Region`. Never print, log or interpolate an agent: use `.id` or `.name`.
- Agents are unhashable (non-frozen models). Use `.id` as the dict key or set member, never the object.
- `id` defaults to `uuid4()`, which is unseeded: a regenerated scenario gets new ids, and so does every agent created during a run. Results must not depend on id values (no sorting by id, no iterating a `set` of ids where order matters).
- Legacy names: `forSale` and `forRent` (camelCase), `remaining_morgtage` (typo), `Contracts` (plural), `Loan.tax_type` (means fixed or variable *rate*). Don't rename them: `BaselineScenario.pkl` is bound to these class paths and field names. A rename needs a maintainer's approval and a regenerated pickle.

## Data

- `data/input/synthetic/BaselineScenarioConfig.yaml`: the generation recipe (18 municipalities with adjacency, house typologies and prices, household archetypes, initial market assignment).
- `data/input/synthetic/datageneration.py`: the generator. It needs the editable install (it imports `engine`) and numpy. It draws from `np.random.Generator`, whereas the Simulator uses `random.Random`. Its output is deterministic for a given recipe, except for ids. `--format json` fails (`Scenario` is a `NamedTuple` with no `model_dump_json`) and leaves an empty file behind.
  ```bash
  python data/input/synthetic/datageneration.py --config data/input/synthetic/BaselineScenarioConfig.yaml \
      --outdir data/input/synthetic/scenarios --name BaselineScenario --format pickle
  ```
- `data/input/synthetic/scenarios/BaselineScenario.pkl`: committed, about 1 MB, holding 18 regions, 1000 households, 1200 houses and 3 constructors. Never hand-edit it; regenerate it. Nothing loads it yet.
- `data/output/`: the intended home of run outputs. Empty.

## Known doc/code mismatches (trust the code)

- `docs/architecture.md` and its diagram name `configs.py` (actual: `config.py`), and also `assembler.py`, `engine/io/output.py`, `data/generator.py` and `data/processor.py`, none of which exist.
- `configs/config_template.yaml`: `scenario.path: data/synthetic/baseline` does not exist (the data is under `data/input/synthetic/`). `output.dir: data/outputs` matches the `OutputConfig.dir` default, but the folder is `data/output/`.
- `BaselineScenarioConfig.yaml`: `investor_percentage: 0.5`, while its comment says 5%.
- `CONTRIBUTING.md`: the test examples use `tests/unit/test_clock.py` (actual: `test_engine_clock.py`), and the venv directory is `venv` (README and this file: `.venv`).

Mention a mismatch when it is relevant to the task. Don't fix one as a side effect. Remove its entry in the PR that fixes it.

## Code conventions

- Python 3.11 style: `X | None`, built-in generics, `pathlib.Path`. Keep paths OS-agnostic (Windows dev machines, Ubuntu CI).
- `engine/` and `orchestration/` are mypy-strict: annotate everything. Tests are not type-checked.
- Configs are Pydantic `BaseModel`s validated with constraints (`Field(gt=0)`, `Literal[...]`), not with manual checks.
- New config parameter: add a typed field with a default in `engine/config.py` (`orchestration/config.py` for run metadata), mirror it in `configs/config_template.yaml`, and add a validation test.
- New runtime dependency: add it to `[project].dependencies`. The mypy hook's environment holds only `pydantic` and `types-PyYAML` (`additional_dependencies` in `.pre-commit-config.yaml`), so any other import is `Any` there. Add the package or its stubs when its types matter.
- Match the existing style: module docstrings that explain *why*, `# ── Section ──` banners in larger files, LF line endings, 4-space indent (2 for YAML, TOML and JSON).
- This is research code. State every modelling assumption in the docstring and in the reply. Never invent Lisbon-specific empirical values: cite the source or mark the value as a placeholder.
- Keep changes small and reviewable. Ask before restructuring `engine/core/agents.py`, the config schema or the engine/orchestration boundary.

## Tests

- Layout: `tests/unit/test_<package>_<module>.py` (e.g. `test_engine_clock.py`). Plain `test_*` functions, no classes.
- Build configs with the `tests/conftest.py` fixtures, not by hand: `make_engine_config(n_ticks=, seed=, **overrides)`, `make_scenario_config(**overrides)`, `minimal_yaml`.
- Unit tests are fast and do no I/O beyond `tmp_path`. Integration tests (`tests/integration/`) exercise several modules together and may read `data/`.
- Every new piece of logic gets a test. Stochastic logic gets a fixed-seed determinism test.

## Git — read-only

- Run only read-only commands: `status`, `diff`, `log`, `show`, `blame`. Never `add`, `commit`, `switch -c`, `checkout -b`, `stash`, `reset`, `rebase`, `push` or `gh pr create`.
- Write commit messages and PR text only when asked. Commit: imperative subject of at most 72 characters, body explaining *why*. PR: follow `.github/pull_request_template.md`.
- Team workflow, for context: `master` is protected (PR with at least one approval; `.github/CODEOWNERS` auto-requests the maintainers), squash-merge, SSH-signed commits, branch names `<initials>/<short-desc>`.
