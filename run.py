import argparse
import configparser
import json
import os
import tomllib
from pathlib import Path
from typing import Any

import yaml

BASE_CONFIG = {"test": "test"}


def load_config(config_path: str) -> dict[str, Any]:
    root = os.path.dirname(__file__)

    path = Path(root, config_path)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()

    loaded_config = load_config(args.config)
    config = BASE_CONFIG | loaded_config if loaded_config else BASE_CONFIG

    print(config)
