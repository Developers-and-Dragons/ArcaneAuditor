![Arcane Auditor Logo](assets/arcane-auditor-logo.png)

*A mystical code review tool for Workday Extend applications.*

> ⚗️ **Validate. Visualize. Improve.** — PMD, Pod, and Script compliance with wizard-level precision.

![Version](https://img.shields.io/badge/version-1.6.0-blue?style=for-the-badge)
[![Download](https://img.shields.io/badge/🚀-Download_Latest-orange?style=for-the-badge)](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)
[![Support](https://img.shields.io/badge/🪄-Support_This_Project-purple?style=for-the-badge)](https://buymeacoffee.com/developersanddragons)

---

## ✨ Overview

Arcane Auditor channels ancient wisdom through **48 validation rules** to reveal subtle code quality issues invisible to compilers but obvious to master developers.

It analyzes:

- **📄 PMD** — Page definitions with embedded scripts and endpoints
- **🧩 Pod** — Reusable widget components
- **📜 Script** — Function libraries and utilities
- **🔄 Orchestration** — All templates + suborchestrations
- **🗝️ AMD / 🔒 SMD** — Application and security manifests

**Key Traits**

- 🧙 Always-ready reviewer that understands Extend best practices
- 🔍 Precise line-level detection
- 🧠 Context-aware validation (cross-file and cross-field)
- ⚙️ Update-safe configuration layering
- 📊 Multiple output formats: Excel (desktop UI and CLI), JSON (CLI only)

**New in v1.6:**
 * **Desktop: analyze a project folder** — pick a directory on disk for recursive analysis (same model as the CLI), with a Browse menu for ZIP, files, or folder.

**Earlier highlights (v1.5):**
 * Orchestration support — additional validations for orchestrations.
 * Linux CLI builds (tar.gz + SHA-256).
 * Docker definition files for CI/container workflows.
---

## 🚀 Quick Start — Desktop App


### 1. Download

Get the latest build from [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases):

| Platform                      | File                                | Description                                                        |
| ----------------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| 🪟**Windows (Desktop)** | `ArcaneAuditor.exe`               | Full desktop app — double-click to launch                         |
| 🍎**macOS (Desktop)**   | `ArcaneAuditor_macOS_Desktop.dmg` | Double click DMG, drag **Arcane Auditor.app** to Applications |
| ⚙️**Windows (CLI)**   | `ArcaneAuditorCLI.exe`            | Command-line analyzer for automation and CI/CD                     |
| ⚙️**macOS (CLI)**     | `ArcaneAuditor_macOS_CLI.zip`     | Unzip and run `ArcaneAuditorCLI` from Terminal                   |
| 🐧**Linux (CLI)**     | `ArcaneAuditor_linux_CLI.tar.gz`                | CLI only; verify with included `ArcaneAuditor_linux_CLI.tar.gz.sha256` |

> 🧩 **Note for macOS users:**
> The first time you open the app or CLI, macOS Gatekeeper may show
> “App is from an unidentified developer.”
> Right-click → **Open** once to approve; future launches will be trusted.

### 2. Install & Run

**Windows**

1. Download `ArcaneAuditor.exe`
2. Double-click to launch (no installation required)

**macOS**

1. Open `ArcaneAuditor_macOS_Desktop.dmg`
2. Drag **Arcane Auditor.app** to Applications
3. Open from Launchpad or Finder

### 3. Analyze

Drag and drop your Extend app ZIP or individual files (`.pmd`, `.pod`, `.script`, `.orchestration`, `.suborchestration`, `.amd`, `.smd`).
Results appear faster than a polymorph spell — download Excel reports as needed.

**Includes:** 48 rules, configuration presets, Excel export — fully self-contained.

> 💡 **Windows SmartScreen Notice**
> Even with code signing, Windows SmartScreen may show “Windows protected your PC” until the app builds download reputation with Microsoft.
> This is normal for new/updated releases. Click **More info** → **Run anyway** to proceed.
> The warning will disappear as more users successfully run the signed app.

---

## 🧩 Interfaces at a Glance

| Interface             | Best For                    | Launch                                    | Highlights                             |
| --------------------- | --------------------------- | ----------------------------------------- | -------------------------------------- |
| 🖥️**Desktop** | Everyone                    | Native app (Windows/macOS)                 | Clean UI, drag-and-drop, fast analysis |
| ⚔️**CLI**     | CI/CD, automation, Docker   | `ArcaneAuditorCLI review-app myapp.zip` | Windows, macOS, Linux; Excel/JSON     |

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

</details>

---

## ⚔️ Command Line Interface

For automation, CI/CD pipelines, and power users who prefer the terminal:

**Download:**

- **Windows:** `ArcaneAuditorCLI.exe`
- **macOS:** `ArcaneAuditor_macOS_CLI.zip` (unzip to get `ArcaneAuditorCLI`)
- **Linux (CLI only):** `ArcaneAuditor_linux_CLI.tar.gz` and matching `ArcaneAuditor_linux_CLI.tar.gz.sha256`

**Usage:**

```bash
# Analyze an app
ArcaneAuditorCLI review-app myapp.zip

# Use specific configuration
ArcaneAuditorCLI review-app myapp.zip --config production-ready

# Export results to Excel
ArcaneAuditorCLI review-app myapp.zip --format excel --output report.xlsx

# CI/CD: one flag for quiet, JSON, and default output file (arcane-auditor-results.json)
ArcaneAuditorCLI review-app myapp.zip --ci

# Or specify format/output explicitly
ArcaneAuditorCLI review-app myapp.zip --format json --output report.json
```

**For CI/CD pipelines:** use `--ci` to enable a preset that is quiet (no status chatter), outputs JSON, and writes to a default file (`arcane-auditor-results.json`) unless you pass `--output`. You can still override with `--format` or `--output` when needed.

**Using the Linux CLI:**

1. Download the `.tar.gz` from [Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases).
2. Verify the archive: `sha256sum -c ArcaneAuditor_linux_CLI.tar.gz.sha256`
3. Extract: `tar xzf ArcaneAuditor_linux_CLI.tar.gz`
4. Run: `./ArcaneAuditorCLI review-app myapp.zip` (or add to PATH).

**Docker (definition files only):** The repo includes Dockerfiles for running the CLI from source (`Dockerfile.cli-src`) or from the built Linux binary (`Dockerfile.cli-binary`). These are definition files only — no prebuilt images are published. Build and run locally or in your CI; use a `/work` (or similar) mount for the app under analysis. See [docker/README.md](docker/README.md) for build and run examples.

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
2. **Team Configuration**
   - Windows: `%AppData%\ArcaneAuditor\config\rules\teams\`
   - macOS: `~/Library/Application Support/ArcaneAuditor/config/rules/teams/`
   - Linux (CLI): `~/.config/ArcaneAuditor/config/rules/teams/`
3. **Personal Configuration**
   - Windows: `%AppData%\ArcaneAuditor\config\rules\personal\`
   - macOS: `~/Library/Application Support/ArcaneAuditor/config/rules/personal/`
   - Linux (CLI): `~/.config/ArcaneAuditor/config/rules/personal/`
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

Arcane Auditor enforces **48 rules** across two realms:

### 📜 Script Quality (22)

Complexity limits • long-function checks • unused variables/functions • naming • magic numbers • descriptive parameters

### 🗝️ Structural Integrity (26)

Widget IDs • endpoint failOnStatusCodes • naming conventions • file structure • security domain checks • orchestration (error handlers, security domains, branching, expression best practices)

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

The desktop app runs a local server (default port 8080).
If you have a port conflict, edit:

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
```

**UV** automatically installs and manages Python (tested with **Python 3.12.6**) — no manual setup required. More details: [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

> 📖 For development setup, building executables, and contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🧙 Contributing

Contributions are welcome! Submit pull requests against the **`develop`** branch.

> 📖 See [CONTRIBUTING.md](CONTRIBUTING.md) and [Custom Rules Guide](docs/CUSTOM_RULES.md)

---

## 📚 Documentation

- [Rule Documentation](docs/RULES.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Custom Rules Guide](docs/CUSTOM_RULES.md)
- [Docker (CLI)](docker/README.md) — source-run and binary-run images for CI/containers

---

## 📄 License

Licensed under the **MIT License** — see [LICENSE](LICENSE).

---

⭐ **If Arcane Auditor helps you, star the repo and share the magic!**
⚡ **Channel mana to the developer:** [Support the Weave](https://buymeacoffee.com/developersanddragons)
*May the Weave guide your code to perfection.* ✨
