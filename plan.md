# Plan — artificial demographics module and per-module config files

- **Baseline.** Written against `antoniomf97/LisHABM` at `eddd0a4` (2026-10-07). The local `initialize_scenario` change is not pushed, so check `engine/core/simulator.py` before PR 6.
- **Status.** Nothing in this plan has been implemented or run.
- **Ground rules.** CLAUDE.md applies throughout: git read-only, no invented Lisbon values, and "done" means `uv run pytest` and `uv run pre-commit run --all-files` pass.

## Maintainer sign-off

CLAUDE.md requires approval before these changes. Tick them before starting the PRs that need them.

- [ ] Config schema and loader: per-module config files and a variant tag (PR 1, PR 2)
- [ ] `engine/core/agents.py`: `Person.sex` and `Person.partner`, plus regenerating `BaselineScenario.pkl` (PR 3)
- [ ] Passing `months_per_tick` to domain modules, as the one exception to "each module receives only its own config slice" (PR 4)

## Decisions

1. **Tick length.** One tick is a hyperparameter, `sim.months_per_tick`, defaulting to 3. Module rates are annual and converted per tick.
2. **Config split.**
   - The run config holds `runs`, `sim`, `scenario` and `output`.
   - Each module's settings live in their own file, `configs/<module>/<variant>.yaml`. The run config names the file: `demographics: artificial` loads `configs/demographics/artificial.yaml`.
   - Each variant has its own schema, tagged by a `model` field. A future data-driven demographics variant can then have different parameters without touching this one, and other modules are unaffected.
3. **This module is artificial.** Its rates and rules are stylised assumptions, not calibrated to data. All values in its config file are placeholders.
4. **Initial population.** The synthetic generator produces households with couples, families and parent–child links already set. The module only evolves them.
5. **Adult children.** A child who turns adult keeps `income=0.0` and cannot leave home until their income meets the leave-home rule.
6. **Sex.** `Person` gets a `sex` field.

## Scope

The module changes household composition through ageing, death, birth, separation, leaving the parental home, and partnership (moving in together).

Out of scope:

- **Finding a house.** New households start with `living_house=None` and become demand for the market module.
- **Income and employment.**
- **Inheritance.**
- **Migration.**
- **Moving the generation recipe** to `configs/scenarios/` and generating the population at run time. That was discussed but not decided.

## Config design

### Run config, `configs/config_template.yaml`

```yaml
engine:
  sim:
    n_ticks: 100000
    seed: 42
    months_per_tick: 3      # length of one tick in months
  scenario: {...}           # unchanged
  demographics: artificial  # -> configs/demographics/artificial.yaml
  construction:             # stays inline until it has variants
    enabled: true
  market:
    enabled: true
  output: {...}             # unchanged
```

### Loader, `orchestration/config.py`

`load_config` resolves module references before validation:

- For each of `demographics`, `construction` and `market` under `engine`:
  - A **string** value is a variant name. Load `<run config's directory>/<module>/<name>.yaml` and put the mapping in its place.
  - A **mapping** is used as is. Tests and inline configs keep working.
- Then validate the whole `RunConfig` once, as today.

Notes:

- **Resolve against the run config file's directory, not the cwd.** That way `configs/baseline.yaml` finds `configs/demographics/…`, and tests can use `tmp_path`.
- **Error messages.** A missing module file raises an error naming the module, the variant and the path it tried. An empty file raises the same "config file is empty" error the loader uses today.
- **Single reader.** `orchestration/config.py` stays the only YAML reader. The engine still receives a validated, typed `EngineConfig`.

### Schema, `engine/config.py`

```python
class SimConfig(BaseModel):
    n_ticks: int = 1000
    seed: int = 42
    months_per_tick: int = Field(default=3, gt=0)


class AgeBandRate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min_age: int = Field(ge=0)
    max_age: int = Field(ge=0)            # inclusive
    rate: float = Field(ge=0.0, le=1.0)   # annual probability


class ArtificialDemographicsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["artificial"] = "artificial"
    enabled: bool = True
    adult_age: int = Field(default=18, ge=0)
    mortality: dict[Literal["F", "M"], list[AgeBandRate]] = Field(default_factory=dict)
    fertility: list[AgeBandRate] = Field(default_factory=list)
    female_birth_share: float = Field(default=0.5, ge=0.0, le=1.0)
    separation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    partnership: list[AgeBandRate] = Field(default_factory=list)
    max_partner_age_gap: int = Field(default=10, ge=0)
    leave_home: list[AgeBandRate] = Field(default_factory=list)
    min_income_to_leave: float = Field(default=0.0, ge=0.0)


# One variant today. A second variant turns this into
# Annotated[ArtificialDemographicsConfig | OtherConfig, Field(discriminator="model")].
DemographicsConfig = ArtificialDemographicsConfig
```

