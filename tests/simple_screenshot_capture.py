#!/usr/bin/env python3
"""
Simplified screenshot capture for already-running server.
Run this after starting the web server manually.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "config-editor"

# Server configuration (should already be running)
SERVER_URL = "http://127.0.0.1:8765"


async def capture_screenshots():
    """Capture screenshots of the configuration editor feature."""

    # Ensure assets directory exists
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📸 Starting screenshot capture...")
    print(f"   Server URL: {SERVER_URL}")
    print(f"   Screenshots will be saved to: {ASSETS_DIR}")

    async with async_playwright() as p:
        # Launch browser in headed mode for debugging
        browser = await p.chromium.launch(headless=False, slow_mo=500)

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
                print(f"   Loading page...")
                await page.goto(SERVER_URL, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Set theme via localStorage
                await page.evaluate(f'localStorage.setItem("arcane-auditor-theme", "{theme}")')
                await page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(3)

                # Screenshot 1: Initial page load
                print(f"   1. Initial page load...")
                await page.screenshot(
                    path=str(ASSETS_DIR / f"01-initial-page-{theme}.png"),
                    full_page=True
                )

                # Wait and check for config options
                try:
                    print(f"   Waiting for config options...")
                    await page.wait_for_selector(".config-option", timeout=15000)
                    await asyncio.sleep(2)

                    # Screenshot 2: Configuration view loaded
                    print(f"   2. Configuration selection view...")
                    await page.screenshot(
                        path=str(ASSETS_DIR / f"02-config-selection-{theme}.png"),
                        full_page=True
                    )

                    # Click on the first config to select it
                    print(f"   Selecting first configuration...")
                    first_config = await page.query_selector(".config-option")
                    if first_config:
                        await first_config.click()
                        await asyncio.sleep(1)

                        # Screenshot 3: Config selected
                        print(f"   3. Configuration selected...")
                        await page.screenshot(
                            path=str(ASSETS_DIR / f"03-config-selected-{theme}.png"),
                            full_page=True
                        )

                        # Try to find Edit button
                        edit_button = await page.query_selector('button.config-edit-btn, button:has-text("Edit")')
                        if edit_button:
                            print(f"   Opening configuration editor...")
                            await edit_button.click()
                            await asyncio.sleep(2)

                            # Screenshot 4: Editor modal
                            print(f"   4. Configuration editor modal...")
                            await page.screenshot(
                                path=str(ASSETS_DIR / f"04-editor-modal-{theme}.png"),
                                full_page=True
                            )

                            # Test search
                            search_input = await page.query_selector("#rule-search")
                            if search_input:
                                print(f"   Testing search functionality...")
                                await search_input.fill("Script")
                                await asyncio.sleep(1)

                                # Screenshot 5: Search in action
                                print(f"   5. Search functionality...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"05-editor-search-{theme}.png"),
                                    full_page=True
                                )

                                await search_input.fill("")
                                await asyncio.sleep(0.5)

                            # Test filter
                            filter_select = await page.query_selector("#rule-filter")
                            if filter_select:
                                print(f"   Testing filter functionality...")
                                await filter_select.select_option("enabled")
                                await asyncio.sleep(1)

                                # Screenshot 6: Filter in action
                                print(f"   6. Filter - enabled only...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"06-editor-filter-enabled-{theme}.png"),
                                    full_page=True
                                )

                                await filter_select.select_option("all")
                                await asyncio.sleep(0.5)

                            # Toggle a rule
                            first_toggle = await page.query_selector(".rule-toggle")
                            if first_toggle:
                                print(f"   Testing rule toggle...")
                                await first_toggle.click()
                                await asyncio.sleep(1)

                                # Screenshot 7: Rule toggled
                                print(f"   7. Rule toggle changed...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"07-editor-toggle-{theme}.png"),
                                    full_page=True
                                )

                            # Expand settings
                            expand_btn = await page.query_selector(".expand-settings-btn")
                            if expand_btn:
                                print(f"   Expanding rule settings...")
                                await expand_btn.click()
                                await asyncio.sleep(1)

                                # Screenshot 8: Settings expanded
                                print(f"   8. Rule settings expanded...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"08-editor-settings-expanded-{theme}.png"),
                                    full_page=True
                                )

                        else:
                            print(f"   No Edit button found - trying View Details...")
                            view_btn = await page.query_selector('button:has-text("View Details")')
                            if view_btn:
                                await view_btn.click()
                                await asyncio.sleep(1)

                                # Screenshot: Breakdown view
                                print(f"   4. Configuration breakdown...")
                                await page.screenshot(
                                    path=str(ASSETS_DIR / f"04-config-breakdown-{theme}.png"),
                                    full_page=True
                                )

                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
                    # Capture current state
                    await page.screenshot(
                        path=str(ASSETS_DIR / f"error-state-{theme}.png"),
                        full_page=True
                    )

            finally:
                await context.close()

        await browser.close()

    print(f"\n✅ Screenshot capture completed!")
    print(f"   Screenshots saved to: {ASSETS_DIR}")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
