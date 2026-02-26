"""
Key insight: 
- Script parsing (parse_with_preprocessor) uses preprocess() for EXTRACTED script code
- File parsing (preprocess_pmd_content) needs to track FULL file with <% %> tags
"""

import re
import hashlib
from typing import Tuple, List, Dict

class PMDPreprocessor:
    def __init__(self, warn_ambiguous=True):
        self.warn_ambiguous = warn_ambiguous
        self.warnings = []
    
    def preprocess(self, code: str) -> str:
        """
        Disambiguate { tokens into #{ for sets, and { for objects/blocks.
        Used by parse_with_preprocessor() for .script files and extracted PMD scripts.
        """
        # Handle newlines in PMD script blocks first, regardless of content type
        code = self._preprocess_newlines_in_script_blocks(code)
        
        # Skip brace disambiguation for JSON content - JSON doesn't have set/block ambiguity
        if self._is_json_content(code):
            return code
            
        result = []
        i = 0
        
        while i < len(code):
            if code[i] == '{':
                # Classify this brace
                brace_type, context = self._classify_brace(code, i)
                
                if brace_type == 'EXPR':
                    # Replace { with #{} for set literals in expression context
                    result.append('#{')
                elif brace_type == 'OBJECT':
                    # Keep { as-is for object literals
                    result.append('{')
                elif brace_type == 'BLOCK':
                    # Keep { as-is for blocks
                    result.append('{')
                elif brace_type == 'STRING':
                    # Keep { as-is for braces inside string literals
                    result.append('{')
                elif brace_type == 'COMMENT':
                    # Keep { as-is for braces inside comments
                    result.append('{')
                else:  # UNKNOWN
                    if self.warn_ambiguous:
                        line_num = code[:i].count('\n') + 1
                        self.warnings.append(
                            f"Line {line_num}: Ambiguous brace, defaulting to BLOCK. "
                            f"Context: {context}"
                        )
                    result.append('{')
                
                i += 1  # Skip the original {
            else:
                result.append(code[i])
                i += 1
        
        return ''.join(result)
    
    def preprocess_with_line_tracking(self, code: str) -> Tuple[str, Dict[str, List[List[int]]]]:
        """
        Used by preprocess_pmd_content() to track where scripts are located.
        
        Returns:
            tuple: (processed_content, hash_to_lines)
        """
        # STEP 1: Extract script blocks and track their line numbers BEFORE any modification
        hash_to_lines = self._extract_script_blocks_with_lines(code)
        
        # STEP 2: Now do the normal preprocessing (newline escaping + brace disambiguation)
        # This is the same as preprocess() but we keep track of the hash mappings
        processed_code = self.preprocess(code)
        
        return processed_code, hash_to_lines
    
    def _extract_script_blocks_with_lines(self, code: str) -> Dict[str, List[List[int]]]:
        """
        Find all <% %> script blocks in FULL FILE and track their line numbers.
        
        This only looks at FULL PMD/Pod files, not extracted script code.
        
        Returns:
            Dict mapping SHA256 hash -> list of line number ranges
        """
        hash_to_lines = {}
        i = 0
        current_line = 1
        
        while i < len(code):
            # Track line numbers
            if code[i] == '\n':
                current_line += 1
                i += 1
                continue
            
            # Look for script block start
            if code[i:i+2] == '<%':
                script_start_line = current_line
                
                # Find the end
                end_pos = code.find('%>', i + 2)
                if end_pos == -1:
                    break  # Unclosed
                
                # Extract FULL block including <% %>
                script_block = code[i:end_pos+2]
                
                # Count lines in this block
                lines_in_block = script_block.count('\n')
                script_end_line = current_line + lines_in_block
                
                # Create line range
                line_range = list(range(script_start_line, script_end_line + 1))
                
                # Hash the ORIGINAL content (before any escaping)
                content_hash = hashlib.sha256(script_block.encode('utf-8')).hexdigest()
                
                # Store mapping
                if content_hash not in hash_to_lines:
                    hash_to_lines[content_hash] = []
                hash_to_lines[content_hash].append(line_range)
                
                # Move past this block
                current_line = script_end_line
                i = end_pos + 2
            else:
                i += 1
        
        return hash_to_lines
    
    # ===== ALL YOUR EXISTING METHODS BELOW - UNCHANGED ===== 
    
    def _classify_brace(self, code: str, pos: int) -> Tuple[str, str]:
        """
        Classify { at position pos.
        Returns: (type, context_snippet)
        type: 'EXPR', 'OBJECT', 'BLOCK', 'STRING', 'COMMENT', or 'UNKNOWN'
        """
        # First check if we're inside a string literal (quoted string or template literal)
        if self._is_inside_string_literal(code, pos):
            return ('STRING', 'inside string literal')
        
        # Check if we're inside a comment
        if self._is_inside_comment(code, pos):
            return ('COMMENT', 'inside comment')
        
        # Get context before the brace (up to 200 chars to handle long conditions)
        start = max(0, pos - 200)
        before = code[start:pos]
        context_snippet = before[-50:] if len(before) > 50 else before
        
        # Smart lookahead - skip comments and whitespace until we find meaningful content
        after_content = self._get_meaningful_content_after_brace(code, pos)
        
        # Pattern 1: {:} is always an empty object (expression)
        if after_content.startswith(':}'):
            return ('OBJECT', context_snippet)
        
        # Pattern 2: { followed by quoted key: is always object (expression)
        if re.match(r'^["\'][^"\']+["\']\s*:', after_content):
            return ('OBJECT', context_snippet)
        
        # Pattern 2b: { followed by unquoted key: is always object (expression)
        if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*\s*:', after_content):
            return ('OBJECT', context_snippet)
        
        # Pattern 3: { preceded by =, comma, [, ( is expression context
        # This handles: var x = {}, func({}), arr[{}]
        # IMPORTANT: Use \s* to handle newlines/whitespace
        if re.search(r'[=,\(\[]\s*$', before):
            # Check if this looks like an object literal by looking ahead
            # If it's followed by a property assignment (key: value), it's an object
            if re.search(r'^\s*[a-zA-Z_$][a-zA-Z0-9_$]*\s*:', after_content):
                return ('OBJECT', context_snippet)
            # If it's followed by quoted key, it's an object
            if re.match(r'^\s*["\'][^"\']*["\']\s*:', after_content):
                return ('OBJECT', context_snippet)
            # Otherwise, it's likely a set literal
            return ('EXPR', context_snippet)
        
        # Pattern 3b: { preceded by colon (inside object literal)
        # This handles: {"key": {}, "other": {}}
        if re.search(r':\s*$', before):
            return ('EXPR', context_snippet)
        
        # Pattern 3c: { preceded by return is expression context
        # This handles: return {}, return {1, 2, 3}
        if re.search(r'\breturn\s*$', before):
            return ('EXPR', context_snippet)
        
        # Pattern 4: { preceded by control flow keyword + ) is block
        # Handle: if (...) {, while (...) {\n, for (...)\n{
        # Allow whitespace and newlines between ) and {
        if re.search(r'\b(if|else\s+if|while|for)\b[^{]*\)\s*$', before, re.DOTALL):
            return ('BLOCK', context_snippet)
        
        # Pattern 5a: { preceded by function keyword is block (function body)
        # Handle: function foo() {, function() {\n
        if re.search(r'\bfunction\b[^{]*\)\s*$', before, re.DOTALL):
            return ('BLOCK', context_snippet)
        
        # Pattern 5b: { preceded by => is block (arrow function body)
        # Handle: () => {, x => {\n
        if re.search(r'=>\s*$', before):
            return ('BLOCK', context_snippet)
        
        # Pattern 6: { preceded by else (without if) is block
        # Handle: else {, else\n{
        if re.search(r'\belse\s*$', before):
            return ('BLOCK', context_snippet)
        
        # Pattern 7: { preceded by do is block
        # Handle: do {, do\n{
        if re.search(r'\bdo\s*$', before):
            return ('BLOCK', context_snippet)
        
        # Pattern 8: { at start of statement (after ; or newline or start of file)
        # This catches standalone blocks, but only if it's actually a statement context
        # For standalone expressions (like in tests), default to EXPR
        if re.search(r'(^|[;\n])\s*$', before):
            # If this looks like it might be a standalone expression (has commas or other expression indicators),
            # treat it as EXPR rather than BLOCK
            if re.search(r'[,+*/%-]', after_content) or ',' in after_content or len(after_content.strip()) > 5:
                return ('EXPR', context_snippet)
            return ('BLOCK', context_snippet)
        
        # If we can't determine, return UNKNOWN
        return ('UNKNOWN', context_snippet)
    
    def _is_inside_string_literal(self, code: str, pos: int) -> bool:
        """
        Check if the position is inside a string literal (quoted string or template literal).
        """
        # Look backwards from the position to find the start of the current string
        i = pos - 1
        in_string = False
        string_start_char = None
        escape_next = False
        
        while i >= 0:
            char = code[i]
            
            if escape_next:
                escape_next = False
                i -= 1
                continue
            
            if char == '\\':
                escape_next = True
                i -= 1
                continue
            
            # Check for string delimiters
            if char in ['"', "'", '`']:
                if not in_string:
                    # Starting a new string
                    in_string = True
                    string_start_char = char
                elif char == string_start_char:
                    # Ending the current string
                    in_string = False
                    string_start_char = None
            
            i -= 1
        
        return in_string
    
    def _is_inside_comment(self, code: str, pos: int) -> bool:
        """
        Check if the position is inside a comment (line comment // or block comment /* */).
        """
        # Find the start of the current line for line comment detection
        line_start = code.rfind('\n', 0, pos) + 1
        
        # Check if we're in a line comment
        line_content = code[line_start:pos]
        if '//' in line_content:
            # Find the position of the last // before our position
            last_comment = line_content.rfind('//')
            # Check if there are any string delimiters between // and our position
            content_after_comment = line_content[last_comment + 2:pos - line_start]
            if not self._has_unclosed_string_delimiters(content_after_comment):
                return True
        
        # Check if we're in a block comment
        # Look for /* before our position and */ after it
        block_start = code.rfind('/*', 0, pos)
        if block_start != -1:
            # Check if there's a matching */ after our position
            block_end = code.find('*/', pos)
            if block_end != -1:
                return True
        
        return False
    
    def _has_unclosed_string_delimiters(self, content: str) -> bool:
        """Check if content has unclosed string delimiters."""
        in_string = False
        string_char = None
        escape_next = False
        
        for char in content:
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char in ['"', "'", '`']:
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
        
        return in_string
    
    def _is_json_content(self, code: str) -> bool:
        """
        Detect if the content is JSON rather than PMD script.
        JSON content should not be preprocessed since it doesn't have set/block ambiguity.
        """
        # Strip whitespace to check first character
        stripped = code.strip()
        
        # JSON typically starts with { or [
        if not (stripped.startswith('{') or stripped.startswith('[')):
            return False
        
        # Remove PMD script tags (<% %>) before checking for JavaScript keywords
        # JSON can contain PMD script code inside <% %> tags
        code_without_script_tags = re.sub(r'<%.*?%>', '', code, flags=re.DOTALL)
        
        # Check for JSON-like structure patterns
        # JSON doesn't contain JavaScript keywords or operators outside of script tags
        js_keywords = ['var ', 'let ', 'const ', 'function', 'if (', 'while (', 'for (', 'return ', '=>']
        for keyword in js_keywords:
            if keyword in code_without_script_tags:
                return False
        
        # JSON typically contains quoted keys and values
        if '"' not in code and "'" not in code:
            return False
        
        # Additional checks to distinguish JSON from PMD Script expressions:
        # 1. JSON should have key-value pairs with colons (e.g., "key": "value")
        # 2. JSON should not have standalone expressions with operators like +, -, *, /
        # 3. JSON should not have function calls like user.name or func()
        
        # Check if it looks like a JSON object with key-value pairs
        has_colon_quotes = bool(re.search(r'"[^"]*"\s*:', code_without_script_tags))
        
        # Check if it looks like a PMD Script expression (has function calls)
        # Note: Property access patterns like "stepAction.id" can appear in JSON field names/values
        # so we only check for function calls which are more indicative of executable code
        has_function_calls = bool(re.search(r'\w+\(', code_without_script_tags))
        
        # If it has function calls outside of script tags, it's likely PMD Script, not JSON
        if has_function_calls:
            return False
        
        # If it has key-value pairs with colons, it's likely JSON
        if has_colon_quotes:
            return True
        
        # Default: if it starts with { and has quotes but no clear indicators, assume it's JSON
        return True
    
    def _get_meaningful_content_after_brace(self, code: str, pos: int) -> str:
        """
        Look ahead from a brace position, skipping comments and whitespace until we find meaningful content.
        Returns up to 50 characters of meaningful content after the brace.
        """
        i = pos + 1
        while i < len(code):
            # Skip whitespace
            if code[i] in ' \t\n\r':
                i += 1
                continue
            
            # Skip line comments
            if code[i:i+2] == '//':
                # Skip to end of line
                while i < len(code) and code[i] != '\n':
                    i += 1
                continue
            
            # Skip block comments
            if code[i:i+2] == '/*':
                # Skip to end of comment
                end = code.find('*/', i + 2)
                if end != -1:
                    i = end + 2
                    continue
                else:
                    break  # Unclosed comment
            
            # Found actual content - return up to 50 chars
            remaining = code[i:i+50]
            return remaining
        
        # No meaningful content found
        return ""
    
    def _preprocess_newlines_in_script_blocks(self, code: str) -> str:
        """
        Preprocess newlines in PMD script blocks (<% %>) to make them JSON-safe.
        This handles the case where JSON contains PMD script blocks with literal newlines.
        
        IMPORTANT: This method preserves existing escape sequences (like \\n, \\t, etc.)
        and only escapes actual newline characters that are not already escaped.
        """
        result = []
        i = 0
        
        while i < len(code):
            # Look for PMD script block start
            if code[i:i+2] == '<%':
                # Find the end of the script block
                end_pos = code.find('%>', i + 2)
                if end_pos == -1:
                    # Unclosed script block, just append the rest
                    result.append(code[i:])
                    break
                
                # Extract the script block content (without <% and %>)
                script_content = code[i+2:end_pos]
                
                # Process newlines while preserving existing escape sequences
                # We need to escape actual newline characters but preserve escape sequences
                # like \n, \t, etc. that are already in the string
                # Process character-by-character to correctly handle backslashes
                
                # Use a more careful approach: iterate and only escape newlines
                # that are NOT preceded by an odd number of backslashes
                escaped_parts = []
                i = 0
                while i < len(script_content):
                    char = script_content[i]
                    
                    if char == '\n':
                        # Count consecutive backslashes before this position
                        backslash_count = 0
                        j = i - 1
                        while j >= 0 and script_content[j] == '\\':
                            backslash_count += 1
                            j -= 1
                        
                        # If even number (or zero) of backslashes, this is an actual newline to escape
                        # If odd number, it's already escaped (part of \n sequence), preserve it
                        if backslash_count % 2 == 0:
                            escaped_parts.append('\\n')
                        else:
                            escaped_parts.append(char)
                        i += 1
                    elif char == '\r':
                        # Same logic for carriage return
                        backslash_count = 0
                        j = i - 1
                        while j >= 0 and script_content[j] == '\\':
                            backslash_count += 1
                            j -= 1
                        if backslash_count % 2 == 0:
                            escaped_parts.append('\\r')
                        else:
                            escaped_parts.append(char)
                        i += 1
                    elif char == '\t':
                        # Same logic for tab - literal tabs in script blocks break JSON parsing
                        backslash_count = 0
                        j = i - 1
                        while j >= 0 and script_content[j] == '\\':
                            backslash_count += 1
                            j -= 1
                        if backslash_count % 2 == 0:
                            escaped_parts.append('\\t')
                        else:
                            escaped_parts.append(char)
                        i += 1
                    else:
                        escaped_parts.append(char)
                        i += 1
                
                escaped_content_str = ''.join(escaped_parts)
                
                # Add the processed script block
                result.append('<%' + escaped_content_str + '%>')
                
                # Move past the script block
                i = end_pos + 2
            else:
                result.append(code[i])
                i += 1
        
        return ''.join(result)


