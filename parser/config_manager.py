"""
Configuration Manager for Arcane Auditor

Provides layered configuration loading with update-safe user configurations.
Uses arcane_paths for consistent path resolution across platforms.

Structure (config/):
1. Personal configs (config/personal/) - Highest priority, personal overrides
2. Team configs (config/teams/) - Team/project customizations  
3. Preset configs (config/presets/) - Application defaults

This ensures user customizations survive application updates.
"""
from pathlib import Path
from typing import Dict, Optional
from .config import ArcaneAuditorConfig
from utils.arcane_paths import get_config_dirs


class ConfigurationManager:
    """Manages layered configuration loading with update-safe user configurations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            base_path: Base directory path. Defaults to current working directory.
        """
        self.base_path = base_path or Path.cwd()
        
        # Use arcane_paths for consistent path resolution
        dirs = get_config_dirs()
        self.config_paths = [
            Path(dirs["personal"]),   # Highest priority - personal overrides
            Path(dirs["teams"]),       # Team/project customizations
            Path(dirs["presets"])      # Lowest priority - app defaults
        ]
        
        # Simple cache for last loaded config (future enhancement)
        self._last_loaded = None  # (config_name, merged_config)
    
    def load_config(self, config_name: Optional[str] = None) -> ArcaneAuditorConfig:
        """Load configuration with layered priority system.
        
        Args:
            config_name: Configuration name (without .json extension) or full path.
                        If None, loads 'default' configuration.
        
        Returns:
            Merged ArcaneAuditorConfig with all applicable layers applied.
        """
        # Simple cache check (future enhancement - currently disabled for reliability)
        # if self._last_loaded and self._last_loaded[0] == config_name:
        #     return self._last_loaded[1]
        
        # Handle explicit file paths
        if config_name and ('/' in config_name or '\\' in config_name or config_name.endswith('.json')):
            config_path = Path(config_name)
            if config_path.exists():
                # Use .as_posix() to normalize path separators for cross-platform compatibility
                return ArcaneAuditorConfig.from_file(config_path.as_posix())
            else:
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Use default if no name provided
        config_name = config_name or "production-ready"
        
        # Find all applicable configuration files in priority order
        config_files = []
        for config_dir in self.config_paths:
            config_file = config_dir / f"{config_name}.json"
            if config_file.exists():
                config_files.append(config_file)
        
        if not config_files:
            # No fallback - raise error for non-existent config names
            raise FileNotFoundError(f"Configuration '{config_name}' not found in any config directory (personal, teams, presets)")
        
        # For specific config names, use only the highest priority config (no merging)
        # For "production-ready" config, merge all layers
        if config_name == "production-ready":
            # Load and merge configurations (lowest priority first)
            merged_config = None
            for config_file in reversed(config_files):  # Start with lowest priority (presets) as base
                try:
                    if merged_config is None:
                        # First configuration becomes the base (lowest priority)
                        merged_config = ArcaneAuditorConfig.from_file(config_file.as_posix())
                    else:
                        # Merge higher priority configuration over base
                        overlay_config = ArcaneAuditorConfig.from_file(config_file.as_posix())
                        merged_config = self._merge_configurations(merged_config, overlay_config)
                except Exception as e:
                    print(f"Warning: Failed to load configuration {config_file}: {e}")
                    continue
            
            result = merged_config or ArcaneAuditorConfig()
        else:
            # For specific config names, use only the highest priority config file
            highest_priority_config = config_files[0]  # First one is highest priority
            try:
                result = ArcaneAuditorConfig.from_file(highest_priority_config.as_posix())
            except Exception as e:
                print(f"Warning: Failed to load configuration {highest_priority_config}: {e}")
                result = ArcaneAuditorConfig()
        
        # Update cache (future enhancement)
        # self._last_loaded = (config_name, result)
        
        return result
    
    def get_config_source_info(self, config_name: Optional[str] = None) -> dict:
        """Get information about where a configuration would be loaded from.
        
        Args:
            config_name: Configuration name or None for default
            
        Returns:
            Dictionary with source information
        """
        # Use production-ready if no name provided
        config_name = config_name or "production-ready"
        
        # Handle explicit file paths
        if config_name and ('/' in config_name or '\\' in config_name or config_name.endswith('.json')):
            return {
                "type": "custom_file",
                "name": Path(config_name).stem,
                "path": config_name
            }
        
        # Check what config files exist
        config_files = []
        for config_dir in self.config_paths:
            config_file = config_dir / f"{config_name}.json"
            if config_file.exists():
                config_files.append((config_dir.name, config_file))
        
        if not config_files:
            # No fallback - return error info for non-existent config names
            return {
                "type": "error",
                "name": config_name,
                "description": f"Configuration '{config_name}' not found in any config directory (personal, teams, presets)"
            }
        
        # Determine the highest priority source
        source_dir, source_file = config_files[0]  # First one is highest priority
        
        if source_dir == "personal":
            return {
                "type": "personal",
                "name": config_name,
                "source": "personal"
            }
        elif source_dir == "teams":
            return {
                "type": "team",
                "name": config_name,
                "source": "teams"
            }
        elif source_dir == "presets":
            return {
                "type": "preset",
                "name": config_name,
                "source": "presets"
            }
        
        return {
            "type": "unknown",
            "name": config_name,
            "source": source_dir
        }
    
    def _merge_configurations(self, base: ArcaneAuditorConfig, overlay: ArcaneAuditorConfig) -> ArcaneAuditorConfig:
        """Merge two configurations with overlay taking priority.
        
        Args:
            base: Base configuration (lower priority)
            overlay: Overlay configuration (higher priority)
            
        Returns:
            Merged configuration with overlay settings overriding base settings.
        """
        # Start with base configuration data
        merged_data = base.model_dump()
        overlay_data = overlay.model_dump()
        
        # Merge rules configuration
        if "rules" in overlay_data and overlay_data["rules"]:
            merged_rules = merged_data.get("rules", {})
            
            # Merge each rule configuration
            for rule_name, overlay_rule in overlay_data["rules"].items():
                if overlay_rule is None:
                    continue
                    
                base_rule = merged_rules.get(rule_name, {})
                
                # Merge rule settings with type safety
                merged_rule = {}
                
                # Start with base rule settings
                if base_rule:
                    merged_rule.update(base_rule)
                
                # Override with overlay rule settings (preserve type safety)
                if overlay_rule.get("enabled") is not None:
                    merged_rule["enabled"] = overlay_rule["enabled"]
                
                if overlay_rule.get("severity_override") is not None:
                    merged_rule["severity_override"] = overlay_rule["severity_override"]

                if overlay_rule.get("fix_strategy_override") is not None:
                    merged_rule["fix_strategy_override"] = overlay_rule["fix_strategy_override"]

                # Merge custom_settings (deep merge)
                base_custom = base_rule.get("custom_settings", {}) if base_rule else {}
                overlay_custom = overlay_rule.get("custom_settings", {})
                if overlay_custom:
                    merged_custom = base_custom.copy()
                    merged_custom.update(overlay_custom)
                    merged_rule["custom_settings"] = merged_custom
                elif base_custom:
                    merged_rule["custom_settings"] = base_custom
                
                merged_rules[rule_name] = merged_rule
            
            merged_data["rules"] = merged_rules
        
        # Merge other top-level settings
        for key, value in overlay_data.items():
            if key != "rules" and value is not None:
                merged_data[key] = value
        
        # Create merged configuration
        try:
            merged_config = ArcaneAuditorConfig(**merged_data)
            
            # Preserve original config data for dynamic rule support
            # Merge original config data from both base and overlay
            merged_original_data = {"rules": {}}
            
            # Start with base original data
            if hasattr(base, '_original_config_data') and base._original_config_data:
                base_original_rules = base._original_config_data.get('rules', {})
                merged_original_data["rules"].update(base_original_rules)
            
            # Overlay with higher priority original data
            if hasattr(overlay, '_original_config_data') and overlay._original_config_data:
                overlay_original_rules = overlay._original_config_data.get('rules', {})
                merged_original_data["rules"].update(overlay_original_rules)
            
            # Set the merged original config data
            merged_config._original_config_data = merged_original_data
            
            return merged_config
        except Exception as e:
            print(f"Warning: Failed to create merged configuration: {e}")
            return base  # Return base configuration as fallback
    
    def list_available_configs(self) -> Dict[str, list]:
        """List all available configurations by directory.
        
        Returns:
            Dictionary mapping directory names to list of available config names.
        """
        available_configs = {}
        
        for config_dir in self.config_paths:
            if not config_dir.exists():
                continue
                
            # Use friendly directory names
            if config_dir.name == "personal":
                dir_name = "Personal Configurations"
            elif config_dir.name == "teams":
                dir_name = "Team Configurations"
            elif config_dir.name == "presets":
                dir_name = "Built-in Configurations"
            else:
                dir_name = config_dir.name
            
            configs = []
            
            for config_file in config_dir.glob("*.json"):
                # Skip files in examples subdirectory
                if "examples" in str(config_file):
                    continue
                configs.append(config_file.stem)
            
            if configs:
                available_configs[dir_name] = sorted(configs)
        
        return available_configs
    
    def validate_config_safety(self) -> Dict[str, str]:
        """Validate that user configurations are properly protected.
        
        Returns:
            Dictionary of safety status for each configuration directory.
        """
        safety_status = {}
        
        for config_dir in self.config_paths:
            if not config_dir.exists():
                safety_status[config_dir.name] = "Directory does not exist"
                continue
            
            # Check if this is an app-managed directory
            is_app_managed = (config_dir.name == "presets")
            
            if is_app_managed:
                safety_status[config_dir.name] = "App-managed (will be updated)"
            else:
                safety_status[config_dir.name] = "Protected (update-safe)"
        
        return safety_status


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def load_configuration(config_name: Optional[str] = None) -> ArcaneAuditorConfig:
    """Convenience function to load configuration using the global manager.
    
    Args:
        config_name: Configuration name or file path.
        
    Returns:
        Loaded and merged configuration.
    """
    return get_config_manager().load_config(config_name)
