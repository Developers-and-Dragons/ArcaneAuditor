"""
Configuration management routes for Arcane Auditor.

Handles CRUD operations for configuration files.
"""

from copy import deepcopy
import json
import re
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from utils.arcane_paths import get_config_dirs
from utils.preferences_manager import get_new_rule_default_enabled
from utils.config_normalizer import get_production_rules, normalize_config_rules
from utils.json_io import atomic_write_json
from web.services.config_loader import get_dynamic_config_info
from parser.rules_engine import RulesEngine
from parser.config import ArcaneAuditorConfig

router = APIRouter()


class ConfigSaveRequest(BaseModel):
    """Request payload for saving a configuration document."""
    config: Dict[str, Any]


class ConfigCreateRequest(BaseModel):
    """Request payload for creating a new configuration document."""
    name: str
    target: str
    base_id: None | str = None
    config: None | Dict[str, Any] = None


def _get_config_entry(config_id: str) -> Dict[str, Any]:
    entry = get_dynamic_config_info().get(config_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Configuration '{config_id}' not found")
    return entry


def _read_config_document(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file missing")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Configuration JSON malformed: {exc}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Configuration document must be a JSON object")
    return data


def _get_runtime_rules_list() -> list[str]:
    """
    Instantiate RulesEngine (lightweight) and return a list of all rule class names.
    
    Returns:
        list[str]: List of rule class names discovered at runtime.
    """
    config = ArcaneAuditorConfig()
    engine = RulesEngine(config)
    return [rule.__class__.__name__ for rule in engine.rules]


def _normalize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    normalized = deepcopy(document or {})
    rules = normalized.get("rules", {})
    runtime_rule_names = _get_runtime_rules_list()
    normalized["rules"] = normalize_config_rules(
        rules,
        default_enabled=get_new_rule_default_enabled(),
        runtime_rule_names=runtime_rule_names,
        production_rules=get_production_rules(),
    )
    return normalized


def _ensure_writable(entry: Dict[str, Any]) -> None:
    if entry.get("source") == "presets":
        raise HTTPException(status_code=403, detail="Built-in presets cannot be modified")


def _allowed_roots() -> Dict[str, Path]:
    dirs = get_config_dirs()
    return {key: Path(path) for key, path in dirs.items()}


def _ensure_path_within(path: Path) -> None:
    resolved = path.resolve()
    roots = _allowed_roots()
    if not any(resolved.is_relative_to(root.resolve()) for root in roots.values()):
        raise HTTPException(status_code=400, detail="Configuration path is outside allowed directories")


def _build_config_response(config_id: str) -> Dict[str, Any]:
    entry = _get_config_entry(config_id)
    document = _read_config_document(Path(entry["path"]))
    normalized = _normalize_document(document)
    rules = normalized.get("rules", {})

    return {
        "id": config_id,
        "name": entry.get("name"),
        "description": entry.get("description"),
        "source": entry.get("source"),
        "type": entry.get("type"),
        "path": entry.get("path"),
        "rules_count": entry.get("rules_count", sum(1 for rule in rules.values() if rule.get("enabled", True))),
        "total_rules": entry.get("total_rules", len(rules)),
        "config": normalized,
    }


def _sanitize_config_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", name.strip())
    cleaned = re.sub(r"_{2,}", "_", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("_-")
    if not cleaned:
        raise HTTPException(status_code=400, detail="Configuration name is invalid")
    return cleaned.lower()


def _resolve_target_directory(target: str) -> tuple[str, Path]:
    normalized = (target or "").strip().lower()
    if normalized in ("personal", "user"):
        key = "personal"
    elif normalized in ("team", "teams"):
        key = "teams"
    else:
        raise HTTPException(status_code=400, detail="Target must be 'personal' or 'team'")

    dirs = get_config_dirs()
    directory = Path(dirs[key])
    directory.mkdir(parents=True, exist_ok=True)
    return key, directory


def get_rule_default_severities():
    """Get default severities for all rules by loading them from rule classes."""
    from parser.rules_engine import RulesEngine
    from parser.config import ArcaneAuditorConfig

    # Create a default config to discover all rules
    config = ArcaneAuditorConfig()
    engine = RulesEngine(config)

    # Build a map of rule name -> default severity
    severities = {}
    for rule in engine.rules:
        rule_name = rule.__class__.__name__
        severities[rule_name] = rule.SEVERITY

    return severities


def get_rule_default_fix_strategies():
    """Get default fix_strategy values for all rules by loading them from rule classes."""
    from parser.rules_engine import RulesEngine
    from parser.config import ArcaneAuditorConfig

    config = ArcaneAuditorConfig()
    engine = RulesEngine(config)
    return {
        rule.__class__.__name__: rule.FIX_STRATEGY.value
        for rule in engine.rules
    }


@router.get("/api/configs")
async def get_available_configs(response: Response):
    """Get list of available configurations with resolved severities."""
    # Add cache-busting headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Get default severities and fix_strategy values from rule classes
    default_severities = get_rule_default_severities()
    default_fix_strategies = get_rule_default_fix_strategies()

    config_info = get_dynamic_config_info()
    available_configs = []

    for config_name, info in config_info.items():
        config_data = info.copy()
        config_data["id"] = config_name

        # Resolve null overrides to actual rule defaults so the UI can render
        # the effective value without round-tripping through the rules engine.
        if "rules" in config_data:
            for rule_name, rule_config in config_data["rules"].items():
                if isinstance(rule_config, dict):
                    if rule_config.get("severity_override") is None and rule_name in default_severities:
                        rule_config["severity_override"] = default_severities[rule_name]
                    if rule_config.get("fix_strategy_override") is None and rule_name in default_fix_strategies:
                        rule_config["fix_strategy_override"] = default_fix_strategies[rule_name]

        available_configs.append(config_data)
    
    return {"configs": available_configs}


@router.get("/api/config/{config_id}")
async def get_configuration(config_id: str):
    """Fetch a normalized configuration document."""
    return _build_config_response(config_id)


@router.post("/api/config/{config_id}/save")
async def save_configuration(config_id: str, payload: ConfigSaveRequest):
    """Persist configuration changes with normalization and atomic write safety."""
    entry = _get_config_entry(config_id)
    _ensure_writable(entry)
    path = Path(entry["path"])
    _ensure_path_within(path)

    normalized = _normalize_document(payload.config)

    try:
        atomic_write_json(path, normalized)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {exc}")

    return _build_config_response(config_id)


@router.post("/api/config/create")
async def create_configuration(request: ConfigCreateRequest):
    """Create a new configuration, optionally duplicating from an existing one."""
    key, directory = _resolve_target_directory(request.target)
    config_name = _sanitize_config_name(request.name)
    target_path = directory / f"{config_name}.json"

    if target_path.exists():
        raise HTTPException(status_code=409, detail="A configuration with that name already exists")

    if request.base_id:
        base_entry = _get_config_entry(request.base_id)
        base_document = _read_config_document(Path(base_entry["path"]))
    elif request.config is not None:
        base_document = request.config
    else:
        base_document = {}

    normalized = _normalize_document(base_document)

    try:
        atomic_write_json(target_path, normalized)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {exc}")

    new_id = f"{config_name}_{key}"
    return _build_config_response(new_id)


@router.delete("/api/config/{config_id}")
async def delete_configuration(config_id: str):
    """Delete a writable configuration."""
    entry = _get_config_entry(config_id)
    _ensure_writable(entry)
    path = Path(entry["path"])
    _ensure_path_within(path)

    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {exc}")

    return {"id": config_id, "status": "deleted"}


