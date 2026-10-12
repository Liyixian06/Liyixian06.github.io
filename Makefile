DOUBAN_VENV := .venv-douban
DOUBAN_PYTHON := $(DOUBAN_VENV)/bin/python

.PHONY: douban-install douban-check douban-sync douban-migrate-book-images douban-test

douban-install:
	python3 -m venv $(DOUBAN_VENV)
	$(DOUBAN_PYTHON) -m pip install -r requirements-douban.txt

douban-check:
	$(DOUBAN_PYTHON) scripts/sync_douban.py --dry-run

douban-sync:
	$(DOUBAN_PYTHON) scripts/sync_douban.py

douban-migrate-book-images:
	$(DOUBAN_PYTHON) scripts/sync_douban.py --type book --replace-douban-images --delay 1

douban-test:
	$(DOUBAN_PYTHON) -m unittest discover -s tests -v
