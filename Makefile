DOUBAN_VENV := .venv-douban
DOUBAN_PYTHON := $(DOUBAN_VENV)/bin/python
PAGEFIND_VERSION := 1.6.0
PAGEFIND := npx --yes pagefind@$(PAGEFIND_VERSION)

.PHONY: build search-index search-preview douban-install douban-check douban-sync douban-migrate-book-images douban-test images-check images-optimize

build:
	hugo
	$(MAKE) search-index

search-index:
	$(PAGEFIND) --site public --output-subdir _pagefind

search-preview:
	hugo
	$(PAGEFIND) --site public --output-subdir _pagefind --serve

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

images-check:
	$(DOUBAN_PYTHON) scripts/optimize_journal_images.py

images-optimize:
	$(DOUBAN_PYTHON) scripts/optimize_journal_images.py --apply
