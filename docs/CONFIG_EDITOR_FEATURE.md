# Configuration Editor Feature Documentation

## 📋 Overview

The Configuration Editor is a new web interface feature that allows users to visually edit validation rule configurations through an interactive modal editor. This addresses [Issue #10](https://github.com/Developers-and-Dragons/ArcaneAuditor/issues/10) by providing write capabilities for configuration files.

**Key Benefits:**
- ✏️ Visual editing of personal and team configurations
- 🔒 Built-in presets are protected from accidental modification
- 🎚️ Quick enable/disable rules with toggle switches
- ⚙️ Edit custom settings for each rule with JSON validation
- 🔍 Search and filter rules for easy navigation
- 💾 Save changes directly from the web interface

---

## 🎯 Feature Capabilities

### What You Can Do

#### ✅ Enable/Disable Rules
- Toggle individual rules on/off with visual switches
- See immediate visual feedback when changing rule status
- Status badge updates in real-time

#### ✅ Edit Rule Settings
- Change severity overrides (ACTION ↔ ADVICE)
- Configure custom rule-specific settings via JSON editor
- JSON validation prevents invalid configurations

#### ✅ Search & Filter
- **Search by name**: Find rules instantly by typing partial names
- **Filter options**:
  - All rules
  - Enabled rules only
  - Disabled rules only
  - Rules with custom settings

#### ✅ Save Configurations
- Save changes to personal configurations (`config/personal/`)
- Save changes to team configurations (`config/teams/`)
- **Cannot** modify built-in presets (`config/presets/`) - they're protected

### What You Cannot Do

#### ❌ Edit Built-in Presets
Built-in presets (`development`, `production-ready`) are read-only because:
- They get overwritten during application updates
- Modifying them could break expected behavior
- You should create a personal/team config instead

**Solution:** Copy a preset's settings and create your own configuration.

#### ❌ Delete Configurations
Currently, deletion must be done manually by removing the JSON file from `config/personal/` or `config/teams/`.

#### ❌ Create New Configurations
The current interface only supports editing existing configurations. To create a new one:
1. Manually create a JSON file in `config/personal/` or `config/teams/`
2. Use the command-line tool: `uv run main.py generate-config > config/personal/my-config.json`
3. Refresh the web interface to see your new configuration

---

## 🚀 How to Test the Feature

### Prerequisites

1. **Start the web server:**
   ```bash
   cd ArcaneAuditor
   ./start-web-service.sh
   ```

   The server will automatically open your browser to `http://localhost:8080`

2. **Create a test configuration** (if you don't have one):
   ```bash
   # Copy the development preset to personal
   mkdir -p config/personal
   cp config/presets/development.json config/personal/test-config.json
   ```

### Test Workflow

#### Step 1: Access the Configuration Editor

1. Open the web interface (`http://localhost:8080`)
2. Scroll to the **⚙️ Analysis Configuration** section
3. You'll see configuration cards grouped by type:
   - **Built-in** (presets from Arcane Auditor)
   - **Team** (shared team configurations)
   - **Personal** (your personal configurations)

#### Step 2: Select a Configuration

1. Click on a configuration card to select it
2. The card will highlight and show action buttons
3. **For built-in presets**: You'll only see "📋 View Details"
4. **For personal/team configs**: You'll see both "📋 View Details" and "✏️ Edit"

#### Step 3: Open the Editor

1. Click the **✏️ Edit** button on a personal or team configuration
2. The Configuration Editor modal will open
3. You should see:
   - Editor title showing which config you're editing
   - Search bar at the top
   - Filter dropdown (All Rules / Enabled Only / Disabled Only / Has Custom Settings)
   - Scrollable list of all validation rules

#### Step 4: Test Rule Toggling

1. Find any rule in the list
2. Click the toggle switch on the left
3. Observe:
   - The switch animates to the new position
   - The status text changes ("✓ Enabled" ↔ "✗ Disabled")
   - The rule's `data-enabled` attribute updates
4. Toggle it back to confirm it works both ways

#### Step 5: Test Search Functionality

1. In the search bar, type: `Script`
2. Observe:
   - Only rules with "Script" in their name are shown
   - Other rules are hidden
   - Search is case-insensitive
3. Clear the search to see all rules again

#### Step 6: Test Filter Functionality

1. Open the filter dropdown
2. Select "Enabled Only"
3. Observe:
   - Only enabled rules are displayed
   - Disabled rules are hidden
4. Try other filter options:
   - "Disabled Only"
   - "Has Custom Settings"
5. Return to "All Rules"

#### Step 7: Test Settings Panel

1. Find a rule (like `ScriptLongBlockRule` which has custom settings)
2. Click the "⚙️ Settings" button
3. The settings panel expands showing:
   - **Severity Override** dropdown
   - **Custom Settings** JSON textarea
4. Try changing the severity from ADVICE to ACTION or vice versa
5. Try editing the JSON in the custom settings:
   ```json
   {
     "max_lines": 50,
     "skip_comments": true,
     "skip_blank_lines": true
   }
   ```

#### Step 8: Test Saving

1. Make a few changes:
   - Toggle a rule on/off
   - Change a severity
   - Modify custom settings
2. Click the **💾 Save Changes** button at the bottom
3. Observe:
   - If successful, you'll see "Configuration saved successfully!"
   - If there's a JSON error, you'll see an error message
   - The modal closes automatically on success
4. Verify the changes were saved:
   - Open your config file (`config/personal/test-config.json`)
   - Confirm your changes are present

#### Step 9: Test Built-in Preset Protection

1. Select a built-in preset (like "Development" or "Production Ready")
2. Observe:
   - No "✏️ Edit" button appears
   - Only "📋 View Details" is available
3. Click "📋 View Details" to see the breakdown
4. This confirms built-in presets are protected

---

## 🎨 User Interface Elements

### Configuration Card

Each configuration displays:
- **Type badge** (Built-in / Team / Personal)
- **Configuration name**
- **Description** (shows rule count)
- **Performance indicator** (Fast / Balanced / Thorough)
- **Action buttons** (when selected)

### Editor Modal Components

#### Header
- **Title**: "✏️ Edit Configuration"
- **Close button** (×)

#### Search & Filter Bar
- **Search input**: Real-time filtering by rule name
- **Filter dropdown**: Filter by status or settings

#### Rule List
Each rule item shows:
- **Toggle switch**: Enable/disable the rule
- **Rule name**: Full rule class name
- **Status text**: Current status with icon
- **Settings button**: Expand to see/edit settings

#### Settings Panel (when expanded)
- **Severity dropdown**: ACTION or ADVICE
- **Custom settings textarea**: JSON configuration
- **Hint text**: "Enter valid JSON for rule-specific settings"

#### Footer
- **Cancel button**: Close without saving
- **Save Changes button**: Validate and save

---

## 🔧 Technical Details

### API Endpoints

#### POST `/api/configs/{config_id}`
Saves changes to an existing configuration.

**Request Body:**
```json
{
  "rules": {
    "RuleName": {
      "enabled": true,
      "severity_override": "ACTION",
      "custom_settings": {}
    }
  },
  "file_processing": { ... },
  "output": { ... }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration saved to config/personal/test-config.json"
}
```

**Error Responses:**
- `400`: Invalid config ID format
- `403`: Attempting to edit a built-in preset
- `500`: File write error

#### POST `/api/configs/create`
Creates a new configuration file.

**Note:** Not yet implemented in the UI, but the API endpoint exists for future use.

### File Structure

```
config/
├── presets/           # Built-in (read-only)
│   ├── development.json
│   └── production-ready.json
├── teams/             # Team configs (editable)
│   └── team-config.json
└── personal/          # Personal configs (editable)
    └── my-config.json
```

### Configuration ID Format

Configurations are identified by: `{config_name}_{source}`

Examples:
- `development_presets` - Built-in development preset
- `test-config_personal` - Personal test configuration
- `strict-rules_teams` - Team strict rules configuration

---

## 🐛 Known Limitations

1. **No visual diff**: Changes aren't highlighted until after save
2. **No undo/redo**: Once saved, changes are permanent (edit the file manually to revert)
3. **No real-time validation**: JSON errors are only caught on save
4. **No configuration creation**: Must create JSON files manually or via CLI
5. **No configuration deletion**: Must delete JSON files manually

---

## 💡 Tips & Best Practices

### For Configuration Management

1. **Start with a preset**: Copy `development.json` or `production-ready.json` to personal
2. **Use descriptive names**: Name your configs clearly (e.g., `frontend-strict.json`)
3. **Test before deploying**: Use personal configs to test rule changes before promoting to team
4. **Document custom settings**: Add comments in your config file (outside the JSON) to explain why specific rules are configured

### For Editing Rules

1. **Search before scrolling**: Use the search bar to find specific rules quickly
2. **Filter to focus**: Use filters to focus on enabled rules you want to fine-tune
3. **Expand one at a time**: Keep only one settings panel open to avoid confusion
4. **Validate JSON**: Use a JSON validator if you're unsure about your custom settings syntax
5. **Save frequently**: Save after each logical group of changes

### For Custom Settings

Examples of common custom settings:

```json
// ScriptLongBlockRule - adjust max lines and skip options
{
  "max_lines": 50,
  "skip_comments": true,
  "skip_blank_lines": true
}

// ScriptNestingLevelRule - change maximum nesting depth
{
  "max_nesting_level": 4
}

// ScriptDescriptiveParameterRule - allow specific single-letter params
{
  "allowed_single_letters": ["i", "j", "x", "y"]
}
```

---

## 📸 Screenshot Capture Guide

### Automated Approach

We've provided a Playwright script for automated screenshot capture:

```bash
# Install Playwright
pip3 install playwright
playwright install chromium

# Run the screenshot script (requires server to be running)
python3 tests/simple_screenshot_capture.py
```

Screenshots will be saved to: `assets/config-editor/`

### Manual Approach

If automated screenshot capture doesn't work, use this manual process:

1. **Start the web server**:
   ```bash
   ./start-web-service.sh --port 8080
   ```

2. **Open browser to http://localhost:8080**

3. **Capture these key screenshots**:

   **01 - Configuration Selection View**
   - Full page showing all configuration cards
   - Save as: `assets/config-editor/01-config-selection-[theme].png`

   **02 - Configuration Selected**
   - Click a personal config to show the Edit button
   - Save as: `assets/config-editor/02-config-selected-[theme].png`

   **03 - Editor Modal Opened**
   - Click Edit to open the modal
   - Full modal view with all rules visible
   - Save as: `assets/config-editor/03-editor-modal-[theme].png`

   **04 - Search in Action**
   - Type "Script" in the search bar
   - Save as: `assets/config-editor/04-editor-search-[theme].png`

   **05 - Filter Applied**
   - Select "Enabled Only" from filter
   - Save as: `assets/config-editor/05-editor-filter-enabled-[theme].png`

   **06 - Rule Toggle Changed**
   - Toggle a rule and capture the visual feedback
   - Save as: `assets/config-editor/06-editor-toggle-[theme].png`

   **07 - Settings Panel Expanded**
   - Click "Settings" on a rule with custom settings
   - Save as: `assets/config-editor/07-editor-settings-expanded-[theme].png`

   **08 - Built-in Preset Protection**
   - Select a built-in preset showing no Edit button
   - Save as: `assets/config-editor/08-preset-protected-[theme].png`

4. **Capture both themes**:
   - Use the theme toggle button (bottom right) to switch between dark and light modes
   - Repeat all screenshots for both themes

5. **Use browser developer tools for consistent screenshots**:
   - Press F12 to open DevTools
   - Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)
   - Type "screenshot" and select "Capture full size screenshot"

---

## ✅ Testing Checklist

Use this checklist to verify all features work correctly:

### Basic Functionality
- [ ] Web interface loads without errors
- [ ] Configuration cards display correctly
- [ ] Can select different configurations
- [ ] Edit button appears for personal/team configs
- [ ] Edit button does NOT appear for built-in presets
- [ ] View Details button works for all configs

### Editor Modal
- [ ] Modal opens when clicking Edit
- [ ] Modal shows correct configuration name
- [ ] All rules are displayed
- [ ] Scrolling works correctly
- [ ] Modal can be closed with X button
- [ ] Modal can be closed with Cancel button

### Search Functionality
- [ ] Search filters rules in real-time
- [ ] Search is case-insensitive
- [ ] Clearing search shows all rules again
- [ ] Search works with partial matches

### Filter Functionality
- [ ] "All Rules" shows everything
- [ ] "Enabled Only" hides disabled rules
- [ ] "Disabled Only" hides enabled rules
- [ ] "Has Custom Settings" shows only rules with settings

### Rule Toggles
- [ ] Toggle switches change state when clicked
- [ ] Status text updates ("✓ Enabled" / "✗ Disabled")
- [ ] Visual feedback is clear
- [ ] Can toggle multiple rules

### Settings Panels
- [ ] Settings button expands the panel
- [ ] Severity dropdown shows ACTION and ADVICE
- [ ] Custom settings textarea shows current JSON
- [ ] Can edit JSON in textarea
- [ ] Multiple panels can be opened

### Saving
- [ ] Save button triggers save operation
- [ ] Success message appears on successful save
- [ ] Error message appears if JSON is invalid
- [ ] Modal closes after successful save
- [ ] Changes persist in the JSON file
- [ ] Config list refreshes after save

### Error Handling
- [ ] Invalid JSON shows clear error message
- [ ] Cannot edit built-in presets
- [ ] Helpful error messages for all failure modes

### Theme Support
- [ ] Works correctly in dark mode
- [ ] Works correctly in light mode
- [ ] Theme persists across page reloads
- [ ] All UI elements are readable in both themes

---

## 🤔 Questions for the Author

After reviewing this feature, please consider:

1. **Does this meet the requirements of Issue #10?**
   - Are there any missing capabilities?
   - Are there any unnecessary features?

2. **User Experience:**
   - Is the workflow intuitive?
   - Should we add inline help text or tooltips?
   - Should there be confirmation dialogs for destructive actions?

3. **Missing Features:**
   - Should we add the ability to create new configs from the UI?
   - Should we add the ability to delete configs?
   - Should we add the ability to duplicate/copy configs?
   - Should we show a diff view before saving?

4. **Visual Design:**
   - Does the modal size feel appropriate?
   - Should we adjust colors or spacing?
   - Should we add more visual feedback?

5. **Technical Concerns:**
   - Should we add more validation before saving?
   - Should we implement auto-save or draft functionality?
   - Should we add import/export capabilities?

---

## 📝 Implementation Notes

This feature was implemented in `feature/config-file-editor` branch with the following changes:

**Files Modified:**
- `web/server.py` - Added `/api/configs/{config_id}` and `/api/configs/create` endpoints
- `web/frontend/index.html` - Added configuration editor modal HTML
- `web/frontend/js/config-manager.js` - Added editor functionality
- `web/frontend/style.css` - Added editor styling

**Key Design Decisions:**
1. **Protected presets**: Built-in presets are read-only to prevent update conflicts
2. **JSON validation**: Client-side validation prevents invalid saves
3. **Real-time search/filter**: Improves UX for large rule sets
4. **Modal interface**: Keeps users in context without navigation

**Future Enhancements:**
- Configuration creation from UI
- Configuration duplication
- Import/export functionality
- Visual diff before save
- Undo/redo support
- Real-time JSON validation with highlighting

---

## 🙋 Support

If you encounter issues or have questions:

1. Check the browser console for JavaScript errors
2. Check the server logs for API errors
3. Verify your configuration file is valid JSON
4. Try refreshing the page to reload configurations

For bugs or feature requests, please open an issue on GitHub.
