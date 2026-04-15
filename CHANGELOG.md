# Changelog

All notable changes to Arcane Auditor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.6.0] - 2026-04-14

### Added

- **Desktop folder analysis** — In the desktop app, **Browse… → Project folder…** selects a local directory; analysis uses the same recursive directory processing as the CLI, preserving relative paths (including duplicate filenames in different subfolders). Gated API (`POST /api/analyze-directory`) enabled only for the desktop shell.

### Changed

- **Upload UI** — Single **Browse…** menu for ZIP archive, source files, or project folder (folder option on desktop only).

---

## [v1.5.0] - 2026-03-17

### Added

- **Linux CLI Build & Release** - Official Linux CLI artifact for CI and headless environments.
  - Single executable built with PyInstaller (onefile); distributed as `ArcaneAuditor_linux_CLI.tar.gz` with SHA-256 checksum.
  - Built on Ubuntu 22.04 in GitHub Actions; included in tagged releases alongside Windows and macOS assets.
- **Docker Definition Files** - Repo includes Dockerfiles for running the CLI in containers (definition files only; no prebuilt images published).
  - `Dockerfile.cli-src` - Run CLI from source with `uv` (development/CI experimentation).
  - `Dockerfile.cli-binary` - Run the built Linux CLI binary (minimal runtime, CI/production-style).
  - See [docker/README.md](docker/README.md) for build and run examples.
- **`--ci` CLI Preset** - One flag for CI/CD: quiet output, JSON format, and default output file (`arcane-auditor-results.json`); overridable with `--format` and `--output`.
- **Orchestration Support** - Validation for `.orchestration` and `.suborchestration` files; rule count increased to 48 with orchestration-specific rules (security domains, error handlers, branching, expression best practices).
- **Linux Configuration Paths** - Documented config locations for Linux CLI: `~/.config/ArcaneAuditor/config/rules/teams/` and `~/.config/ArcaneAuditor/config/rules/personal/`.

### Changed

- **README (v1.5)** - Updated for Linux CLI download/usage, Docker subsection, interface table (CLI on Windows, macOS, Linux), and configuration paths; Quick Start highlights v1.5 features.
- **Release Workflow** - Added Linux CLI job; release artifact naming: `ArcaneAuditor_linux_CLI.tar.gz` and `ArcaneAuditor_linux_CLI.tar.gz.sha256`.

### Fixed
- **Closes #53** - Finding text fix
- **Closes #52** - Control character (tab) not escaped properly
- **Closes #19** - CLI quiet flag...noisy
- **Closes #12** - Security domains on Orchs (validation rule)
- **Closes #11** - Orch support!

---

## [v1.4.0] - 2025-12-02

### Added

- **Interactive Rules Grimoire** - Complete documentation system for all 42 rules with searchable index, categorized browsing, detailed examples, and markdown-formatted explanations accessible from anywhere in the UI.
- **In-app Rule Configuration** - Custom settings UI for rules that support advanced configuration, enabling/disabling of rules, and more!
- **Global Grimoire Access** - Floating button and integrated documentation links throughout the configuration interface for instant rule reference.
- **UX Onboarding Improvements** - Unified control panel design, configuration section headers, and dynamic status badges to improve discoverability for new users.

### Changed

- **Results Module Architecture** - Refactored monolithic results renderer into modular structure with separated templates, UI components, and controller logic for better maintainability.
- **Configuration UI Refactoring** - Split large CSS files into feature-specific modules and extracted configuration logic into dedicated JavaScript modules.
- **Light Mode Polish** - Enhanced visual depth, shadows, and hover effects for Grimoire cards and modal interfaces.
- **Modal Ergonomics** - Optimized modal dimensions with shrink-wrap behavior and fixed desktop width for consistent experience across screen sizes.
- **Configuration Cards** - Gone are the huge configuration cards, in favor of a less dominant presence. 


### Fixed

- **Closes #10** - New configuration file editor.
- **Closes #27** - The move away from Configuration Cards eliminates this issue.
- **Closes #42** - In-app rule details (Grimoire).

---

## [v1.3.0] - 2025-11-11

### Added

- **Version Awareness Everywhere** - Packaging-driven source of truth now surfaces through the `__version__` module, CLI `--version` flag, desktop splash/title, and the web UI badge.
- **Automated Update Detection** - Full update checker stack with FastAPI endpoints, desktop bridge, and web wiring backed by a preferences manager with opt-in, timestamp, and cache fields.
- **In-App Settings Panel** - Hover-expanding settings orb lets users toggle automated update checks without leaving the primary workflow.

### Changed

- **Preferences Schema & Storage** - Atomic writes, schema migrations, and normalized legacy keys safeguard future settings expansions.
- **Frontend Controls & Layout** - Theme toggle restyled as a hover orb with modularized CSS bundles for maintainability and responsiveness.
- **Update Caching Strategy** - Server and desktop health checks reuse GitHub responses for five minutes to respect external rate limits.

### Fixed

