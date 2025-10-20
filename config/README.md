`<a id="configuration-guide"></a>`

# Arcane Auditor Configuration Guide 📜

[⬅️ Back to Main README](../README.md) | [🧠 Rules Overview](../parser/rules/RULE_BREAKDOWN.md)

This directory contains all configuration files for the Arcane Auditor in a consolidated structure.

## 📁 Directory Structure

```
config/
├── README.md                  # This guide
├── presets/                   # Built-in configurations (app defaults)
│   ├── development.json       # Development-friendly validation
│   └── production-ready.json  # Pre-deployment validation
├── teams/                     # Team/project configurations
│   └── [your-team-configs.json]
└── personal/                  # Personal overrides (gitignored)
    └── [your-personal-configs.json]
```

## 🎯 Configuration Types — Choosing the Right Layer

| Type     | Location             | Use Case                                           | Priority   |
| -------- | -------------------- | -------------------------------------------------- | ---------- |
| Preset   | `config/presets/`  | Default app-provided configs for dev or production | 🔹 Lowest  |
| Team     | `config/teams/`    | Shared standards for your project or team          | 🔸 Medium  |
| Personal | `config/personal/` | Your private tweaks and debugging overrides        | 🔺 Highest |

### 📦 Presets (config/presets/)

Built-in configurations that come with the application:

- **development.json** - Development-friendly validation that focuses on structure and standards

  - **Disabled**: Rules that flag normal development patterns (console logs, unused code, etc.)
  - **Enabled**: Structure rules (naming, IDs, security), code quality (complexity, nesting)
  - Allows work-in-progress code without noise
  - **Use case**: Daily development, active coding, prototyping
- **production-ready.json** - Comprehensive pre-deployment validation

  - **All rules enabled** with strict settings
  - Catches console logs, unused code, and more
  - Strict enforcement of all structure and quality rules
  - **Use case**: Pre-deployment validation, CI/CD pipelines, code reviews before release

### 👥 Team Configurations (config/teams/)

Team and project-specific configurations:

- Shared across your development team
- Committed to version control (directory structure only)
- Customized for specific projects or organizational standards
- **Protected from app updates** - your customizations survive app releases
- **JSON files are gitignored** - only directory structure is tracked

### 🔒 Personal Configurations (config/personal/)

Personal developer overrides:

- Never committed to version control
- Highest priority - precedent over team and preset configs
- Perfect for debugging and personal preferences

## 🚀 Usage

### ⚔️ Command Line

```bash
# Use development configuration (recommended for daily development)
uv run main.py review-app myapp.zip --config development

# Use production-ready configuration (pre-deployment validation)
uv run main.py review-app myapp.zip --config production-ready

# Use a team configuration
uv run main.py review-app myapp.zip --config my-team-config

# Use a personal configuration
uv run main.py review-app myapp.zip --config my-personal-config
```

---

### 🌐 Web Interface

Configurations are automatically discovered and available in the web interface under:

- **Built-in Configurations** (presets)
- **Team Configurations** (teams)
- **Personal Configurations** (personal)

## 📊 Configuration Priority

When you specify a configuration on the CLI by name, the system searches in this order:

1. `config/personal/name.json` ← **Highest Priority** (Personal overrides)
2. `config/teams/name.json` ← Team/project settings
3. `config/presets/name.json` ← App defaults

## 🛠️ Creating Custom Configurations

### Team Configuration

```bash
# Copy a preset as starting point
cp config/presets/development.json config/teams/my-team-config.json

# OR use the app to generate a config
uv run main.py generate-config >config/teams/my-team-config.json

# Edit the configuration to match your team's standards
# ... customize rules as needed ...

# Use it
uv run main.py review-app myapp.zip --config my-team-config
```

### Personal Configuration

```bash
# Create personal override
echo '{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false
    }
  }
}' > config/personal/debug-mode.json

# Use it
uv run main.py review-app myapp.zip --config debug-mode
```

## 🔒 App Update Safety

| Directory            | Managed By  | Versioned          | Overwritten on Update? | Notes                         |
| -------------------- | ----------- | ------------------ | ---------------------- | ----------------------------- |
| `config/presets/`  | Application | ✅ Yes             | ⚠️ Yes               | Updated automatically         |
| `config/teams/`    | Your team   | 🚫 No (gitignored) | 🚫 No                  | Protected, JSON files ignored |
| `config/personal/` | You         | 🚫 No (gitignored) | 🚫 No                  | Private, completely ignored   |

Your team and personal configurations will never be overwritten — your preferences are safe within the Weave.

## 📚 Additional Resources

- [Rule Documentation](../parser/rules/RULE_BREAKDOWN.md) - Detailed rule descriptions
- [Custom Rules Guide](../parser/rules/custom/README.md) - Creating custom validation rules

[⬆️ Back to Top](#configuration-guide)
