# Quick Testing Guide: Configuration Editor

This guide will help you quickly test the new configuration editor feature.

## Quick Start (5 minutes)

### Step 1: Start the Server
```bash
cd ArcaneAuditor
./start-web-service.sh
```

Your browser will automatically open to `http://localhost:8080`

### Step 2: Create a Test Configuration
```bash
# In a new terminal
cd ArcaneAuditor
mkdir -p config/personal
cp config/presets/development.json config/personal/test-config.json
```

### Step 3: Refresh the Browser
Refresh the page to see your new `test-config` appear in the Personal section.

### Step 4: Test the Editor

1. **Click** on the "Test Config" card to select it
2. **Click** the "✏️ Edit" button that appears
3. **Try these actions**:
   - Toggle a rule on/off using the switch
   - Search for "Script" in the search bar
   - Change the filter to "Enabled Only"
   - Click "Settings" on a rule and expand it
   - Edit the JSON in the custom settings
   - Click "💾 Save Changes"

4. **Verify** the changes saved:
   ```bash
   cat config/personal/test-config.json | grep -A 5 "ScriptLongBlockRule"
   ```

## What to Look For

### ✅ Good Signs
- The Edit button appears for personal/team configs
- NO Edit button appears for built-in presets (development, production-ready)
- Toggle switches animate smoothly
- Search filters rules instantly
- Settings panels expand/collapse correctly
- Save button shows success message
- Changes persist in the JSON file

### ❌ Red Flags
- Errors in browser console (Press F12 to check)
- 500 errors in server logs
- Edit button on built-in presets
- Cannot save changes
- Page doesn't load configuration cards
- Modal doesn't open

## Visual Testing Checklist

Open the feature and verify:

- [ ] Configuration cards display with correct information
- [ ] Personal/Team configs show "✏️ Edit" button
- [ ] Built-in presets do NOT show "✏️ Edit" button
- [ ] Editor modal opens smoothly
- [ ] All 42 rules are visible in the editor
- [ ] Search bar filters rules correctly
- [ ] Filter dropdown works (All/Enabled/Disabled/Custom Settings)
- [ ] Toggle switches change state visually
- [ ] Status text updates when toggling
- [ ] Settings panels expand when clicked
- [ ] Severity dropdown shows ACTION and ADVICE
- [ ] JSON textarea shows current settings
- [ ] Save button triggers save
- [ ] Success message appears after save
- [ ] Modal closes after successful save

## Common Issues & Solutions

### Issue: No Edit button appears
**Solution:** Make sure you're selecting a personal or team config, not a built-in preset.

### Issue: Configurations don't load
**Solution:**
1. Check browser console for errors
2. Check server logs: `tail -f /tmp/server.log`
3. Verify the `/api/configs` endpoint works: `curl http://localhost:8080/api/configs`

### Issue: Cannot save changes
**Solution:**
1. Check if your JSON is valid
2. Verify file permissions on `config/personal/` directory
3. Check server logs for permission errors

### Issue: Changes don't persist
**Solution:**
1. Verify the success message appeared
2. Check the timestamp on the config file: `ls -l config/personal/test-config.json`
3. Reload the page and check if changes are visible

## Screenshot Locations

If you want to capture screenshots for documentation:

Save screenshots to: `assets/config-editor/`

Naming convention: `{number}-{description}-{theme}.png`

Examples:
- `01-config-selection-dark.png`
- `02-editor-modal-light.png`
- `03-search-functionality-dark.png`

## Quick Test Script

Run this to verify the feature works end-to-end:

```bash
#!/bin/bash

echo "🧪 Testing Configuration Editor Feature"

# 1. Start server in background
echo "1️⃣ Starting server..."
./start-web-service.sh --no-browser --port 8080 &
SERVER_PID=$!
sleep 5

# 2. Test API endpoints
echo "2️⃣ Testing API..."
curl -s http://localhost:8080/api/health | grep "healthy" && echo "✅ Server is healthy" || echo "❌ Server not responding"

# 3. Test configs endpoint
curl -s http://localhost:8080/api/configs | grep "configs" && echo "✅ Configs API works" || echo "❌ Configs API failed"

# 4. Create test config
echo "3️⃣ Creating test configuration..."
mkdir -p config/personal
cp config/presets/development.json config/personal/test-config.json && echo "✅ Test config created" || echo "❌ Failed to create test config"

# 5. Test saving (requires manual browser testing)
echo "4️⃣ Manual testing required:"
echo "   - Open http://localhost:8080 in your browser"
echo "   - Select 'Test Config'"
echo "   - Click 'Edit' button"
echo "   - Make a change and click 'Save'"

# Cleanup
echo "
5️⃣ When done testing, cleanup with:"
echo "   kill $SERVER_PID"
echo "   rm config/personal/test-config.json"
```

## Report Your Findings

After testing, please note:

1. **What worked well?**
2. **What didn't work?**
3. **What was confusing?**
4. **What features are missing?**
5. **Any bugs or issues?**

Share your feedback in the GitHub issue or PR comments.

---

**Happy Testing!** 🎉
