import inspect
import pkgutil
import importlib.util
import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Local Imports ---
from .models import ProjectContext
from . import rules
from .rules.base import Rule, Finding
from .config import ArcaneAuditorConfig
from utils.arcane_paths import get_rule_dirs
from utils.console import info, error

class RulesEngine:
    """Discovers, loads, and runs all analysis rules."""

    def __init__(self, config: Optional[ArcaneAuditorConfig] = None):
        self.config = config or ArcaneAuditorConfig()
        self.rules = self._discover_rules()

    def _discover_rules(self) -> List[Rule]:
        """
        Automatically finds and instantiates all Rule classes from both
        built-in and user-defined rule directories.
        
        Note: This method runs once at initialization. If dynamic rule reloading
        is implemented in the future, thread safety should be considered.
        """
        discovered_rules = []

        # 1. Load built-in rules using the original working approach
        self._load_builtin_rules(discovered_rules)
        
        # 2. Load user rules from custom directories
        self._load_user_rules(discovered_rules)

        return discovered_rules

    def _load_builtin_rules(self, discovered_rules: List[Rule]) -> None:
        """Load built-in rules using the original pkgutil approach."""
        # Use the original working approach for built-in rules
        for _, name, _ in pkgutil.walk_packages(rules.__path__, f"{rules.__name__}."):
            try:
                module = __import__(name, fromlist="dummy")
                self._extract_rules_from_module(module, discovered_rules, "built-in")
            except Exception as e:
                error(f"[RulesEngine] Error loading built-in rule {name}: {e}")

    def _load_user_rules(self, discovered_rules: List[Rule]) -> None:
        """Load user rules from custom directories."""
        rule_dirs = get_rule_dirs()
        for rule_dir in rule_dirs:
            # Only process user custom directories (not built-in)
            # Use basename check to avoid false positives if "custom" appears elsewhere in path
            if os.path.basename(rule_dir) == "user" and os.path.isdir(rule_dir):
                for file in os.listdir(rule_dir):
                    if file.endswith(".py") and not file.startswith("__"):
                        path = os.path.join(rule_dir, file)
                        mod_name = os.path.splitext(file)[0]
                        try:
                            spec = importlib.util.spec_from_file_location(mod_name, path)
                            if spec and spec.loader:
                                mod = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(mod)
                                self._extract_rules_from_module(mod, discovered_rules, "user")
                        except Exception as e:
                            error(f"[RulesEngine] Error loading user rule {file} from {rule_dir}: {e}")

    def _extract_rules_from_module(self, module, discovered_rules: List[Rule], rule_type: str) -> None:
        """Extract and instantiate rules from a module."""
        for member_name, member_obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(member_obj, Rule) and member_obj is not Rule:
                # Skip abstract classes
                if hasattr(member_obj, '__abstractmethods__') and member_obj.__abstractmethods__:
                    continue
                
                # Skip example rules (flagged with IS_EXAMPLE = True)
                if hasattr(member_obj, 'IS_EXAMPLE') and member_obj.IS_EXAMPLE:
                    continue
                
                # Check if rule is enabled in configuration using class name
                if self.config.is_rule_enabled(member_obj.__name__):
                    info(f"[RulesEngine] Discovered {rule_type} rule: {member_obj.__name__}")
                    rule_instance = member_obj()
                    self._apply_rule_config(rule_instance)
                    discovered_rules.append(rule_instance)
                else:
                    info(f"[RulesEngine] Skipping disabled {rule_type} rule: {member_obj.__name__}")
    
    def _apply_rule_config(self, rule: Rule) -> None:
        """Apply configuration overrides to a rule instance."""
        # Override severity if configured
        if hasattr(rule, 'SEVERITY'):
            original_severity = rule.SEVERITY
            configured_severity = self.config.get_rule_severity(rule.__class__.__name__, original_severity)
            if configured_severity != original_severity:
                rule.SEVERITY = configured_severity
                info(f"[CONFIG] Override severity for {rule.__class__.__name__}: {original_severity} -> {configured_severity}")
        
        # Apply custom settings if the rule supports it
        custom_settings = self.config.get_rule_settings(rule.__class__.__name__)
        if custom_settings and hasattr(rule, 'apply_settings'):
            rule.apply_settings(custom_settings)

    def run(self, context: ProjectContext) -> List[Finding]:
        """

        Executes all discovered rules against the project context.

        Args:
            context: The ProjectContext containing the entire application model.

        Returns:
            A list of all findings from all rules.
        """
        all_findings = []
        if not self.rules:
            info("No rules were found to run.")
            return []

        info(f"\nRunning {len(self.rules)} rule(s)...")

        if len(self.rules) <= 5:
            info("Using serial rule execution (small rule count)")
            for rule in self.rules:
                try:
                    findings_from_rule = list(rule.analyze(context))
                    if findings_from_rule:
                        all_findings.extend(findings_from_rule)
                except Exception as e:
                    error(f"Rule {rule.__class__.__name__} failed: {e}")
        else:
            # Use parallel processing for larger rule sets
            max_workers = min(8, len(self.rules))  # Cap at 8 workers for rules
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all rule execution tasks
                future_to_rule = {
                    executor.submit(self._run_rule_safe, rule, context): rule
                    for rule in self.rules
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_rule):
                    rule = future_to_rule[future]
                    try:
                        findings_from_rule = future.result()
                        if findings_from_rule:
                            all_findings.extend(findings_from_rule)
                    except Exception as e:
                        error(f"Error running rule {rule.__class__.__name__}: {e}")
        
        return all_findings
    
    def _run_rule_safe(self, rule: Rule, context: ProjectContext) -> List[Finding]:
        """Thread-safe wrapper for running a single rule."""
        try:
            return list(rule.analyze(context))
        except Exception as e:
            error(f"Rule {rule.__class__.__name__} failed: {e}")
            return []