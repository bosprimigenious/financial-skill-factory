PY ?= python3
VENV ?= vendor/financial-audit-bench/.venv
RUNPY = $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(PY))

.PHONY: test scan pack verify case help
help:
	@echo "make test   # run unit tests"
	@echo "make scan CASE=cases/<id>"
	@echo "make pack CASE=cases/<id>"
	@echo "make case   # 重建实例材料+GT（含逐格断言）"
	@echo "make verify # 题包机器校验"
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
