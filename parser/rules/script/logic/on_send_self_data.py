"""Script rule for detecting anti-pattern in onSend scripts."""

from typing import Generator, List, Tuple
from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from ....models import PMDModel
from .on_send_self_data_detector import OnSendSelfDataDetector


class ScriptOnSendSelfDataRule(ScriptRuleBase):
    """Detects the anti-pattern of using self.data as temporary storage in outbound endpoint onSend scripts."""

    DESCRIPTION = "Detects anti-pattern of using self.data as temporary storage in outbound endpoint onSend scripts"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.LOCALIZED
    DETECTOR = OnSendSelfDataDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Using `self.data` as temporary storage in onSend scripts is an anti-pattern that obscures intent and pollutes the `self` reference with unnecessary properties. When developers write patterns like `self.data = {:}` followed by building up that object and returning it, they're using the endpoint's `self` reference as a temporary variable holder instead of using proper local variables.

**This makes code harder to understand** because readers must determine whether `self.data` contains important endpoint state or is just temporary storage. It also makes testing and debugging more difficult since the `self` object is being mutated unnecessarily.

**What This Rule Does:** This rule detects when `self.data` is **assigned a new object** (empty or populated) in outbound endpoint onSend scripts. This pattern indicates the developer is using `self.data` as temporary storage. Property assignments to existing data like `self.data.foo = 'bar'` are allowed (for cases where data comes from valueOutBinding).

**Note:** This rule only applies to **outbound** endpoints. Inbound endpoints are not checked.''',
        'catches': [
            '`self.data = {:}` - Using self.data as temporary storage (empty object)',
            '`self.data = {\'foo\': \'bar\'}` - Using `self.data` as temporary storage (populated object)',
            'Any assignment that creates a new `self.data` object'
        ],
        'allows': [
            '`self.data.foo = \'bar\'` - Property assignment to existing data (✅ OK - assumes `self.data` is created from valueOutBinding)',
            'Creating local variables: `let postData = {:}` (✅ Recommended)'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Anti-pattern - Using self.data as temporary storage
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      self.data = {:};  // Pollutes self reference
      self.data.foo = 'bar';
      self.data.baz = computeValue();
      return self.data;  // Returns temporary storage
    %>"
  }]
}
```

**Fix:**

```javascript
// ✅ Good - Use local variable for clarity
{
  "outboundEndpoints": [{
    "name": "sendData",
    "onSend": "<%
      let postData = {:};  // Clear intent: local temporary variable
      postData.name = 'John';
      postData.age = 30;
      postData.computed = computeValue();
      return postData;  // Return the local variable
    %>"
  }]
}
```''',
        'recommendation': 'Use local variables instead of `self.data` for temporary storage in onSend scripts. This makes code clearer and prevents polluting the `self` reference. Property assignments to existing `self.data` (from valueOutBinding) are allowed.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _analyze_pmd(self, pmd_model: PMDModel, context) -> Generator[Finding, None, None]:
        """Analyze PMD file specifically for outbound endpoint onSend scripts."""
        # Only check outbound endpoints
        if not pmd_model.outboundEndpoints or not isinstance(pmd_model.outboundEndpoints, list):
            return
        
        for i, endpoint in enumerate(pmd_model.outboundEndpoints):
            if not isinstance(endpoint, dict):
                continue
            
            endpoint_name = endpoint.get('name', f'unnamed_outbound_{i}')
            on_send = endpoint.get('onSend', '')
            
            if not on_send or not on_send.strip():
                continue
            
            # Get line offset for the onSend field
            line_offset = self._get_on_send_line_offset(pmd_model, endpoint_name)
            
            # Check the onSend script using the detector
            findings = self._check(on_send, f"outbound endpoint '{endpoint_name}'", pmd_model.file_path, line_offset, context)
            
            # Add endpoint name to the finding messages
            for finding in findings:
                # Update the message to include endpoint name
                finding.message = f"Outbound endpoint '{endpoint_name}' onSend script uses 'self.data' as temporary storage. Use a local variable instead (let postData = {{...}}) for clarity and proper scoping."
                yield finding
    
    def _get_on_send_line_offset(self, pmd_model: PMDModel, endpoint_name: str) -> int:
        """Get line offset for onSend field in the source."""
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the endpoint name first
            endpoint_line = -1
            for i, line in enumerate(lines):
                if f'"name": "{endpoint_name}"' in line or f'"name":"{endpoint_name}"' in line:
                    endpoint_line = i
                    break
            
            if endpoint_line >= 0:
                # Look for the onSend field after the endpoint name
                for i in range(endpoint_line, min(endpoint_line + 20, len(lines))):
                    if '"onSend"' in lines[i]:
                        # Return the line after "onSend": where the script starts
                        return i + 2  # +1 for 0-based to 1-based, +1 for script start
            
            return 1
        except Exception:
            return 1

