# LisHABM — Lisbon Housing Market Agent-Based Simulation

An agent-based model (ABM) of the Lisbon housing market, built for academic
research into housing dynamics, demographics, and construction. LisHMABS
simulates the interactions between households, dwellings, developers, and
market mechanisms over time, with the aim of supporting policy analysis and
exploratory scenario work.

> **Status:** early development (v0.1.0). The project structure and tooling
> are in place; the simulation modules themselves are under active design.
> Expect breaking changes.

## Requirements

- Python **3.11** or newer
- [Git](https://git-scm.com/) (for development and contributions)

## Installation

Clone the repository and install in editable mode with the development
extras:

```bash
git clone https://github.com/antoniomf97/LisHABM.git
cd LisHABM

uv sync --extra dev
```

This creates a `.venv` and installs the `lishabm` package, plus the
development tools used by the project: `pytest`, `ruff`, and `pre-commit`.
`uv run <command>` runs a command inside that environment without needing
to activate it.

## Usage

Run a simulation from a config file under
[configs/simulation/](configs/simulation/), either by name or by path:

```bash
uv run lishabm config_template
# equivalent:
uv run python main.py configs/simulation/config_template.yaml
```

A config describes how many runs to repeat (`runs.n_runs`), on how many
worker processes (`runs.n_workers`), and the engine settings every run
shares — number of ticks, RNG seed, and where the initial scenario (real or
synthetically generated) comes from. Copy
[configs/simulation/config_template.yaml](configs/simulation/config_template.yaml)
to start a new one; every field is validated on load.

> As the status note above says, the simulation modules are still stubs: a
> run currently just advances a clock and returns the finished runs in
> memory, without writing anything to [data/output/](data/output/) yet.

## Running the tests

```bash
uv run pytest
```

Tests live under [tests/](tests/), split into [tests/unit/](tests/unit/) and
[tests/integration/](tests/integration/).

## Project layout

```
LisHABM/
├── engine/              # Simulation engine
│   ├── core/            #   Engine internals (time, state, agents)
│   ├── io/              #   Input loaders and output writers
│   ├── modules/         #   Domain modules
│   │   ├── construction/
│   │   ├── demographics/
│   │   └── market/
│   └── parallel/        #   Intra-run parallel execution
├── orchestration/       # Sweeps and scheduling across runs
│   └── scheduler/
├── configs/             # Configuration files
│   ├── simulation/      #   Run configs (`lishabm <name>`)
│   └── generator/       #   Data-generation recipes
├── data/
│   ├── input/           #   Input datasets
│   └── output/          #   Simulation outputs
├── scripts/             # Helper scripts (one-off / utility)
└── tests/               # Unit and integration tests
```

## Contributing

Contributions, bug reports, and ideas are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards,
the branch/PR workflow, and commit signing requirements.

For open-ended questions or discussion, use the project's
[GitHub Discussions](https://github.com/antoniomf97/LisHABM/discussions).

## License

LisHABM is distributed under the **GNU General Public License v3.0 or
later** (GPL-3.0-or-later). See [LICENSE](LICENSE) for the full text.

## Authors

- António Ferreira ([@antoniomf97](https://github.com/antoniomf97))
- Regina Duarte ([@ReginaBDuarte](https://github.com/ReginaBDuarte))
