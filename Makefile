PY ?= python3
VENV ?= vendor/financial-audit-bench/.venv
RUNPY = $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(PY))

.PHONY: test scan pack help
help:
	@echo "make test   # run unit tests"
	@echo "make scan CASE=cases/<id>"
	@echo "make pack CASE=cases/<id>"
test:
	PYTHONPATH=src $(RUNPY) -m unittest discover -s tests -v
scan:
	PYTHONPATH=src $(RUNPY) -m fsf scan $(CASE) --out out/$(notdir $(CASE))
pack:
	PYTHONPATH=src $(RUNPY) -m fsf pack $(CASE) --out packs
