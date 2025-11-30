VENV = .venv
BIN = $(VENV)/Scripts
PYTHON = $(BIN)/python

PROJECT_NAME = 1_log_parser

.PHONY: run lint

run:
	$(PYTHON) ./main.py

lint:
	pre-commit run --all-files --color=never
