import asyncio
import importlib
import pytest

from web.routes.health import UpdatePreferencesPayload, set_update_preferences_api
from web.services.updater import get_cached_health
import web.services.updater as updater_module
import web.routes.health as health_module
from __version__ import __version__

RELEASES_BASE = "https://github.com/Developers-and-Dragons/ArcaneAuditor/releases"


def test_update_preferences_post(monkeypatch):
    stored = {"enabled": False, "first_run_completed": False}

    monkeypatch.setattr("utils.preferences_manager.get_update_prefs", lambda: stored.copy())

    def fake_set_update_prefs(new_prefs):
        stored.update(new_prefs)
        return True

    monkeypatch.setattr("utils.preferences_manager.set_update_prefs", fake_set_update_prefs)
    importlib.reload(health_module)

    response = asyncio.run(health_module.set_update_preferences_api(health_module.UpdatePreferencesPayload(enabled=True)))

    assert response["success"] is True
    assert stored["enabled"] is True


def test_get_cached_health_respects_caching(monkeypatch):
    monkeypatch.setattr("utils.preferences_manager.get_update_prefs", lambda: {"enabled": True, "first_run_completed": True})
    
    call_count = {"value": 0}

    def fake_check(force=False):
        call_count["value"] += 1
        return {
            "update_available": False,
            "latest_version": "99.0.0",
            "current_version": __version__,
            "error": None,
            "release_url": f"{RELEASES_BASE}/tag/v99.0.0",
        }

    monkeypatch.setattr("utils.update_checker.check_for_updates", fake_check)
    import time
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    importlib.reload(updater_module)

    updater_module._HEALTH_CACHE = {"latest_version": None, "error": None, "timestamp": 0.0, "release_url": RELEASES_BASE}

    payload1 = get_cached_health(force=True)
    assert call_count["value"] == 1
    assert payload1["update_info"]["latest_version"] == "99.0.0"
    assert payload1["update_info"]["update_available"] is True
    assert payload1["update_info"]["release_url"] == f"{RELEASES_BASE}/tag/v99.0.0"

    monkeypatch.setattr(time, "time", lambda: 1001.0)
    payload2 = get_cached_health()

    assert call_count["value"] == 1
    assert payload2["update_info"]["latest_version"] == "99.0.0"
    assert payload2["update_info"]["release_url"] == f"{RELEASES_BASE}/tag/v99.0.0"

    monkeypatch.setattr(updater_module, "__version__", "99.0.0")
    payload3 = get_cached_health()
    assert payload3["update_info"]["update_available"] is False


def test_get_cached_health_disabled(monkeypatch):
    importlib.reload(updater_module)

    monkeypatch.setattr("utils.preferences_manager.get_update_prefs", lambda: {"enabled": False, "first_run_completed": True})
    monkeypatch.setattr("utils.update_checker.check_for_updates", lambda force=False: {"latest_version": "3.0.0", "current_version": __version__, "error": None})
    updater_module._HEALTH_CACHE = {"latest_version": None, "error": None, "timestamp": 0.0, "release_url": RELEASES_BASE}

    payload = get_cached_health(force=True)

    assert payload["status"] == "healthy"
    assert payload["version"] == __version__
    assert "update_info" not in payload

