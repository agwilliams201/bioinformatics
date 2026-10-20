VENV = .venv
PYTHON = $(VENV)/bin/python

.PHONY: setup pipeline dashboard

setup:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) load_data.py
	$(PYTHON) analysis.py

dashboard:
	$(PYTHON) dashboard.py
