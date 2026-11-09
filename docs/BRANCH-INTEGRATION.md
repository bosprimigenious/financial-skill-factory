# Branch integration: Financial Skill Factory V2

## Source repositories and refs

- Primary financial implementation: `bosprimigenious/financial-skill-factory@v2`
- Batch-pipeline implementation: `bosprimigenious/expert-task-pipeline@feature/financial-skill-factory-v2`
- Integration target: `bosprimigenious/financial-skill-factory@integration/expert-task-pipeline-v2`

These branches are in **different GitHub repositories** and do not share a branch ancestry. A native same-repository branch merge is therefore not possible. This integration ports the compatible source components into the Financial Skill Factory V2 repository while preserving its history and existing V2 architecture.

## Kept as canonical from Financial Skill Factory V2

- `case_intake/`: source authenticity, provenance and PII gates.
- `task_architect/`: Skill mapping and decision-DAG complexity.
- `generators/`: separate Prompt, Ideal Steps, Golden Response and Rubric builders.
- `generators/isolation.py`: executable GT/Rubric input-isolation assertions.
- `financial_verifiers/`: the V2 Decimal-based financial verifiers, including TCA, Carry waterfall and Implementation Shortfall.
- `evaluation/`: Rubric QA, mutation testing, blind-run record and current difficulty preflight.
- `quality_gates/`: external-evidence-driven Xpert readiness.
- `registry/difficulty_rule.yaml`: FDE 11.4 `combine: all` rule.

These are not overwritten by older or overlapping code from the other repository.

## Ported from expert-task-pipeline

- `finance/skill_registry.json`: captured platform Task ID → L2/L3 mapping.
- `finance/domain_catalog.json`: professional domain objects, inputs, decisions, controls, deliverables, failure modes and policy parameters.
- `finance/batch/selected_tasks.json`: eight selected tasks and their exact platform identifiers.
- `tools/new_task.py`: case scaffold generator, now cross-checking the project's submitted-skill reservation ledger.
- `tools/package_batch.py`: 8-package + master packager with fail-closed AUTHOR release checks.
- `tests/test_financial_batch_pipeline.py`: batch registry, scaffold and release-gate tests.

## Deliberately not copied

- The source branch's POWER-PERF example corpus and its reference answers/evidence. Those are case-specific legacy artifacts and are not required to integrate the financial factory; copying them would unnecessarily mix a separate power-sector benchmark into the finance repository.
- The source branch's older generic/POWER-PERF `grader.py`, `schema_preflight.py` and `score_with_preflight.py`. V2 already has its own financial verifiers, schema and Xpert readiness layers.
- Duplicate financial calculation kernels from the source branch. V2's existing `financial_verifiers/` already implements the overlapping TCA, Carry and execution-shortfall logic and remains canonical.
- Conflicting root README, LICENSE and .gitignore files. The Financial Skill Factory V2 repository remains canonical for these project-level files.

## Current FDE 11.4 difficulty gate

Release requires both:
1. platform Judge internal quality-check score <= 50;
2. platform-published single-round model-call steps >= 50.

Runtime is rating metadata only. It cannot substitute for steps. The older `score <= 50 AND (steps >= 50 OR time > 2400s)` rule is historical only.

## Upgrade commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install openpyxl

make v2-test
make batch-test
make batch-scaffold
```

Scaffolds are created under `work/financial-eight/cases/`, and archives under `dist/financial-eight/`. They do not overwrite the existing `cases/<platform-task-id>/` source-material registry.

For final packaging:

```bash
make batch-release
```

This command must fail until every case has the required accepted materials, author qualification, current platform Skill verification, independent Reference/Grader, verified Rubric, C20 calibration, official Doubao 2.1 Pro run evidence, Judge <= 50 and official single-round steps >= 50.

## Integration status

This branch is a compatibility integration candidate. It is not merged into `v2` until automated tests and clean-clone verification pass. No Doubao run or Xpert platform acceptance is implied by GitHub CI.
