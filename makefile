VENV = .venv
BIN = $(VENV)/Scripts
PYTHON = $(BIN)/python

PROJECT_NAME = 1_log_parser

run:
	$(PYTHON) ./main.py
