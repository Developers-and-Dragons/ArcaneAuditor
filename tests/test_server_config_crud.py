import importlib
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import web.server as server
from web.services import config_loader
from utils import arcane_paths
from utils.preferences_manager import get_new_rule_default_enabled
from utils.config_normalizer import get_production_rules


@pytest.fixture
def server_ctx(monkeypatch, tmp_path):
    personal_dir = tmp_path / "personal"
    teams_dir = tmp_path / "teams"
    presets_dir = tmp_path / "presets"
    for directory in (personal_dir, teams_dir, presets_dir):
        directory.mkdir(parents=True, exist_ok=True)

    production_rules = {
        "RuleA": {"enabled": True, "severity_override": None, "custom_settings": {"threshold": 10}},
        "RuleB": {"enabled": True, "severity_override": "warning", "custom_settings": {}},
    }

    def fake_config_dirs():
        return {
            "personal": str(personal_dir),
            "teams": str(teams_dir),
            "presets": str(presets_dir),
        }

    # Patch in the modules BEFORE reloading so the reloaded modules pick up the patches
    monkeypatch.setattr(arcane_paths, "get_config_dirs", fake_config_dirs)
    monkeypatch.setattr("utils.preferences_manager.get_new_rule_default_enabled", lambda: False)
    monkeypatch.setattr("utils.config_normalizer.get_production_rules", lambda: production_rules)
    
    # Mock the runtime rules list to return our test rules
    # This is needed because normalize_config_rules uses runtime_rule_names as the source of truth
    def fake_get_runtime_rules_list():
        return ["RuleA", "RuleB"]
    
    # Clear cache first
    from utils import config_normalizer
    if hasattr(config_normalizer, '_load_production_rules'):
        config_normalizer._load_production_rules.cache_clear()
    
    # Now reload modules so they pick up the patched functions
    # Reload in order: config_loader first (bottom), then routes (middle), then server (top)
    config_loader_module = importlib.reload(config_loader)
    from web.routes import configs
    importlib.reload(configs)
    # Reload server last - when it reloads, it will re-include the routers
    server_module = importlib.reload(server)
    
    # Patch the runtime rules list AFTER reloading so the reloaded module uses it
    monkeypatch.setattr(configs, "_get_runtime_rules_list", fake_get_runtime_rules_list)

    # Seed configs
    with (personal_dir / "alpha.json").open("w", encoding="utf-8") as handle:
        json.dump({"rules": {"RuleA": {"enabled": True}}}, handle)

    with (presets_dir / "baseline.json").open("w", encoding="utf-8") as handle:
        json.dump({"rules": {"RuleA": {"enabled": True}}}, handle)

    client = TestClient(server_module.app)
    return SimpleNamespace(
        server=server_module,
        client=client,
        personal=personal_dir,
        teams=teams_dir,
        presets=presets_dir,
    )


def test_get_configuration_normalizes_rules(server_ctx):
    response = server_ctx.client.get("/api/config/alpha_personal")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "alpha_personal"
    assert data["rules_count"] == 1
    rules = data["config"]["rules"]
    assert rules["RuleA"]["enabled"] is True
    # Missing RuleB should be injected but disabled (preference set to False)
    assert rules["RuleB"]["enabled"] is False
    assert rules["RuleB"]["severity_override"] == "warning"


def test_save_configuration_writes_normalized_rules(server_ctx, tmp_path):
    payload = {
        "config": {
            "rules": {
                "RuleB": {"enabled": True, "custom_settings": {"threshold": 99}},
            }
        }
    }

    response = server_ctx.client.post("/api/config/alpha_personal/save", json=payload)
    assert response.status_code == 200
    data = response.json()

    rules = data["config"]["rules"]
    assert rules["RuleB"]["enabled"] is True
    assert rules["RuleB"]["custom_settings"]["threshold"] == 99
    assert rules["RuleA"]["enabled"] is False  # Default preference disables new rules

    saved = json.loads((server_ctx.personal / "alpha.json").read_text(encoding="utf-8"))
    assert "RuleA" in saved["rules"]
    assert saved["rules"]["RuleB"]["enabled"] is True


def test_save_configuration_rejects_presets(server_ctx):
    payload = {"config": {"rules": {"RuleA": {"enabled": False}}}}
    response = server_ctx.client.post("/api/config/baseline_presets/save", json=payload)
    assert response.status_code == 403


def test_create_configuration_with_defaults(server_ctx):
    response = server_ctx.client.post(
        "/api/config/create",
        json={"name": "New Config", "target": "personal"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "new_config_personal"
    new_path = server_ctx.personal / "new_config.json"
    assert new_path.exists()

    saved = json.loads(new_path.read_text(encoding="utf-8"))
    assert "rules" in saved
    # Default preference disabled, so rules should be disabled
    assert all(not rule.get("enabled", False) for rule in saved["rules"].values())


def test_create_configuration_from_base(server_ctx):
    response = server_ctx.client.post(
        "/api/config/create",
        json={"name": "Baseline Copy", "target": "team", "base_id": "baseline_presets"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "baseline_copy_teams"

    copied_path = server_ctx.teams / "baseline_copy.json"
    assert copied_path.exists()
    copied = json.loads(copied_path.read_text(encoding="utf-8"))
    assert "RuleA" in copied["rules"]


def test_delete_configuration(server_ctx):
    new_config_path = server_ctx.personal / "delete_me.json"
    new_config_path.write_text(json.dumps({"rules": {"RuleA": {"enabled": True}}}), encoding="utf-8")

    # Force dynamic info to pick up new file
    server_ctx.client.get("/api/configs")

    response = server_ctx.client.delete("/api/config/delete_me_personal")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not new_config_path.exists()

