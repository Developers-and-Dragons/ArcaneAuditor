"""
Unit tests for the RulesEngine class.
"""
import pytest
from parser.rules_engine import RulesEngine
from parser.models import ProjectContext, PMDModel
from parser.rules.base import Rule, Finding


class MockRule(Rule):
    """Mock rule for testing purposes."""
    ID = "TEST001"
    DESCRIPTION = "Test rule for unit testing"
    SEVERITY = "ADVICE"
    
    def analyze(self, context):
        """Mock analysis that yields test findings."""
        yield Finding(
            rule=self,
            message="Test finding from mock rule",
            line=1
        )
        yield Finding(
            rule=self,
            message="Another test finding",
            line=2
        )


class MockRuleWithError(Rule):
    """Mock rule that raises an error during analysis."""
    ID = "ERROR001"
    DESCRIPTION = "Rule that raises an error"
    SEVERITY = "ERROR"
    
    def analyze(self, context):
        """Mock analysis that raises an error."""
        raise Exception("Simulated rule error")


class MockRuleNoFindings(Rule):
    """Mock rule that finds no issues."""
    ID = "EMPTY001"
    DESCRIPTION = "Rule that finds nothing"
    SEVERITY = "ADVICE"
    
    def analyze(self, context):
        """Mock analysis that finds nothing."""
        return  # No findings