- **`EngineConfig.demographics`** keeps the type `DemographicsConfig` and defaults to `ArtificialDemographicsConfig()`. That keeps `tests/unit/test_engine_config.py:18` and the name used in CLAUDE.md valid.
- **Validators.** A model validator rejects any band with `min_age > max_age`, and overlapping bands within one list or within one sex.
- **`extra="forbid"`** on the new models means a misspelt key in a module file is an error. The existing config models don't set it, so unknown keys there are silently dropped. That is noted below as out of scope.
- **An empty list switches that event off.** The defaults therefore change nothing.

### Variant file, `configs/demographics/artificial.yaml`

```yaml
# Artificial demographics: stylised rules, not calibrated to data.
# Every rate is an ANNUAL probability in [0, 1], by age band (min_age and
# max_age inclusive, whole years). Bands in a list must not overlap. An age
# outside every band gets rate 0, and an empty list switches the event off.
# ALL VALUES ARE PLACEHOLDERS. 0.0 means the event is off.
model: artificial
enabled: true
adult_age: 18

# Death, by sex. Bands must cover every age that occurs (e.g. 0–120), or
# people outside them never die.
mortality:
  F:
    - {min_age: 0, max_age: 120, rate: 0.0}   # PLACEHOLDER
  M:
    - {min_age: 0, max_age: 120, rate: 0.0}   # PLACEHOLDER

# Birth: annual probability for EVERY woman in the band.
fertility:
  - {min_age: 15, max_age: 49, rate: 0.0}     # PLACEHOLDER
female_birth_share: 0.5                       # PLACEHOLDER

# Separation: annual probability per couple.
separation_rate: 0.0                          # PLACEHOLDER

# Partnership: annual probability that a single adult not living with a
# parent enters the partner pool.
partnership:
  - {min_age: 18, max_age: 120, rate: 0.0}    # PLACEHOLDER
max_partner_age_gap: 10                       # PLACEHOLDER

# Leaving home: annual probability for an adult living with a parent whose
# income is > 0 and >= min_income_to_leave.
leave_home:
  - {min_age: 18, max_age: 120, rate: 0.0}    # PLACEHOLDER
min_income_to_leave: 0.0                      # PLACEHOLDER, € per year
```

## Modelling assumptions

Each assumption goes into the module docstring.

1. **Annual to per-tick.** `p_tick = 1 - (1 - p_year) ** (months_per_tick / 12)`, assuming a constant hazard within the year.
2. **Ageing.** Ages are whole years. Each step adds `floor(months_after / 12) - floor(months_before / 12)` years to everyone, where `months_before = tick * months_per_tick`. This works for any tick length, and all birthdays are synchronised (Q1).
3. **Sex** is `Literal["F", "M"]`.
4. **Event order within a step:** ageing → death → birth → separation → leaving home → partnership → clean-up.
5. **Death.** A per-sex probability by age band. The person is removed from their household and unlinked from their partner, parents and children.
6. **Birth.**
   - A probability by age band, applied to every woman in the band, with at most one birth per woman per tick.
   - The newborn joins the mother's household, with sex drawn from `female_birth_share`, `income=0`, `capital=0`, `education=1` and the mother's `nationality`.
   - The newborn is linked to the mother, and to her partner if she has one.
7. **Separation.**
   - A probability per couple. The leaving partner is chosen with `rng` and forms a new household with `living_house=None`.
   - Children, the house, contracts and mortgages stay with the remaining household.
8. **Leaving home.**
   - Eligible: adults living with a parent who have `income > 0` and `income >= min_income_to_leave`. Each eligible adult leaves with a probability by age band and forms a new household with `living_house=None`.
   - Nobody is eligible until something gives adult children income (Q2).
9. **Partnership.**
   - **Pool.** Single adults who don't live with a parent; each enters with a probability by age band.
   - **Matching.** Shuffle the pool with `rng` in list order, then pair greedily, opposite-sex (Q5), within `max_partner_age_gap`. Unmatched agents drop out of the pool for this tick.
   - **Which household the pair joins.** If exactly one partner's household owns the house it lives in, the other moves there. Otherwise the destination is chosen with `rng`.
   - The mover's children come along. The mover's old household dissolves if it is left empty.
10. **Clean-up.** Recompute `Household.income` and `Household.capital` as sums over members (Q4). Report households left with no members as dissolved.

## Code layout

```
engine/modules/demographics/
  __init__.py      exports ArtificialDemographics, DemographicsResult
  artificial.py    ArtificialDemographics(config: ArtificialDemographicsConfig, months_per_tick: int)
                   .step(households: list[Household], tick: int, rng: random.Random) -> DemographicsResult
                   DemographicsResult(NamedTuple): new: list[Household], dissolved: list[Household]
                   annual_to_tick(p: float, months_per_tick: int) -> float
                   one module-level function per event
```

- **Randomness.** All randomness comes from the `rng` argument, which is `Simulator.rng`.
- **Iteration order.** Iterate households and pools in list order. Never sort or key ordering by id.
- **Picklability.** The class holds only its config and `months_per_tick`, so it stays picklable.
- **Agent references.** Never print, log or interpolate an agent; use `.id`. Agents are unhashable, so key dicts and sets by `.id`.
- **Choosing the implementation.** With one variant, the Simulator constructs `ArtificialDemographics` directly. A lookup on `config.demographics.model` is added only when a second variant exists.