- **macOS DMG Detection** - Correctly recognizes mounted volumes, prevents premature exits, and improves relocation guidance.
- **Structure Rule Reliability** - PMD section ordering and string-boolean checks ignore underscore-prefixed (commented) keys, resolving issue #46.
- **Script Rule Accuracy** - Stops flagging top-level constants as unused and consistently detects magic numbers in simple return statements.
- **Manifest Naming Expectations** - AMD/SMD naming enforcement skips platform-generated files and tabbed PMD sections evaluate correctly.

---

## [v1.2.0] - 2025-10-30

### Added

- **🖥️ Native Desktop Application** - Cross-platform desktop app for Windows and macOS
  - Instant startup with optimized splash screen
  - Centered splash window on both platforms
  - No scrollbars or visual artifacts
  - localStorage persistence for settings
  - Platform-specific storage paths
- **Code Signing** - Windows executables are now digitally signed
- **macOS Notarization** - Full Apple notarization for seamless macOS experience
- **Cross-Platform Support** - macOS builds with DMG distribution
- **Mystical Project Board** - "Academy of Arcana" GitHub Project for task management
- **Support the Weave** - Buy Me a Coffee integration

### Changed

- **Desktop-First Documentation** - Completely rewritten README focusing on desktop app
- **Reorganized Documentation** - Moved to `docs/` folder with clear naming
- **Platform-Specific Paths** - Documentation includes Windows and macOS paths
- **CLI as Secondary** - Positioned for power users and CI/CD
- **Build Optimization** - macOS onedir mode, Windows onefile mode

### Removed

- **Web Server from User Docs** - De-emphasized web server in favor of desktop app
- **Windows-Only Messaging** - Now fully cross-platform
- **Confusing Installation Options** - Streamlined to Desktop → CLI → Source

**Closes #20** - Completes cross-platform package distribution (macOS support added, desktop app fully implemented)
---------------------------------------------------------------------------------------------------------------

## [v1.1.0] - 2025-10-24

### Added

- **Windows Executable Packages** - Self-contained executables requiring no installation
  - `ArcaneAuditorWeb.exe` - Web interface with drag-and-drop convenience
  - `ArcaneAuditorCLI.exe` - Command-line interface for CI/CD pipelines
  - All 42 validation rules included
  - Automatic browser launch
  - Complete dependency bundling
- **Enhanced Configuration System** - New `config/rules/` directory structure
  - Default config now uses `production-ready` (no silent fallbacks)
  - Sample configs automatically created in AppData for executable users
  - Consistent error handling for non-existent config names
- **Web Service Configuration** - New `web_service_config.json` for customization
  - Host, port, browser auto-open, and log level settings
  - Command-line argument override support
  - Auto-creation for executable users

### Changed

- **Grammar & Parser** - Grammar caching for improved performance
- **Configuration Management** - Better developer vs packaged mode detection
- **Build & CI/CD** - PowerShell build script and GitHub Actions automation
- **Documentation Overhaul** - Windows executable as primary installation method
  - Streamlined interface comparison
  - Updated configuration examples with new paths
  - SmartScreen warning guidance
  - macOS user guidance for developer installation

### Fixed

- Custom rule loading from AppData in developer mode
- Config name vs path error handling inconsistency
- Configuration type display in frozen version
- `arcane_paths.py` developer mode detection

### Breaking Changes

- **Configuration Paths** (UV/Python users only) - Move configs:
  - `config/personal/` → `config/rules/personal/`
  - `config/teams/` → `config/rules/teams/`
- **Default Configuration** - Now uses `production-ready` instead of implicit `development` fallback

---

## [v1.0.1] - 2025-10-21

### Fixed

- **Config Breakdown Modal** - Restored comprehensive rule details view
  - Fixed broken modal affected during UI refactoring
  - Improved badge positioning to prevent overlapping
  - Enhanced layout with 2-column grid
  - Added orange theme for disabled rules in light mode
  - Fixed results page colors from conflicting CSS
- **Code Quality** - Cleaned up dead code and unused CSS/JavaScript references

*Fixes GitHub Issue #21*

---

## [v1.0.0] - 2025-10-20

### Added

- **42 Validation Rules** - Complete rule set for Workday Extend
  - 10 ACTION rules (critical issues)
  - 32 ADVICE rules (best practices)
  - Coverage: Scripts, Structure, Endpoints, Widgets, PMD organization
- **Smart Configuration System**
  - Built-in presets: `development`, `production-ready`
  - Team configs for shared standards
  - Personal configs for debugging
  - Update-safe configuration (never overwritten)
- **Custom Rules Framework**
  - Create organization-specific rules
  - Example rules included
  - Unified architecture (ScriptRuleBase, StructureRuleBase)
  - Drop-in: Add to `custom/user/` directory
- **Developer Experience**
  - Dark and light mode web themes
  - Performance optimizations (AST caching, hash-based line tracking)
  - Config breakdown viewer
  - Beautiful, readable violation reports
- **Comprehensive Documentation**
  - Complete Rule Catalog
  - Custom Rules Guide
  - Configuration Guide

---

*Built for the Workday Extend community* 🔮✨

*May the Weave guide your code to perfection.*
