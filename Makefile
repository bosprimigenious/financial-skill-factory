PY ?= python3
VENV ?= vendor/financial-audit-bench/.venv
RUNPY = $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(PY))

.PHONY: test scan pack verify case help v2-test v2-smoke sample run fin8 batch-test batch-scaffold batch-release
help:
	@echo "make test   # run unit tests"
	@echo "make scan CASE=cases/<id>"
	@echo "make pack CASE=cases/<id>"
	@echo "make case   # 重建实例材料+GT（含逐格断言）"
	@echo "make verify # 题包机器校验"
	@echo "make v2-test # V2 全部测试"
	@echo "make v2-smoke # V2 八阶段冒烟（写 artifacts/v2-smoke.md）"
test:
	PYTHONPATH=src $(RUNPY) -m unittest discover -s tests -v
scan:
	PYTHONPATH=src $(RUNPY) -m fsf scan $(CASE) --out out/$(notdir $(CASE))
pack:
	PYTHONPATH=src $(RUNPY) -m fsf pack $(CASE) --out packs

case:
	$(RUNPY) cases/ccb-vendor-tpr-2026/build_case.py --pack packs/7689005313907642138
verify:
		$(RUNPY) tools/verify_pack.py packs/7689005313907642138

v2-test:
	PYTHONPATH=src:. $(RUNPY) -m unittest discover -s tests -v
v2-smoke:
	PYTHONPATH=src:. $(RUNPY) tools/v2_smoke.py
sample:
	PYTHONPATH=. $(RUNPY) samples/tca-01/build_sample.py
	PYTHONPATH=src:. $(RUNPY) -m unittest tests.test_sample_tca -v

run:
	PYTHONPATH=src:. $(RUNPY) tools/fsf_run.py --all

fin8:
	PYTHONPATH=src:. $(RUNPY) tools/scaffold_fin8.py --verify
	PYTHONPATH=src:. $(RUNPY) -m unittest tests.test_fin8_scaffold -v

# Eight-task batch production tools (scaffolds are not submission-ready)
batch-test:
	PYTHONPATH=src:. $(RUNPY) -m unittest tests.test_financial_batch_pipeline -v

batch-scaffold:
	@mkdir -p work/financial-eight
	@python3 -c 'import json,subprocess; b=json.load(open("finance/batch/selected_tasks.json",encoding="utf-8")); [subprocess.run(["$(RUNPY)","tools/new_task.py","--case-code",x["case_code"],"--batch-root","work/financial-eight"],check=True) for x in b["selected_tasks"]]'
	PYTHONPATH=src:. $(RUNPY) tools/package_batch.py --batch-root work/financial-eight --output dist/financial-eight --mode scaffold

batch-release:
	PYTHONPATH=src:. $(RUNPY) tools/package_batch.py --batch-root work/financial-eight --output dist/financial-eight --mode release
