PY_FILES = zone.py connection.py graph.py parser.py dijkstra.py simulation.py main.py

MAP ?= 03_ultimate_challenge.txt
install:
	pip install flake8 mypy colorama --break-system-packages

run:
	python3 main.py $(MAP)

debug:
	python3 -m pdb main.py $(MAP)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

lint:
	flake8 $(PY_FILES)
	mypy $(PY_FILES) \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs \
		--explicit-package-bases

lint-strict:
	flake8 $(PY_FILES)
	mypy $(PY_FILES) --strict --explicit-package-bases

.PHONY: install run debug clean lint lint-strict
