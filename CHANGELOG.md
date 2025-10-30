# Changelog

All notable changes to Arcane Auditor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
----------------------------------------------------------------------------------------------------------------------------

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