## PR sequence

Each PR updates the CLAUDE.md lines it makes false.

1. **Tick length.**
   - Add `SimConfig.months_per_tick` and the template entry.
   - Add a validation test (`0` and negative values rejected) in `tests/unit/test_engine_config.py`.
   - Replace CLAUDE.md's "Undecided: the time unit of a tick" with the decision.
2. **Per-module config files.**
   - In the loader: resolve module references.
   - In `engine/config.py`: add `AgeBandRate`, `ArtificialDemographicsConfig`, the `DemographicsConfig` alias and the validators.
   - Add `configs/demographics/artificial.yaml`. The template references it by name.
   - Tests, in `tests/unit/test_orchestration_config.py`:
     - a name resolves to the module file
     - an inline mapping still works
     - a missing module file gives an error naming the path
   - Tests, in `tests/unit/test_engine_config.py`:
     - overlapping bands are rejected
     - `min_age > max_age` is rejected
     - an unknown key in the module config is rejected
     - `model` defaults to `"artificial"`
   - CLAUDE.md updates:
     - Architecture: describe the config layout.
     - Code conventions: module parameters go in the variant's schema and are mirrored in `configs/<module>/<variant>.yaml`.
     - Mismatches: the template's `scenario.path` entry is unchanged.
3. **Agents, generator and pickle.**
   - `engine/core/agents.py`: add `Person.sex: Literal["F", "M"]` and `Person.partner: Person | None = None`.
   - `data/input/synthetic/datageneration.py`:
     - draw each person's sex
     - link the two adults of two-adult archetypes as partners, opposite-sex (Q5)
     - set `parents` and `children` between adults and the children of their household
     - draw children's ages consistent with their parents' ages (see the defect below)
   - Add any new recipe parameters to `BaselineScenarioConfig.yaml` as placeholders.
   - Regenerate `BaselineScenario.pkl` with the `datagen` extra. Old pickles lack the new attributes after unpickling.
   - Add an integration test in `tests/integration/` that loads the pickle and checks:
     - partner links are symmetric
     - parent and child links are symmetric
     - every child is younger than each of its parents by at least a minimum gap
   - Update CLAUDE.md's agent-models section.
4. **Module part 1: ageing, death, birth,** plus `annual_to_tick` and `DemographicsResult`, with tests.
5. **Module part 2: separation, leaving home, partnership,** plus household creation and dissolution, with tests.
6. **Wiring.**
   - `Simulator` builds `ArtificialDemographics(config.demographics, config.sim.months_per_tick)` when the module is enabled.
   - `Simulator.step` calls it first, then appends `new` and drops `dissolved` by id from the Simulator's household list.
   - Add a simulator test.
   - Update CLAUDE.md's Status section.

PRs 1 and 3 are independent. PR 2 needs PR 1 only for the template. PRs 4 and 5 need PRs 2 and 3.

## Tests

The module tests go in `tests/unit/test_engine_demographics.py`, using new `make_person` and `make_household` factory fixtures in `tests/conftest.py`.

- **`annual_to_tick`:** 0 maps to 0, 1 maps to 1, and with 12 months per tick it returns `p` unchanged.
- **Ageing:** happens exactly on year boundaries with 3, 5 and 12 months per tick.
- **Rate extremes:** rate 0 produces no events. Rate 1 makes every eligible agent experience the event.
- **Determinism:** same seed and same households give an identical outcome. Compare by structure (ages, sexes, household sizes, links), not by ids.
- **Invariants after a multi-tick run with non-zero rates:**
  - each person is in exactly one household
  - partner links are symmetric
  - parent and child links are symmetric
  - no household is empty
  - household aggregates equal the sums over members
- **Leaving home:** never happens for `income == 0`.

## Defects found (fix only where listed)

- **Child ages in the generator.** `datageneration.py` draws each child's age as `uniform(0, 18)`, independently of the parents. A 25-year-old single parent can get a 17-year-old child. Fixed in PR 3.
- **Unknown config keys are dropped.** The existing config models (`SimConfig`, `ScenarioConfig`, `ConstructionConfig`, `MarketConfig`, `OutputConfig`, `RunsConfig`) don't set `extra="forbid"`, so unknown YAML keys are dropped without error. The new models in PR 2 forbid them. The old ones are out of scope.

## Open questions

1. **Ageing.** Are synchronised birthdays acceptable, or should `Person` get a `birth_month`?
2. **Income.** What gives adult children income? Is it this module, a separate income/labour module, or nothing for now? And should "enough to pay rent" stay a fixed `min_income_to_leave`, or become an affordability check by the market module?
3. **Assets of dissolved households.** When a household dissolves through death, who gets its houses, contracts and mortgages? And what happens when only minors remain?
4. **Capital.** Which is authoritative: `Household.capital`/`income`, or the members' values? They will diverge once the market moves money.
5. **Couples.** Opposite-sex only, or also same-sex, in the generator and in matching?
6. **Initial population across runs.** Should all runs share one initial population, seeded by the recipe, or should each run draw its own from the run seed?
