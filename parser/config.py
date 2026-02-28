"""
Configuration models for the Arcane Auditor tool.

This module defines the configuration structure for controlling rule execution,
file processing settings, and other tool behaviors.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class SeverityLevel(str, Enum):
    """Severity levels for findings."""
    ADVICE = "ADVICE"
    ACTION = "ACTION"


class RuleConfig(BaseModel):
    """Configuration for a single rule."""
    enabled: bool = Field(default=True, description="Whether this rule is enabled")
    severity_override: Optional[SeverityLevel] = Field(default=None, description="Override the rule's default severity")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom settings for the rule")


class RulesConfig(BaseModel):
    """Configuration for all rules using human-readable class names."""
    
    # Script Complexity & Structure Rules
    ScriptComplexityRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)")
    ScriptFunctionParameterCountRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions don't have too many parameters (max 5 parameters)")
    ScriptLongFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions don't exceed maximum line count (max 50 lines)")
    ScriptNestingLevelRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't have excessive nesting levels (max 4 levels)")
    ScriptLongBlockRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures non-function script blocks don't exceed maximum line count (max 30 lines)")
    
    # Script Code Quality Rules
    ScriptConsoleLogRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't contain console.log statements (production code)")
    ScriptVarUsageRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts use 'let' or 'const' instead of 'var' (best practice)")
    ScriptDeadCodeRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects dead code in standalone script files")
    ScriptVariableNamingRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures variables follow lowerCamelCase naming convention")
    ScriptFunctionParameterNamingRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures function parameters follow lowerCamelCase naming convention")
    ScriptArrayMethodUsageRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using array higher-order methods instead of manual loops")
    ScriptMagicNumberRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't contain magic numbers (use named constants)")
    ScriptFunctionReturnConsistencyRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions have consistent return patterns")
    ScriptStringConcatRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using template literals instead of string concatenation")
    ScriptVerboseBooleanCheckRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using concise boolean expressions")
    ScriptDescriptiveParameterRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functional method parameters use descriptive names instead of single letters")
    ScriptOnSendSelfDataRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects anti-pattern of using self.data as temporary storage in outbound endpoint onSend scripts")
    
    # Script Unused Code Rules
    ScriptEmptyFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects empty function bodies")
    ScriptUnusedFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects functions that are declared but never called")
    ScriptUnusedFunctionParametersRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects unused function parameters")
    ScriptUnusedVariableRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures all declared variables are used (prevents dead code)")
    ScriptUnusedIncludesRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects script files that are included but never used in PMD files")
    
    # Endpoint Structure Rules
    EndpointFailOnStatusCodesRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoints handle failure status codes properly")
    EndpointNameLowerCamelCaseRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint names follow lowerCamelCase convention")
    EndpointOnSendSelfDataRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint onSend methods use self.data appropriately")
    EndpointBaseUrlTypeRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values")
    NoIsCollectionOnEndpointsRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects isCollection: true on inbound endpoints which can cause tenant-wide performance issues")
    OnlyMaximumEffortRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoints do not use bestEffort to prevent masked API failures")
    NoPMDSessionVariablesRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects outboundVariable endpoints with variableScope: session which can cause performance degradation")
    
    # Widget Structure Rules
    WidgetIdRequiredRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures all widgets have required 'id' field")
    WidgetIdLowerCamelCaseRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures widget IDs follow lowerCamelCase convention")
    GridPagingWithSortableFilterableRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects grids with paging and sortableAndFilterable columns which can cause performance issues")
    
    # General Structure Rules
    HardcodedWorkdayAPIRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects hardcoded *.workday.com URLs that should use apiGatewayEndpoint for regional awareness")
    FooterPodRequiredRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures footer widgets utilize pods")
    StringBooleanRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures boolean values are not stored as strings")
    EmbeddedImagesRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects base64 encoded images and large binary content")
    PMDSectionOrderingRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures PMD file sections follow consistent ordering for better readability")
    HardcodedApplicationIdRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects hardcoded applicationId values that should be replaced with site.applicationId")
    HardcodedWidRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects hardcoded WID values that should be configured in app attributes")
    PMDSecurityDomainRule: RuleConfig = Field(default_factory=RuleConfig, description="Validates that PMD files have a securityDomains section and that it is not empty")
    OrchestrationSecurityDomainRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures Sync and Async orchestrations have at least one security domain")
    OrchestrationGlobalErrorHandlerRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures orchestrations have a global error handler (Sync, Async, BPT, Integration)")
    FileNameLowerCamelCaseRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures all file names follow lowerCamelCase naming convention")
    MultipleStringInterpolatorsRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects multiple string interpolators in a single string which should use template literals instead")


class FileProcessingConfig(BaseModel):
    """Configuration for file processing."""
    max_file_size: int = Field(default=52428800, description="Maximum file size in bytes (50MB)")
    max_zip_size: int = Field(default=524288000, description="Maximum zip file size in bytes (500MB)")
    relevant_extensions: List[str] = Field(
        default=[".pod", ".pmd", ".script", ".amd", ".smd", ".wqlquery", ".orchestration", ".suborchestration"],
        description="File extensions to process"
    )
    encoding: str = Field(default="utf-8", description="Default file encoding")
    log_level: str = Field(default="ADVICE", description="Logging level")
    chunk_size: int = Field(default=16384, description="Chunk size for file reading")
    max_concurrent_files: int = Field(default=20, description="Maximum concurrent files to process")
    fallback_encodings: List[str] = Field(
        default=["utf-8", "latin-1", "cp1252", "iso-8859-1"],
        description="Fallback encodings to try"
    )


class OutputConfig(BaseModel):
    """Configuration for output formatting."""
    format: str = Field(default="text", description="Output format (text, json, xml)")
    include_rule_details: bool = Field(default=True, description="Include rule ID and description in output")
    group_by_file: bool = Field(default=False, description="Group findings by file")
    sort_by_severity: bool = Field(default=True, description="Sort findings by severity")
    max_findings_per_rule: Optional[int] = Field(default=None, description="Maximum findings per rule (None = unlimited)")


class ArcaneAuditorConfig(BaseModel):
    """Main configuration model for the Arcane Auditor tool."""
    rules: RulesConfig = Field(default_factory=RulesConfig, description="Rule configuration")
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig, description="File processing settings")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output formatting settings")
    
    # Global settings
    fail_on_severe: bool = Field(default=False, description="Exit with error code if any SEVERE severity findings are found")
    fail_on_warning: bool = Field(default=False, description="Exit with error code if any WARNING severity findings are found")
    quiet: bool = Field(default=False, description="Suppress non-essential output")
    
    @classmethod
    def from_layers(cls) -> 'ArcaneAuditorConfig':
        """
        Load configuration from all config tiers using the centralized config manager.
        
        This method provides a standalone way to load layered configuration
        for environments like CLI startup where the full config_manager isn't needed.
        
        Returns:
            ArcaneAuditorConfig loaded from presets → teams → personal layers
        """
        from .config_manager import load_configuration
        return load_configuration()

    @classmethod
    def from_file(cls, config_path: str) -> 'ArcaneAuditorConfig':
        """Load configuration from a JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Store original config data for dynamic rule access
        original_rules_data = config_data.get('rules', {})
        
        # Handle dynamic rule configurations
        if 'rules' in config_data:
            # Start with default RulesConfig
            default_rules = RulesConfig()
            
            # Update predefined rules with JSON config, preserving type safety
            for rule_name, rule_config in config_data['rules'].items():
                if hasattr(default_rules, rule_name):
                    # Construct new RuleConfig instance to preserve type safety
                    setattr(default_rules, rule_name, RuleConfig(**rule_config))
            
            config_data['rules'] = default_rules
        
        # Create instance and store original data
        instance = cls(**config_data)
        instance._original_config_data = {'rules': original_rules_data}
        return instance
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to a JSON file."""
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
    
    def is_rule_enabled(self, rule_class_name: str) -> bool:
        """Check if a specific rule is enabled using class name."""
        # First check if it's a predefined rule
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is not None:
            return rule_config.enabled
        
        # If not predefined, check if it's in the original JSON config
        if hasattr(self, '_original_config_data') and 'rules' in self._original_config_data:
            custom_rule = self._original_config_data['rules'].get(rule_class_name)
            if custom_rule:
                return custom_rule.get('enabled', True)
        
        # If rule class name not found anywhere, assume it's enabled
        return True
    
    def get_rule_severity(self, rule_class_name: str, default_severity: str) -> str:
        """Get the severity for a rule using class name, using override if configured."""
        # First check if it's a predefined rule
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is not None and rule_config.severity_override is not None:
            return rule_config.severity_override.value
        
        # If not predefined, check if it's in the original JSON config
        if hasattr(self, '_original_config_data') and 'rules' in self._original_config_data:
            custom_rule = self._original_config_data['rules'].get(rule_class_name)
            if custom_rule and 'severity_override' in custom_rule and custom_rule['severity_override'] is not None:
                return custom_rule['severity_override']
        
        return default_severity
    
    def get_rule_settings(self, rule_class_name: str) -> Dict[str, Any]:
        """Get custom settings for a rule using class name."""
        # First check if it's a predefined rule
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is not None:
            return rule_config.custom_settings
        
        # If not predefined, check if it's in the original JSON config
        if hasattr(self, '_original_config_data') and 'rules' in self._original_config_data:
            custom_rule = self._original_config_data['rules'].get(rule_class_name)
            if custom_rule and 'custom_settings' in custom_rule:
                return custom_rule['custom_settings']
        
        return {}
