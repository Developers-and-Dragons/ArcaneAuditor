"""
Rule to validate that file names follow lowerCamelCase naming convention.

All Workday Extend files (PMD, POD, AMD, SMD, Script) should follow lowerCamelCase
naming convention for consistency and maintainability.
"""
import re
import os
from typing import Generator

from ...base import Finding, Rule, FixStrategy
from ....models import ProjectContext
from utils.file_path_utils import strip_uuid_prefix


class FileNameLowerCamelCaseRule(Rule):
    """
    Validates that all file names follow lowerCamelCase naming convention.

    This rule checks:
    - PMD files
    - POD files
    - Script files
    - AMD file
    - SMD file

    Valid pattern: starts with lowercase letter, followed by letters/numbers
    Examples: myPage.pmd, helperFunctions.script, myApp_abcdef.amd, myApp_abcdef.smd
    """

    ID = "FileNameLowerCamelCaseRule"
    DESCRIPTION = "Ensures all file names follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''LowerCamelCase is the Workday Extend standard, and following it ensures files are organized predictably, keeping your code looking professional.''',
        'catches': [
            'Files using PascalCase (e.g., `MyPage.pmd`)',
            'Files using snake_case (e.g., `my_page.pmd`)'
        ],
        'examples': '''**Example violations:**

```json
MyPage.pmd          // ❌ PascalCase
my_page.pmd         // ❌ snake_case
MY_PAGE.pmd         // ❌ UPPER_SNAKE_CASE
```

**Fix:**

```json
myPage.pmd          // ✅ lowerCamelCase
helperFunctions.script  // ✅ lowerCamelCase
```''',
        'recommendation': 'Use lowerCamelCase for all file names to follow Workday Extend standards and maintain a professional, consistent codebase.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Analyze all files in the context for naming convention compliance.
        
        Args:
            context: The fully-built ProjectContext containing all application models.
            
        Yields:
            Finding objects for any files with invalid naming conventions.
        """
        # Check PMD files
        for pmd_model in context.pmds.values():
            yield from self._check_filename(pmd_model.file_path)
        
        # Check POD files
        for pod_model in context.pods.values():
            yield from self._check_filename(pod_model.file_path)

        # Check Script files
        for script_model in context.scripts.values():
            yield from self._check_filename(script_model.file_path)
        
        # Check AMD file
        if context.amd:
            yield from self._check_filename(context.amd.file_path)
        
        # Check SMD file
        if context.smd:
            yield from self._check_filename(context.smd.file_path)

        # Check WQL query files
        if hasattr(context, "wqlqueries"):
            for wql_model in context.wqlqueries.values():
                yield from self._check_filename(wql_model.file_path)
    
    def _check_filename(self, file_path: str) -> Generator[Finding, None, None]:
        """
        Check if a filename follows lowerCamelCase convention.
        
        Args:
            file_path: Path to the file (can include directory path)
            
        Yields:
            Finding if the filename doesn't follow lowerCamelCase convention.
        """
        if not file_path:
            return
        
        # Extract just the filename (without path) and without extension
        filename_with_ext = os.path.basename(file_path)
        
        # Strip job ID prefix if present (format: uuid_filename.ext)
        # Uses utility function to ensure consistent UUID detection
        filename_with_ext = os.path.basename(strip_uuid_prefix(file_path))
        
        filename, ext = os.path.splitext(filename_with_ext)
        
        # Pattern: must start with lowercase letter, followed by letters/numbers
        # Valid: myPage, helperFunctions
        # Invalid: MyPage, my_page, MYPAGE, 2myPage, helper_functions
        
        # Pure lowerCamelCase (no underscores)
        pure_camel_case = re.compile(r'^[a-z][a-zA-Z0-9]*$')

        # AMD/SMD may have _<app_id>, which is a 6 letter suffix
        amd_smd_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*_[a-zA-Z]{6}$')

        # Check if it matches either pattern
        if not (pure_camel_case.match(filename) or amd_smd_pattern.match(filename)):
            yield Finding(
                rule=self,
                message=f"File '{filename_with_ext}' doesn't follow lowerCamelCase naming convention. Should start with lowercase letter and use camelCase (e.g., 'myPage.pmd', 'helperFunctions.script').",
                file_path=file_path,
                line=1
            )

