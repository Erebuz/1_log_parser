import argparse
import configparser
import json
import os
import sys
import tomllib
import traceback
from pathlib import Path
from typing import Any, cast

import structlog
import yaml

from src.app import App
from src.interfaces import BaseConfig
from src.logger import setup_structlog

BASE_CONFIG = {"LOG_DIR": "logs", "REPORT_DIR": "reports", "ERROR_LIMIT": 20}

root = os.path.dirname(__file__)

logger = structlog.get_logger()


def load_config(config_path: str) -> dict[str, Any]:
    path = Path(root, config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")

    if path.suffix == ".json":
        with open(path) as f:
            return json.load(f)  # type: ignore[no-any-return]
    elif path.suffix in [".yaml", ".yml"]:
        with open(path) as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]
    elif path.suffix == ".toml":
        with open(path, "rb") as f:
            return tomllib.load(f)
    elif path.suffix == ".ini":
        config = configparser.ConfigParser()
        config.read(path)
        return {section: dict(config[section]) for section in config.sections()}
    else:
        raise ValueError(f"Unsupported config format: {path.suffix}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", type=str, required=False)
        args = parser.parse_args()

        loaded_config = load_config(args.config) if args.config else None
        config = BASE_CONFIG | loaded_config if loaded_config else BASE_CONFIG

        log_path: str | None = cast(str | None, config.get("PARSE_LOG_PATH", None))
        setup_structlog(log_path)

        logger.info("Start", config=config)
        app = App(root, cast(BaseConfig, config))
        app.run()
    except BaseException as e:
        logger.error("Critical error", exc=e, exc_trace=traceback.format_exc())
        sys.exit(1)