def preprocess_wqlquery_content(content: str) -> str:
    """
    Escape literal newlines and tabs in .wqlquery "query", "offset", and "limit"
    string values so the file is valid JSON (like PMD preprocessing for script blocks).
    """
    spans = []
    for key in ('query', 'offset', 'limit'):
        pattern = re.escape(f'"{key}"') + r'\s*:\s*"'
        for m in re.finditer(pattern, content):
            value_start = m.end()
            i = value_start
            while i < len(content):
                if content[i] == '\\' and i + 1 < len(content):
                    i += 2
                    continue
                if content[i] == '"':
                    value_end = i
                    inner = content[value_start:value_end]
                    inner_escaped = (
                        inner.replace('\n', '\\n')
                        .replace('\r', '\\r')
                        .replace('\t', '\\t')
                    )
                    spans.append((value_start, value_end, inner_escaped))
                    break
                i += 1
    result = content
    for value_start, value_end, inner_escaped in sorted(spans, key=lambda x: -x[0]):
        result = result[:value_start] + inner_escaped + result[value_end:]
    return result


def preprocess_pmd_content(content: str) -> Tuple[str, dict, Dict[str, List[List[int]]]]:
    """
    Preprocess PMD/Pod FULL FILE content with line tracking.
    
    This is called by the file parsers (app_parser.py) on FULL files.
    
    Returns:
        tuple: (processed_content, line_mappings, hash_to_lines)
    """
    preprocessor = PMDPreprocessor()
    
    # Use the line tracking method for full files
    processed_content, hash_to_lines = preprocessor.preprocess_with_line_tracking(content)
    
    # Line mappings deprecated but kept for compatibility
    line_mappings = {}
    
    return processed_content, line_mappings, hash_to_lines