![Arcane Auditor Logo](assets/arcane-auditor-logo.png)

*A mystical code review tool for Workday Extend applications.*

> ⚗️ **Validate. Visualize. Improve.** — PMD, Pod, and Script compliance with wizard-level precision.

![Version](https://img.shields.io/badge/version-1.2.0-blue?style=for-the-badge)
[![Download](https://img.shields.io/badge/🚀-Download_Latest-orange?style=for-the-badge)](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)
[![Support](https://img.shields.io/badge/🪄-Support_This_Project-yellow?style=for-the-badge)](https://buymeacoffee.com/developersanddragons)

---

## ✨ Overview

Arcane Auditor channels ancient wisdom through **42 validation rules** to reveal subtle code quality issues invisible to compilers but obvious to master developers.

It analyzes:

- **📄 PMD** — Page definitions with embedded scripts and endpoints
- **🧩 Pod** — Reusable widget components
- **📜 Script** — Function libraries and utilities
- **🗝️ AMD / 🔒 SMD** — Application and security manifests

**Key Traits**

- 🧙 Always-ready reviewer that understands Extend best practices
- 🔍 Precise line-level detection
- 🧠 Context-aware validation (cross-file and cross-field)
- ⚙️ Update-safe configuration layering
- 📊 Multiple output formats: Excel (desktop UI and CLI), JSON (CLI only)

## 🚀 Quick Start — Desktop App

**New in v1.2:** Arcane Auditor now ships as a native desktop application for Windows and macOS.
No Python, no browser, no setup — just download and run.

### 1. Download

Get the latest build from [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases):

| Platform       | File                | Description                               |
| -------------- | ------------------- | ----------------------------------------- |
| 🪟 **Windows** | `ArcaneAuditor.exe` | Full desktop app — double-click to launch |
| 🍎 **macOS**   | `ArcaneAuditor.dmg` | Drag to Applications and open normally    |

### 2. Install & Run

**Windows**

1. Download `ArcaneAuditor.exe`
2. Double-click to launch (no installation required)

**macOS**

1. Open `ArcaneAuditor.dmg`
2. Drag **Arcane Auditor** to Applications (optional)
3. Open from Launchpad or Finder

### 3. Analyze

Drag and drop your Extend app ZIP or individual files (`.pmd`, `.pod`, `.script`, `.amd`, `.smd`).
Results appear faster than a polymorph spell — download Excel reports as needed.

**Includes:** 42 rules, configuration presets, Excel export — fully self-contained.

> 💡 **Windows SmartScreen Notice**
>
> Even with code signing, Windows SmartScreen may show "Windows protected your PC" until the app builds download reputation with Microsoft.
>
> This is normal for new/updated releases. Click **More info** → **Run anyway** to proceed.
>
> The warning will disappear as more users successfully run the signed app.

---

## 🧩 Interfaces at a Glance

| Interface             | Best For             | Launch                                    | Highlights                             |
| --------------------- | -------------------- | ----------------------------------------- | -------------------------------------- |
| 🖥️**Desktop** | Everyone             | Native app                                | Clean UI, drag-and-drop, fast analysis |
| ⚔️**CLI**     | CI/CD and automation | `ArcaneAuditorCLI review-app myapp.zip` | Scriptable, Excel/JSON output          |

<details>
<summary>📸 Screenshots</summary>

**Dark Mode:**
![Desktop Interface - Dark Mode](assets/screenshots/results-dark.png)

**Light Mode:**
![Desktop Interface - Light Mode](assets/screenshots/results-light.png)

**Issues View:**
![Issues View](assets/screenshots/issues-dark.png)

**Issues Breakdown:**
![Issues Breakdown](assets/screenshots/details-dark.png)

**Configuration View:**
![Configuration View](assets/screenshots/config-dark.png)

</details>

---

## ⚔️ Command Line Interface

For automation, CI/CD pipelines, and power users who prefer the terminal:

**Download:**

- **Windows:** `ArcaneAuditorCLI.exe`
- **macOS:** `ArcaneAuditorCLI`

**Usage:**

```bash
# Analyze an app
ArcaneAuditorCLI review-app myapp.zip

# Use custom configuration
ArcaneAuditorCLI review-app myapp.zip --config production-ready

# Export to Excel
ArcaneAuditorCLI review-app myapp.zip --format excel --output report.xlsx

# Export to JSON for CI/CD
ArcaneAuditorCLI review-app myapp.zip --format json --output report.json
```

**Exit Codes for CI/CD:**

| Exit Code   | Meaning           | Use Case              |
| ----------- | ----------------- | --------------------- |
| **0** | ✅ Clean          | No ACTION issues      |
| **1** | ⚠️ Issues Found | ACTION issues present |
| **2** | ❌ Usage Error    | Invalid files/config  |
| **3** | 💥 Runtime Error  | Analysis failure      |

---

## ⚙️ Configuration

Arcane Auditor uses a **layered, update-safe configuration** system:

1. **Built-in Presets**
   - `development` — lenient, allows console logs / work-in-progress code
   - `production-ready` — strict, deployment-grade validation
2. **Team Configuration** (Windows: `%AppData%\ArcaneAuditor\config\rules\teams\` | macOS: `~/Library/Application Support/ArcaneAuditor/config/rules/teams/`)
3. **Personal Configuration** (Windows: `%AppData%\ArcaneAuditor\config\rules\personal\` | macOS: `~/Library/Application Support/ArcaneAuditor/config/rules/personal/`)
4. **Command-line overrides** (highest priority)

**Example personal config:**

```json
{
  "rules": {
    "ScriptConsoleLogRule": { "enabled": false },
    "ScriptLongBlockRule": {
      "custom_settings": { "max_lines": 50, "skip_comments": true }
    }
  }
}
```

Use via CLI:

```bash
ArcaneAuditorCLI review-app myapp.zip --config my-config
```

> 📖 Full reference: [Configuration Guide](docs/CONFIGURATION.md)

---

## 🧠 Validation Rules

Arcane Auditor enforces **42 rules** across two realms:

### 📜 Script Quality (23)

Complexity limits • long-function checks • unused variables/functions • naming • magic numbers • descriptive parameters

### 🗝️ Structural Integrity (19)

Widget IDs • endpoint failOnStatusCodes • naming conventions • file structure • security domain checks

> 📖 See full details: [Rule Documentation](docs/RULES.md)

---

## ⚡ Advanced Usage

<details>
<summary>🧩 Context Awareness</summary>

Arcane Auditor detects missing files and adjusts validation scope automatically:

- **Complete** when PMD + AMD + SMD provided
- **Partial** when some missing (rules skipped with clear indicators)
- Reports list skipped or partial rules and suggest required files.

</details>

<details>
<summary>🔧 Port Configuration (Desktop App)</summary>

The desktop app runs a local server (default port 8080). If you have a port conflict, edit:

**Windows:** `%AppData%\ArcaneAuditor\config\web\web_service_config.json`
**macOS:** `~/Library/Application Support/ArcaneAuditor/config/web/web_service_config.json`

```json
{
  "host": "127.0.0.1",
  "port": 8081,
  "log_level": "info"
}
```

</details>

---

## 🧑‍💻 Developer Installation (Optional)

For those extending Arcane Auditor or building from source:

```bash
# Clone and install dependencies
git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git
cd ArcaneAuditor
uv sync

# Run tests
uv run pytest
```

**UV** automatically installs and manages Python — no manual setup required.More details: [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

> 📖 For development setup, building executables, and contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🧙 Contributing

Contributions are welcome!Submit pull requests against the **`develop`** branch.

> 📖 See [CONTRIBUTING.md](CONTRIBUTING.md) and [Custom Rules Guide](docs/CUSTOM_RULES.md)

---

## 📚 Documentation

- [Rule Documentation](docs/RULES.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Custom Rules Guide](docs/CUSTOM_RULES.md)

---

## 📄 License

Licensed under the **MIT License** — see [LICENSE](LICENSE).

---

⭐ **If Arcane Auditor helps you, star the repo and share the magic!**
⚡ **Channel mana to the developer:** [Support the Weave](https://buymeacoffee.com/developersanddragons)
*May the Weave guide your code to perfection.* ✨
