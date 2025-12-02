VENV = .venv
BIN = $(VENV)/Scripts
PYTHON = $(BIN)/python

PROJECT_NAME = 1_log_parser

.PHONY: run lint

run:
	$(PYTHON) ./run.py --config config/config.yaml

lint:
	pre-commit run --all-files --color=never

test:
	uv run pytest

build_docker:
	docker build -t log-parser:latest .

build_up_docker_compose:
	docker compose up --build
