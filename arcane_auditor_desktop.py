"""
Arcane Auditor Desktop Application

Runs the FastAPI web server in a background thread and displays the UI
in a native desktop window using pywebview.
"""

# MINIMAL imports first - only what we need for splash
# This prevents heavy imports from slowing down the splash screen
import webview
import threading
import time
import sys
import os
import json
from pathlib import Path
import socket

def _get_free_port():
    """
    Asks the OS for a free ephemeral port.
    Binding to port 0 tells the OS 'assign me whatever is open'.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


window = None
desktop_api = None


def _wait_for_js_ready(window, timeout=5.0, interval=0.25):
    attempts = int(timeout / interval)
    for _ in range(attempts):
        try:
            ready = window.evaluate_js("Boolean(window.DialogManagerReady)")
            if isinstance(ready, str):
                ready = ready.lower() == 'true'
            if ready:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


class Api:
    """API class to expose Python functions to JavaScript in the desktop app"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def download_file(self, job_id):
        """Handle file downloads - auto-save to Downloads folder"""
        import requests
        from datetime import datetime
        
        try:
            response = requests.get(f'http://{self.host}:{self.port}/api/download/{job_id}')
            
            if response.status_code == 200:
                downloads_folder = Path.home() / "Downloads"
                downloads_folder.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
                filename = f"arcane-auditor-results-{timestamp}.xlsx"
                save_path = downloads_folder / filename
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                return {'success': True, 'path': str(save_path), 'filename': filename}
            else:
                return {'success': False, 'error': f'Server returned status {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_update_preferences(self):
        """Get current update preferences."""
        try:
            from utils.preferences_manager import get_update_prefs
            updates = get_update_prefs()
            return {
                'success': True,
                'enabled': updates.get('enabled', False),
                'first_run_completed': updates.get('first_run_completed', False)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def set_update_preferences(self, enabled):
        """Toggle update detection and persist to preferences."""
        try:
            from utils.preferences_manager import get_update_prefs, set_update_prefs
            updates = get_update_prefs()
            updates['enabled'] = bool(enabled)
            if set_update_prefs(updates):
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to save preferences'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_health_status(self):
        """Return current health and update availability information."""
        try:
            import requests

            response = requests.get(f"http://{self.host}:{self.port}/api/health", timeout=3)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                update_info = data.get("update_info")
                if isinstance(update_info, dict):
                    from utils.update_checker import GITHUB_RELEASES_BASE

                    latest = update_info.get("latest_version")
                    release_url = update_info.get("release_url")
                    if not release_url:
                        data["update_info"]["release_url"] = (
                            f"{GITHUB_RELEASES_BASE}/tag/v{latest}" if latest else GITHUB_RELEASES_BASE
                        )
                return data
        except Exception:
            pass

        from __version__ import __version__

        payload = {'status': 'healthy', 'version': __version__}

        try:
            from utils.preferences_manager import get_update_prefs
            from utils.update_checker import check_for_updates, GITHUB_RELEASES_BASE

            prefs = get_update_prefs()
            if prefs.get('enabled', False) and prefs.get('first_run_completed', False):
                update_info = check_for_updates(force=True)
                if isinstance(update_info, dict):
                    latest = update_info.get("latest_version")
                    release_url = update_info.get("release_url")
                    if not release_url:
                        update_info["release_url"] = (
                            f"{GITHUB_RELEASES_BASE}/tag/v{latest}" if latest else GITHUB_RELEASES_BASE
                        )
                    payload['update_info'] = update_info
        except Exception as exc:
            payload['update_error'] = str(exc)

        return payload

    def select_project_folder(self):
        """Open a native folder picker. Returns the selected directory path or cancellation."""
        global window
        try:
            win = window
            if win is None:
                return {'success': False, 'error': 'Window not ready'}
            paths = win.create_file_dialog(webview.FileDialog.FOLDER)
            if paths is None or (isinstance(paths, (tuple, list)) and len(paths) == 0):
                return {'success': False, 'error': 'cancelled', 'cancelled': True}
            first = paths[0] if isinstance(paths, (tuple, list)) else paths
            return {'success': True, 'path': str(first)}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def show_immediate_splash():
    """Create and show a minimal splash screen with logo"""
    
    # Load logo
    logo_html = '<div style="width: 500px; height: 500px; margin: 0 auto; background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 100px;">🧙</div>'
    
    try:
        from utils.arcane_paths import resource_path
        import base64
        
        splash_logo_path = Path(resource_path("assets/arcane-auditor-splash.webp"))
        if splash_logo_path.exists():
            with open(splash_logo_path, 'rb') as f:
                img_data = f.read()
                base64_data = base64.b64encode(img_data).decode('utf-8')
            logo_html = f'<img src="data:image/webp;base64,{base64_data}" style="width: 500px; height: 500px; object-fit: contain;">'
    except Exception as e:
        print(f"Could not load logo: {e}")
    
    # Simple splash HTML
    splash_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                width: 100%; height: 100vh; display: flex;
                justify-content: center; align-items: center; 
                background: #0f172a;
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        {logo_html}
    </body>
    </html>
    '''
    
    window_width = 500
    window_height = 500
    
    # Windows: Calculate center position
    # macOS: Omit x,y to let OS handle it (already works)
    if sys.platform == 'win32':
        import ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
    else:
        x_pos = None
        y_pos = None
    
    # Import version for window title
    from __version__ import __version__
    
    splash = webview.create_window(
        title=f'Arcane Auditor v{__version__}',
        html=splash_html,
        width=window_width,
        height=window_height,
        x=x_pos,
        y=y_pos,
        frameless=True,
        on_top=True,
        background_color='#0f172a',
    )
    
    return splash

def main():
    """
    Main entry point for the desktop application.
    
    Check for read-only location, shows splash immediately, then loads everything else in background.
    """ 
    
    # ========================================================================
    # CRITICAL: Check for read-only location BEFORE showing splash
    # This handles DMGs with no write access due to mounting as read-only.
    # ========================================================================
    from utils.dmg_detector import check_and_exit_if_dmg
    
    # Check for DMG and exit if found
    check_and_exit_if_dmg()
    
    # Show splash IMMEDIATELY before heavy imports
    splash = show_immediate_splash()

    # NOW do heavy imports and initialization in background
    def initialize_app():
        # Heavy imports happen here (after splash is visible)
        from utils.arcane_paths import is_frozen
        from web.server import app, load_web_config, ensure_sample_rule_config
        import uvicorn

        app.state.allow_directory_analysis = True
        
        DEFAULT_HOST = "127.0.0.1"

        # 1. Generate a guaranteed free port (e.g., 54321)
        dynamic_port = _get_free_port()
 
        # Load config
        cfg = load_web_config(cli_args=None)
        host = cfg.get("host", DEFAULT_HOST)
        port = dynamic_port
        log_level = "info"
        
        # Create API instance
        global desktop_api
        api = Api(host, port)
        desktop_api = api
        
        # Start server
        def run_server():
            ensure_sample_rule_config()
            print(f"Starting Arcane Auditor server on http://{host}:{port}")
            uvicorn_log_level = "critical" if is_frozen() else log_level
            uvicorn.run(app, host=host, port=port, log_level=uvicorn_log_level, access_log=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be ready
        time.sleep(3)  # Minimum display time for splash
        
        import urllib.request
        import urllib.error
        
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                urllib.request.urlopen(f'http://{host}:{port}/api/configs', timeout=1)
                print(f"Server ready after {attempt + 1} attempts")
                break
            except urllib.error.URLError:
                time.sleep(0.5)
                if attempt == max_attempts - 1:
                    print("Warning: Server did not start in time, continuing anyway")
        
        
        # Create main window first (needed for menu callbacks)
        global window
        from __version__ import __version__
        
        window = webview.create_window(
            title=f'Arcane Auditor v{__version__}',
            url=f'http://{host}:{port}',
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(1000, 700),
            background_color='#1e293b',
            text_select=True,
            hidden=True,
            on_top=False,
            confirm_close=False,
            js_api=api
        )
        
        # Wait for window to be ready
        time.sleep(0.5)
        
        # Show main window and close splash
        window.show()
        splash.destroy()

    
    # Start initialization in background thread
    init_thread = threading.Thread(target=initialize_app, daemon=True)
    init_thread.start()

    # Prepare storage directory
    from utils.arcane_paths import user_root
    storage_dir = os.path.join(user_root(), '.user_preferences')
    os.makedirs(storage_dir, exist_ok=True)
    
    def on_app_ready():
        def try_handle_first_run():
            try:
                if window is not None and desktop_api is not None:
                    _handle_first_run_and_updates(window, desktop_api)
                else:
                    timer = threading.Timer(0.5, try_handle_first_run)
                    timer.daemon = True
                    timer.start()
            except Exception as e:
                print(f"Error running first-run/update handler: {e}")

        try_handle_first_run()

    # Start GUI event loop - splash shows while initialization happens
    webview.start(
        debug=False,
        http_server=False,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        private_mode=False,
        storage_path=storage_dir,
        func=on_app_ready
    )
    
    print("Arcane Auditor Desktop closed.")


def _show_confirmation(window, title, message):
    """Show a confirmation dialog using the shared frontend helper."""

    def cleanup_dialog():
        try:
            window.evaluate_js(
                "(() => {"
                "if (window.DialogManager && typeof window.DialogManager.closeAll === 'function') { window.DialogManager.closeAll(); }"
                "window.__aaUpdatePromptState = null;"
                "})()"
            )
        except Exception:
            pass

    def should_abort():
        if getattr(window, "closed", False):
            return True
        try:
            window.evaluate_js("true")
            return False
        except Exception:
            return True

    def native_confirmation():
        if should_abort():
            return False
        try:
            return bool(window.create_confirmation_dialog(title, message))
        except Exception as native_error:
            print(f"Native confirmation dialog unavailable: {native_error}. Falling back to basic JS confirm.")
            script = f"confirm({json.dumps(f'{title}\\n\\n{message} (OK = Enable, Cancel = Disable)')});"
            try:
                if should_abort():
                    return False
                result = window.evaluate_js(script)
                if isinstance(result, str):
                    return result.lower() == 'true'
                return bool(result)
            except Exception as fallback_error:
                print(f"Error showing fallback JS confirm: {fallback_error}")
                return False

    if not _wait_for_js_ready(window):
        print("DialogManager not ready, falling back to native confirmation dialog.")
        return native_confirmation()

    lines = [line.strip() for line in message.split('\n') if line.strip()]
    payload = json.dumps({
        "title": title,
        "lines": lines,
    })

    made_on_top = False
    try:
        if hasattr(window, "set_on_top"):
            try:
                window.set_on_top(True)
                made_on_top = True
            except Exception:
                pass

        init_script = (
            "(() => {"
            "const manager = window.DialogManager;"
            "if (!manager || typeof manager.showUpdatePrompt !== 'function') { return 'missing'; }"
            "window.__aaUpdatePromptState = { ready: false };"
            f"manager.showUpdatePrompt({payload}).then(value => {{ window.__aaUpdatePromptState = {{ ready: true, value: Boolean(value) }}; }}).catch(error => {{ window.__aaUpdatePromptState = {{ ready: true, value: false, error: String(error) }}; }});"
            "return 'started';"
            "})()"
        )
        status = window.evaluate_js(init_script)
        if isinstance(status, str):
            status = status.strip('"')
        if status != 'started':
            raise RuntimeError('DialogManager unavailable')

        while True:
            if getattr(window, "closed", False):
                print("Window closed during update dialog; cancelling prompt.")
                cleanup_dialog()
                return False

            try:
                state_json = window.evaluate_js("JSON.stringify(window.__aaUpdatePromptState)")
            except Exception as eval_error:
                print(f"Lost connection to DialogManager: {eval_error}")
                cleanup_dialog()
                return False

            if state_json and state_json != 'null':
                try:
                    state = json.loads(state_json)
                except json.JSONDecodeError:
                    state = None
                if isinstance(state, dict) and state.get('ready'):
                    value = bool(state.get('value', False))
                    cleanup_dialog()
                    return value
            time.sleep(0.1)

    except Exception as helper_error:
        print(f"Custom update dialog unavailable: {helper_error}")
        return native_confirmation()
    finally:
        if made_on_top and hasattr(window, "set_on_top"):
            try:
                window.set_on_top(False)
            except Exception:
                pass


def _handle_first_run_and_updates(window, api):
    """Handle first-run dialog for update detection preference."""
    try:
        from utils.preferences_manager import get_update_prefs, set_update_prefs
        
        if getattr(window, "closed", False):
            return
        
        updates = get_update_prefs()
        first_run_completed = updates.get('first_run_completed', False)
        
        if first_run_completed:
            return
        
        message = (
            "Would you like Arcane Auditor to occasionally check for new versions?\n\n"
            "This is a read-only check that calls the GitHub API."
        )
        result = _show_confirmation(
            window,
            "Enable Update Detection?",
            message
        )
        
        updates['enabled'] = result
        updates['first_run_completed'] = True
        set_update_prefs(updates)

        try:
            window.evaluate_js(
                "(function(){"
                "if (window.app && typeof window.app.loadUpdatePreferences === 'function') { window.app.loadUpdatePreferences(); }"
                "if (window.app && typeof window.app.loadVersion === 'function') { window.app.loadVersion(); }"
                "})();"
            )
        except Exception:
            pass
    except Exception as e:
        print(f"Error in first-run/update handling: {e}")


if __name__ == '__main__':
    main()