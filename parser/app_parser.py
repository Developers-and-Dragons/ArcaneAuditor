"""
Parser to convert source files into PMD models for analysis.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import ProjectContext, PMDModel, ScriptModel, AMDModel, PMDIncludes, PMDPresentation, PodModel, PodSeed, SMDModel, WQLQueryModel, OrchestrationModel
from .pmd_preprocessor import PMDPreprocessor
from utils.console import info, warn, error


class ModelParser:
    """Parses source files into PMD models for analysis."""
    
    def __init__(self):
        self.supported_extensions = {'.pmd', '.script', '.amd', '.pod', '.smd', '.wqlquery', '.orchestration', '.suborchestration'}
    
    def _filter_commented_keys(self, data):
        """
        Recursively remove keys starting with underscore (commented out).
        
        In Extend, keys starting with underscore are considered commented out
        and should be ignored by all rules and analysis.
        
        Args:
            data: The data structure to filter (dict, list, or primitive)
            
        Returns:
            Filtered data structure with underscore-prefixed keys removed
        """
        if isinstance(data, dict):
            return {k: self._filter_commented_keys(v) 
                    for k, v in data.items() 
                    if not k.startswith('_')}
        elif isinstance(data, list):
            return [self._filter_commented_keys(item) for item in data]
        else:
            return data
    
    def parse_files(self, source_files_map: Dict[str, Any]) -> ProjectContext:
        """
        Parse source files into a ProjectContext with populated models.
        Uses parallel processing for improved performance with large applications.
        
        Args:
            source_files_map: Dictionary mapping file paths to SourceFile objects
            
        Returns:
            ProjectContext with all parsed models
        """
        context = ProjectContext()
        
        # For small numbers of files, use serial processing to avoid overhead
        if len(source_files_map) <= 3:
            info("Using serial file parsing (small file count)")
            for file_path, source_file in source_files_map.items():
                try:
                    self._parse_single_file(file_path, source_file, context)
                except Exception as e:
                    error(f"Failed to parse {file_path}: {e}")
                    context.parsing_errors.append(f"{file_path}: {e}")
        else:
            max_workers = min(10, len(source_files_map))
            info(f"Using parallel file parsing ({max_workers} workers for {len(source_files_map)} files)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all parsing tasks
                future_to_file = {
                    executor.submit(self._parse_single_file_safe, file_path, source_file): file_path
                    for file_path, source_file in source_files_map.items()
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            parsed_context, parse_error = result
                            self._merge_context(context, parsed_context)
                            if parse_error:
                                context.parsing_errors.append(f"{file_path}: {parse_error}")
                    except Exception as e:
                        error(f"Failed to parse {file_path}: {e}")
                        context.parsing_errors.append(f"{file_path}: {e}")
        
        # Pre-compute script fields for all PMD and POD models to improve rule performance
        self._precompute_script_fields(context)
        
        # Pre-compute ASTs for all script fields to avoid repeated parsing
        self._precompute_asts(context)
        
        # Initialize analysis context for tracking missing cross-file dependencies
        self._initialize_analysis_context(context, source_files_map)
        
        return context
    
    def _parse_single_file_safe(self, file_path: str, source_file: Any):
        """Thread-safe version of _parse_single_file that returns a new context."""
        try:
            temp_context = ProjectContext()
            self._parse_single_file(file_path, source_file, temp_context)
            return temp_context, None
        except Exception as e:
            return None, str(e)
    
    def _merge_context(self, main_context: ProjectContext, temp_context: ProjectContext):
        """Merge a temporary context into the main context (thread-safe)."""
        # Merge PMDs
        main_context.pmds.update(temp_context.pmds)
        
        # Merge Scripts
        main_context.scripts.update(temp_context.scripts)
        
        # Merge Pods
        main_context.pods.update(temp_context.pods)

        # Merge WQL Queries
        main_context.wqlqueries.update(temp_context.wqlqueries)

        # Merge Orchestrations
        main_context.orchestrations.update(temp_context.orchestrations)
        
        # Handle SMD (only one expected)
        if temp_context.smd:
            main_context.smd = temp_context.smd
        
        # Handle AMD (only one expected)
        if temp_context.amd:
            main_context.amd = temp_context.amd
    
    def _parse_single_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a single source file based on its extension."""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension == '.pmd':
            self._parse_pmd_file(file_path, source_file, context)
        elif extension == '.amd':
            self._parse_amd_file(file_path, source_file, context)
        elif extension == '.smd':
            self._parse_smd_file(file_path, source_file, context)
        elif extension == '.pod':
            self._parse_pod_file(file_path, source_file, context)
        elif extension == '.script':
            self._parse_script_file(file_path, source_file, context)
        elif extension == '.wqlquery':
            self._parse_wqlquery_file(file_path, source_file, context)
        elif extension == '.orchestration' or extension == '.suborchestration':
            self._parse_orchestration_file(file_path, source_file, context)

    def _unwrap_orchestration_value(self, obj: Any) -> Any:
        """Unwrap typed envelope: return obj['_value'] if obj is a dict with _value."""
        if obj is None:
            return None
        if isinstance(obj, dict) and "_value" in obj:
            return obj["_value"]
        return obj

    def _parse_orchestration_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .orchestration file into an OrchestrationModel."""
        try:
            content = source_file.content.strip()
            if "\n" in content or "\r" in content:
                content = content.replace("\r", "").replace("\n", "")
            data = json.loads(content)
            if data.get("_type") != "Flow" or "_value" not in data:
                raise ValueError("Orchestration root must have _type 'Flow' and _value")
            val = data["_value"]
            flow_type_val = self._unwrap_orchestration_value(val.get("type"))
            flow_type = flow_type_val if isinstance(flow_type_val, str) else ""
            orch_id = self._unwrap_orchestration_value(val.get("id"))
            orch_id = orch_id if isinstance(orch_id, str) else ""
            orch_name = self._unwrap_orchestration_value(val.get("name"))
            orch_name = orch_name if isinstance(orch_name, str) else ""
            sd_node = val.get("securityDomains")
            security_domains = None
            if sd_node is not None:
                inner = self._unwrap_orchestration_value(sd_node)
                if inner is not None:
                    lst = self._unwrap_orchestration_value(inner) if isinstance(inner, dict) else inner
                    if isinstance(lst, list):
                        security_domains = [
                            self._unwrap_orchestration_value(x) or x
                            for x in lst
                        ]
                        security_domains = [x if isinstance(x, str) else str(x) for x in security_domains]
            orch_model = OrchestrationModel(
                flow_type=flow_type,
                id=orch_id,
                name=orch_name,
                security_domains=security_domains,
                raw_value=val,
                file_path=file_path,
                source_content=source_file.content,
            )
            # Use file_path as key so multiple orchestration files never overwrite each other
            context.orchestrations[file_path] = orch_model
            from utils.file_path_utils import strip_uuid_prefix
            cleaned_filename = os.path.basename(strip_uuid_prefix(file_path))
            info(f"Parsed Orchestration: {cleaned_filename}")
        except Exception as e:
            error(f"Failed to parse orchestration file {file_path}: {e}")
            raise

    def _parse_wqlquery_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .wqlquery file into a WQLQueryModel."""
        try:
            content = source_file.content.strip()
            path_obj = Path(file_path)

            # Escape newlines/tabs in query/offset/limit so multi-line values are valid JSON
            from .pmd_preprocessor import preprocess_wqlquery_content, preprocess_pmd_content
            content = preprocess_wqlquery_content(content)
            # Then handle script blocks (<% %>) like PMD/POD
            processed_content, _, hash_to_lines = preprocess_pmd_content(content)

            wql_data = json.loads(processed_content)
            wql_data = self._filter_commented_keys(wql_data)

            wql_model = WQLQueryModel(
                id=wql_data.get('id', path_obj.stem),
                parameters=wql_data.get('parameters', []) or [],
                query=wql_data.get('query'),
                offset=wql_data.get('offset'),
                limit=wql_data.get('limit'),
                file_path=file_path,
                source_content=content
            )
            wql_model.set_hash_to_lines_mapping(hash_to_lines)

            context.wqlqueries[wql_model.id] = wql_model

            from utils.file_path_utils import strip_uuid_prefix
            cleaned_filename = os.path.basename(strip_uuid_prefix(file_path))
            info(f"Parsed WQLQuery: {cleaned_filename}")
        except Exception as e:
            error(f"Failed to parse WQLQuery file {file_path}: {e}")
            raise
    
    def _parse_pmd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .pmd file into a PMDModel."""
        try:
            # Preprocess the content to handle multi-line script sections and newlines in PMD script blocks
            content = source_file.content.strip()
            path_obj = Path(file_path)
            
            # Use the preprocessor to handle newlines in PMD script blocks and brace disambiguation
            # This now also provides hash-to-lines mapping for accurate line number tracking
            from .pmd_preprocessor import preprocess_pmd_content
            processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(content)
            
            # Try to parse as JSON
            try:
                pmd_data = json.loads(processed_content)
                # Filter out commented-out keys (starting with underscore)
                pmd_data = self._filter_commented_keys(pmd_data)

                # Extract presentation data - handle the nested structure properly
                presentation_data = pmd_data.get('presentation', {})

                # Handle includes - convert to PMDIncludes format
                includes_data = pmd_data.get('include', [])
                if isinstance(includes_data, list):
                    includes = PMDIncludes(scripts=includes_data)
                else:
                    includes = None
                
                # Extract microConclusion and other presentation-level attributes
                presentation_attributes = {}
                if presentation_data:
                    # Move microConclusion from presentation to attributes
                    if 'microConclusion' in presentation_data:
                        presentation_attributes['microConclusion'] = presentation_data.pop('microConclusion')
                
                pmd_model = PMDModel(
                    pageId=pmd_data.get('id', path_obj.stem),  # Use 'id' field or fallback to filename
                    securityDomains=pmd_data.get('securityDomains', []),
                    inboundEndpoints=pmd_data.get('endPoints', []), 
                    outboundEndpoints=pmd_data.get('outboundData', {}).get('outboundEndPoints', []),  # Handle nested structure
                    presentation=PMDPresentation(
                        attributes=presentation_attributes, 
                        title=presentation_data.get("title", {}), 
                        body=presentation_data.get("body", []), 
                        footer=presentation_data.get("footer", {}),
                        tabs=presentation_data.get("tabs", [])
                    ) if presentation_data else None,
                    onLoad=pmd_data.get('onLoad'),
                    script=pmd_data.get('script'),
                    includes=includes,
                    file_path=file_path,
                    source_content=content  # Store the original content for line offset calculation
                )
                
                # Set line mappings for proper error reporting
                pmd_model.set_line_mappings(line_mappings)
                pmd_model.set_hash_to_lines_mapping(hash_to_lines)
                
                context.pmds[file_path] = pmd_model
                # Show cleaned filename for consistency with "Parsed Script" messages
                from utils.file_path_utils import strip_uuid_prefix
                cleaned_filename = os.path.basename(strip_uuid_prefix(file_path))
                info(f"Parsed PMD: {cleaned_filename}")
                
            except json.JSONDecodeError as e:
                error(f"JSON parsing failed for {file_path}: {e}")
                raise
                
        except Exception as e:
            error(f"Failed to parse PMD file {file_path}: {e}")
            raise
    
    def _parse_script_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .script file into a ScriptModel."""
        try:
            script_model = ScriptModel(
                source=source_file.content,
                file_path=file_path
            )
            # Use the full filename (including extension) as the key since that's how it's referenced in PMD files
            context.scripts[Path(file_path).name] = script_model
            # Show cleaned filename without UUID prefix for consistency
            from utils.file_path_utils import strip_uuid_prefix
            cleaned_filename = os.path.basename(strip_uuid_prefix(file_path))
            info(f"Parsed Script: {cleaned_filename}")
            
        except Exception as e:
            error(f"Failed to parse script file {file_path}: {e}")
            raise
    
    def _parse_amd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse an .amd file into an AMDModel."""
        try:
            content = source_file.content.strip()
            
            try:
                amd_data = json.loads(content)
                # Filter out commented-out keys (starting with underscore)
                amd_data = self._filter_commented_keys(amd_data)
                amd_model = AMDModel(
                    routes=amd_data.get('routes', {}),
                    baseUrls=amd_data.get('baseUrls', {}),
                    flows=amd_data.get('flows', {}),
                    dataProviders=amd_data.get('dataProviders', []),
                    file_path=file_path,
                    source_content=content
                )
                context.amd = amd_model
                info(f"Parsed AMD: {file_path}")
                
            except json.JSONDecodeError as e:
                error(f"JSON parsing error in AMD file {file_path}: {e}")
                raise
                
        except Exception as e:
            error(f"Failed to parse AMD file {file_path}: {e}")
            raise
    
    def _parse_pod_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .pod file into a PodModel."""
        try:
            content = source_file.content.strip()
            
            # Always preprocess POD files to create hash mappings for line number tracking
            # This ensures script content gets precise line numbers
            from .pmd_preprocessor import preprocess_pmd_content
            processed_content, line_mappings, hash_to_lines = preprocess_pmd_content(content)
            
            try:
                pod_data = json.loads(processed_content)
                # Filter out commented-out keys (starting with underscore)
                pod_data = self._filter_commented_keys(pod_data)
                
                # Extract seed data
                seed_data = pod_data.get('seed', {})
                seed = PodSeed(
                    parameters=seed_data.get('parameters', []),
                    endPoints=seed_data.get('endPoints', []),
                    template=seed_data.get('template', {})
                )
                
                pod_model = PodModel(
                    podId=pod_data.get('podId', Path(file_path).stem),
                    seed=seed,
                    file_path=file_path,
                    source_content=content  # Store original content
                )
                
                # Set hash-based line mappings for POD files too
                pod_model.set_hash_to_lines_mapping(hash_to_lines)
                
                context.pods[file_path] = pod_model
                info(f"Parsed Pod: {pod_model.podId}")
                
            except json.JSONDecodeError as e:
                # If preprocessing and parsing didn't work, fail
                error(f"JSON parsing error in Pod file {file_path}: {e}")
                raise
                
        except Exception as e:
            error(f"Failed to parse Pod file {file_path}: {e}")
            raise

    def _parse_smd_file(self, file_path: str, source_file: Any, context: ProjectContext):
        """Parse a .smd file into an SMDModel."""
        try:
            content = source_file.content.strip()
            path_obj = Path(file_path)
            
            # Parse JSON content
            smd_data = json.loads(content)
            # Filter out commented-out keys (starting with underscore)
            smd_data = self._filter_commented_keys(smd_data)
            
            # Create SMD model
            smd_model = SMDModel(
                id=smd_data.get('id', path_obj.stem),
                applicationId=smd_data.get('applicationId', ''),
                siteId=smd_data.get('siteId', ''),
                languages=smd_data.get('languages', []),
                siteAuth=smd_data.get('siteAuth'),
                errorPageConfigurations=smd_data.get('errorPageConfigurations', []),
                file_path=file_path,
                source_content=content
            )
            
            # Add to context (only one SMD file allowed)
            if context.smd is not None:
                warn(f"Multiple SMD files found. Ignoring {file_path} (already have {context.smd.id})")
            else:
                context.smd = smd_model
                info(f"Parsed SMD: {smd_model.id}")
            
        except json.JSONDecodeError as e:
            error(f"JSON parsing error in SMD file {file_path}: {e}")
            raise
        except Exception as e:
            error(f"Failed to parse SMD file {file_path}: {e}")
            raise
    
    def _precompute_script_fields(self, context: ProjectContext):
        """Pre-compute script fields for all PMD and POD models to improve rule performance."""
        from .rules.base import Rule
        
        # Create a concrete rule instance to use its script field extraction methods
        class TempRule(Rule):
            def analyze(self, context):
                yield from []
        
        temp_rule = TempRule()
        
        # Pre-compute PMD script fields
        for pmd_id, pmd_model in context.pmds.items():
            script_fields = temp_rule._extract_script_fields(pmd_model)
            context.set_cached_pmd_script_fields(pmd_id, script_fields)
        
        # Pre-compute POD script fields
        for pod_id, pod_model in context.pods.items():
            script_fields = temp_rule.find_pod_script_fields(pod_model)
            context.set_cached_pod_script_fields(pod_id, script_fields)
        
        info(f"Pre-computed script fields for {len(context.pmds)} PMD files and {len(context.pods)} POD files")
    
    def _precompute_asts(self, context: ProjectContext):
        """Pre-compute ASTs for all script fields to avoid repeated parsing."""
        from .rules.base import Rule
        from .pmd_script_parser import parse_with_preprocessor
        
        # Create a concrete rule instance to use its script field extraction methods
        class TempRule(Rule):
            def analyze(self, context):
                yield from []
        
        temp_rule = TempRule()
        
        ast_count = 0
        error_count = 0
        
        # Pre-compute ASTs for PMD script fields
        for pmd_id, pmd_model in context.pmds.items():
            cached_fields = context.get_cached_pmd_script_fields(pmd_id)
            if cached_fields:
                for field_path, field_value, field_name, line_offset in cached_fields:
                    if field_value and len(field_value.strip()) > 0:
                        try:
                            parsed_script = temp_rule._strip_pmd_wrappers(field_value)
                            if parsed_script:
                                # Check if AST is already cached
                                cache_key = hash(parsed_script)
                                if context.get_cached_ast(cache_key) is None:
                                    # Use _parse_script_content to handle string extraction properly
                                    ast = temp_rule._parse_script_content(field_value, context)
                                    context.set_cached_ast(cache_key, ast)
                                    ast_count += 1
                        except Exception as e:
                            error_count += 1
        
        # Pre-compute ASTs for POD script fields
        for pod_id, pod_model in context.pods.items():
            cached_fields = context.get_cached_pod_script_fields(pod_id)
            if cached_fields:
                for field_path, field_value, field_name, line_offset in cached_fields:
                    if field_value and len(field_value.strip()) > 0:
                        try:
                            parsed_script = temp_rule._strip_pmd_wrappers(field_value)
                            if parsed_script:
                                # Check if AST is already cached
                                cache_key = hash(parsed_script)
                                if context.get_cached_ast(cache_key) is None:
                                    # Use _parse_script_content to handle string extraction properly
                                    ast = temp_rule._parse_script_content(field_value, context)
                                    context.set_cached_ast(cache_key, ast)
                                    ast_count += 1
                        except Exception as e:
                            error_count += 1
        
        # Pre-compute ASTs for standalone script files
        for script_name, script_model in context.scripts.items():
            if script_model.source and len(script_model.source.strip()) > 0:
                try:
                    # Check if AST is already cached
                    cache_key = hash(script_model.source)
                    if context.get_cached_ast(cache_key) is None:
                        # Use _parse_script_content to handle any preprocessing needed
                        ast = temp_rule._parse_script_content(script_model.source, context)
                        context.set_cached_ast(cache_key, ast)
                        ast_count += 1
                except Exception as e:
                    error_count += 1
        
        info(f"Pre-computed {ast_count} ASTs (errors: {error_count})")
    
    def _initialize_analysis_context(self, context: ProjectContext, source_files_map: Dict[str, Any]):
        """
        Initialize the analysis context to track which files were analyzed.
        
        This helps inform users when validation is partial due to missing cross-file
        dependencies like AMD or SMD files.
        
        Args:
            context: The ProjectContext being populated
            source_files_map: Dictionary mapping file paths to SourceFile objects
        """
        from file_processing.context_tracker import AnalysisContext
        
        # Detect which file types are present
        files_present = set()
        files_analyzed = []
        
        for file_path in source_files_map.keys():
            files_analyzed.append(file_path)
            
            if file_path.endswith('.pmd'):
                files_present.add('PMD')
            elif file_path.endswith('.pod'):
                files_present.add('POD')
            elif file_path.endswith('.amd'):
                files_present.add('AMD')
            elif file_path.endswith('.smd'):
                files_present.add('SMD')
            elif file_path.endswith('.script'):
                files_present.add('SCRIPT')
        
        # Determine analysis type based on input
        # If analyzing from ZIP, it's full_app; otherwise it's individual_files
        analysis_type = "full_app" if any(f.endswith('.zip') for f in source_files_map.keys()) else "individual_files"
        
        # Create and attach analysis context
        context.analysis_context = AnalysisContext(
            analysis_type=analysis_type,
            files_analyzed=files_analyzed,
            files_present=files_present
        )
