"""Configuration helpers for the lead verification orchestrator."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable

LOGGER = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Raised when configuration files are missing or malformed."""


_SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}


def load_configuration(path: str | Path) -> Dict[str, Any]:
    """Load configuration data from a JSON or YAML file."""

    file_path = Path(path)
    if not file_path.exists():
        raise ConfigurationError(f"Configuration file '{file_path}' was not found")

    if file_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        raise ConfigurationError(
            f"Unsupported configuration format '{file_path.suffix}'. Supported extensions: {sorted(_SUPPORTED_EXTENSIONS)}"
        )

    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        return json.loads(text)

    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency optional
        raise ConfigurationError(
            "YAML configuration requires the 'pyyaml' package to be installed"
        ) from exc

    return yaml.safe_load(text)  # type: ignore[no-any-return]


def iter_enabled_scraper_configs(config: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    scrapers = config.get("scrapers", [])
    for scraper in scrapers:
        if scraper.get("enabled", True):
            yield scraper
        else:
            LOGGER.debug("Skipping disabled scraper %s", scraper.get("name"))
