#!/usr/bin/env python3
"""
Automated screenshot capture for the Configuration Editor feature.
This script starts the web server, navigates through the configuration editor,
and captures screenshots for documentation.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "config-editor"
SERVER_SCRIPT = PROJECT_ROOT / "web" / "server.py"

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765  # Use different port to avoid conflicts


async def wait_for_server(url: str, max_attempts: int = 30):
    """Wait for the server to become available."""
    import aiohttp

    for attempt in range(max_attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        print(f"✓ Server is ready at {url}")
                        return True
        except Exception:
            if attempt == 0:
                print(f"Waiting for server at {url}...")
            await asyncio.sleep(1)

    print(f"✗ Server did not become available after {max_attempts} seconds")
    return False


async def capture_screenshots():
    """Capture screenshots of the configuration editor feature."""

    # Ensure assets directory exists
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📸 Starting screenshot capture...")
    print(f"   Screenshots will be saved to: {ASSETS_DIR}")

    # Start the web server
    print(f"\n🚀 Starting web server on {SERVER_HOST}:{SERVER_PORT}...")
    server_process = subprocess.Popen(
        ["python3", str(SERVER_SCRIPT), "--host", SERVER_HOST, "--port", str(SERVER_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for server to be ready
        server_url = f"http://{SERVER_HOST}:{SERVER_PORT}"
        if not await wait_for_server(server_url):
            raise Exception("Server failed to start")

        # Give server extra time to fully initialize
        await asyncio.sleep(2)

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)

            # Create contexts for both themes
            for theme in ["dark", "light"]:
                print(f"\n📷 Capturing {theme} mode screenshots...")

                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    color_scheme=theme
                )

                page = await context.new_page()

                try:
                    # Navigate to the application
                    await page.goto(server_url, wait_until="networkidle")
                    await asyncio.sleep(1)

                    # Set theme via localStorage and reload
                    await page.evaluate(f'localStorage.setItem("arcane-auditor-theme", "{theme}")')
                    await page.reload(wait_until="networkidle")
                    await asyncio.sleep(3)

                    # Wait for the configuration grid to be populated
                    await page.wait_for_selector(".config-grid .config-option", timeout=20000)
                    await asyncio.sleep(2)

                    # Screenshot 1: Initial configuration view
                    print(f"   1. Configuration selection view...")
                    await page.screenshot(
                        path=str(ASSETS_DIR / f"01-config-selection-{theme}.png"),
                        full_page=True
                    )

                    # Select a personal configuration (test-config if it exists)
                    # First, let's try to click on a personal config
                    try:
                        # Wait for configs to be visible
                        await page.wait_for_selector(".config-option", timeout=10000)

                        # Try to find and select a personal or team config
                        personal_config = await page.query_selector('.config-option:has(.config-type:text("Personal")), .config-option:has(.config-type:text("Team"))')

                        if not personal_config:
                            # If no personal/team config, use the first built-in config for demo
                            personal_config = await page.query_selector(".config-option")

                        if personal_config:
                            await personal_config.click()
                            await asyncio.sleep(1)

                            # Screenshot 2: Config selected with Edit button visible
                            print(f"   2. Configuration selected with Edit button...")
                            await page.screenshot(
                                path=str(ASSETS_DIR / f"02-config-selected-{theme}.png"),
                                full_page=True
                            )

                            # Click the Edit button if it exists
                            edit_button = await page.query_selector('button.config-edit-btn')
                            if edit_button:
                                await edit_button.click()
                                await asyncio.sleep(1)

                                # Screenshot 3: Editor modal opened
                                print(f"   3. Configuration editor modal...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"03-editor-modal-{theme}.png"),
                                    full_page=True
                                )

                                # Screenshot 4: Search functionality
                                print(f"   4. Search functionality...")
                                search_input = await page.query_selector("#rule-search")
                                if search_input:
                                    await search_input.fill("Script")
                                    await asyncio.sleep(0.5)
                                    await page.screenshot(
                                        path=str(ASSETS_DIR / f"04-editor-search-{theme}.png"),
                                        full_page=True
                                    )
                                    await search_input.fill("")  # Clear search
                                    await asyncio.sleep(0.5)

                                # Screenshot 5: Filter functionality
                                print(f"   5. Filter functionality...")
                                filter_select = await page.query_selector("#rule-filter")
                                if filter_select:
                                    await filter_select.select_option("enabled")
                                    await asyncio.sleep(0.5)
                                    await page.screenshot(
                                        path=str(ASSETS_DIR / f"05-editor-filter-enabled-{theme}.png"),
                                        full_page=True
                                    )
                                    await filter_select.select_option("all")
                                    await asyncio.sleep(0.5)

                                # Screenshot 6: Toggle a rule
                                print(f"   6. Rule toggle interaction...")
                                first_toggle = await page.query_selector(".rule-toggle")
                                if first_toggle:
                                    original_state = await first_toggle.is_checked()
                                    await first_toggle.click()
                                    await asyncio.sleep(0.5)
                                    await page.screenshot(
                                        path=str(ASSETS_DIR / f"06-editor-toggle-changed-{theme}.png"),
                                        full_page=True
                                    )
                                    # Toggle back
                                    await first_toggle.click()
                                    await asyncio.sleep(0.5)

                                # Screenshot 7: Expand settings panel
                                print(f"   7. Rule settings panel...")
                                expand_button = await page.query_selector(".expand-settings-btn")
                                if expand_button:
                                    await expand_button.click()
                                    await asyncio.sleep(0.5)
                                    await page.screenshot(
                                        path=str(ASSETS_DIR / f"07-editor-settings-expanded-{theme}.png"),
                                        full_page=True
                                    )

                                # Screenshot 8: Full editor view with settings
                                print(f"   8. Full editor overview...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"08-editor-overview-{theme}.png"),
                                    full_page=True
                                )

                                # Close modal
                                close_button = await page.query_selector(".modal-close")
                                if close_button:
                                    await close_button.click()
                                    await asyncio.sleep(0.5)
                            else:
                                print(f"   ⚠️  No Edit button found (may be a built-in preset)")
                                # Still capture the breakdown view
                                view_details_btn = await page.query_selector('button.config-details-btn')
                                if view_details_btn:
                                    await view_details_btn.click()
                                    await asyncio.sleep(1)
                                    await page.screenshot(
                                        path=str(ASSETS_DIR / f"03-config-breakdown-{theme}.png"),
                                        full_page=True
                                    )
                        else:
                            print(f"   ⚠️  No configuration options found")

                    except Exception as e:
                        print(f"   ⚠️  Error during interaction: {e}")
                        # Capture error state
                        await page.screenshot(
                            path=str(ASSETS_DIR / f"error-{theme}.png"),
                            full_page=True
                        )

                finally:
                    await context.close()

            await browser.close()

        print(f"\n✅ Screenshot capture completed!")
        print(f"   Screenshots saved to: {ASSETS_DIR}")

    finally:
        # Cleanup: Stop the server
        print(f"\n🛑 Stopping web server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
        print(f"   Server stopped")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