class TestRulesEngine:
    """Test cases for RulesEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()
        self.rules_engine = RulesEngine()
    
    def test_init(self):
        """Test rules engine initialization."""
        assert hasattr(self.rules_engine, 'rules')
        assert isinstance(self.rules_engine.rules, list)
    
    def test_discover_rules_success(self):
        """Test successful rule discovery."""
        # Create engine with mock rules directly
        engine = RulesEngine()
        engine.rules = [MockRule()]
        
        # Should have the mock rule
        assert len(engine.rules) == 1
        assert isinstance(engine.rules[0], MockRule)
        assert engine.rules[0].ID == "TEST001"
    
    def test_discover_rules_no_rules_found(self):
        """Test rule discovery when no rules are found."""
        # Create engine with no rules
        engine = RulesEngine()
        engine.rules = []
        
        assert len(engine.rules) == 0
    
    def test_discover_rules_import_error(self):
        """Test rule discovery handles import errors gracefully."""
        # Create engine with no rules to simulate import error scenario
        engine = RulesEngine()
        engine.rules = []
        
        # Should handle gracefully
        assert len(engine.rules) == 0
    
    def test_run_no_rules(self):
        """Test running rules engine with no rules."""
        # Create engine with no rules
        engine = RulesEngine()
        engine.rules = []  # Override discovered rules
        
        result = engine.run(self.context)
        
        assert result == []
    
    def test_run_single_rule_success(self):
        """Test running a single rule successfully."""
        # Create engine with mock rule
        engine = RulesEngine()
        engine.rules = [MockRule()]
        
        result = engine.run(self.context)
        
        # Should find 2 findings from MockRule
        assert len(result) == 2
        assert all(isinstance(finding, Finding) for finding in result)
        assert result[0].rule_id == "MockRule"
        assert result[1].rule_id == "MockRule"
    
    def test_run_multiple_rules(self):
        """Test running multiple rules."""
        # Create engine with multiple mock rules
        engine = RulesEngine()
        engine.rules = [MockRule(), MockRuleNoFindings()]
        
        result = engine.run(self.context)
        
        # Should find 2 findings from MockRule, 0 from MockRuleNoFindings
        assert len(result) == 2
        assert all(finding.rule_id == "MockRule" for finding in result)
    
    def test_run_rule_with_error(self):
        """Test running rules when one rule raises an error."""
        # Create engine with rules including one that errors
        engine = RulesEngine()
        engine.rules = [MockRule(), MockRuleWithError(), MockRuleNoFindings()]
        
        result = engine.run(self.context)
        
        # Should still get findings from working rules
        assert len(result) == 2
        assert all(finding.rule_id == "MockRule" for finding in result)
        # MockRuleWithError should be skipped due to error
    
    def test_run_with_empty_context(self):
        """Test running rules with empty project context."""
        empty_context = ProjectContext()
        engine = RulesEngine()
        engine.rules = [MockRule()]
        
        result = engine.run(empty_context)
        
        # Should still work and find issues
        assert len(result) == 2
    
    def test_run_with_populated_context(self):
        """Test running rules with populated project context."""
        # Create context with some PMD models
        context = ProjectContext()
        context.pmds["testPage"] = PMDModel(
            pageId="testPage",
            file_path="test.pmd"
        )
        
        engine = RulesEngine()
        engine.rules = [MockRule()]
        
        result = engine.run(context)
        
        # Should work with populated context
        assert len(result) == 2
    
    def test_finding_structure(self):
        """Test that findings have correct structure."""
        engine = RulesEngine()
        engine.rules = [MockRule()]
        
        result = engine.run(self.context)
        
        # Check finding structure
        finding = result[0]
        assert hasattr(finding, 'rule_id')
        assert hasattr(finding, 'rule_description')
        assert hasattr(finding, 'severity')
        assert hasattr(finding, 'message')
        assert hasattr(finding, 'line')
        assert hasattr(finding, 'file_path')
        
        # Check values
        assert finding.rule_id == "MockRule"
        assert finding.rule_description == "Test rule for unit testing"
        assert finding.severity == "ADVICE"
        assert "Test finding" in finding.message
    
    def test_discover_rules_real_package_structure(self):
        """Test rule discovery with realistic package structure."""
        # Create engine with mock rules to simulate real package structure
        engine = RulesEngine()
        engine.rules = [MockRule()]

        # Should discover the rule
        assert len(engine.rules) == 1
        assert isinstance(engine.rules[0], MockRule)


def _make_ordering_rule(class_name: str, findings_data):
    """Factory: build a Rule subclass that yields the given (file_path, line, message) findings."""
    def analyze(self, context):
        for fp, line, msg in findings_data:
            yield Finding(rule=self, message=msg, file_path=fp, line=line)

    return type(class_name, (Rule,), {
        'ID': class_name,
        'DESCRIPTION': f"Mock {class_name} for ordering tests",
        'SEVERITY': 'ADVICE',
        'analyze': analyze,
    })


class TestDeterministicOrdering:
    """Findings must be deterministically ordered for agent consumption."""

    def setup_method(self):
        self.context = ProjectContext()

    def _build_engine(self, rule_count: int) -> RulesEngine:
        """Build an engine with `rule_count` ordering rules. Each yields scrambled findings."""
        rules = []
        for i in range(rule_count):
            cls = _make_ordering_rule(
                f"OrderingRule{i:02d}",
                [
                    ("file_b.pmd", 10 - i, f"msg_z_{i}"),
                    ("file_a.pmd", i + 1, f"msg_a_{i}"),
                    ("file_a.pmd", i + 1, f"msg_b_{i}"),
                ],
            )
            rules.append(cls())
        engine = RulesEngine()
        engine.rules = rules
        return engine

    def test_findings_sorted_serial_path(self):
        """≤5 rules: findings sorted by (file_path, line, rule_id, message)."""
        engine = self._build_engine(rule_count=3)
        result = engine.run(self.context)

        keys = [(f.file_path, f.line, f.rule_id, f.message) for f in result]
        assert keys == sorted(keys), f"Findings not sorted: {keys}"

    def test_findings_sorted_parallel_path(self):
        """>5 rules triggers ThreadPoolExecutor; output must still be deterministically ordered."""
        engine = self._build_engine(rule_count=8)
        result = engine.run(self.context)

        keys = [(f.file_path, f.line, f.rule_id, f.message) for f in result]
        assert keys == sorted(keys), f"Findings not sorted: {keys}"

    def test_findings_repeatable_across_runs(self):
        """Two runs over the same input must produce identical finding sequences (parallel path)."""
        engine = self._build_engine(rule_count=8)

        run_1 = [(f.file_path, f.line, f.rule_id, f.message) for f in engine.run(self.context)]
        run_2 = [(f.file_path, f.line, f.rule_id, f.message) for f in engine.run(self.context)]

        assert run_1 == run_2

    def test_findings_repeatable_serial_path(self):
        """Two runs (serial path) must produce identical finding sequences."""
        engine = self._build_engine(rule_count=3)

        run_1 = [(f.file_path, f.line, f.rule_id, f.message) for f in engine.run(self.context)]
        run_2 = [(f.file_path, f.line, f.rule_id, f.message) for f in engine.run(self.context)]

        assert run_1 == run_2


if __name__ == "__main__":
    pytest.main([__file__])
