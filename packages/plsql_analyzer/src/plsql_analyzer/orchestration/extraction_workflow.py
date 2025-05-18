# plsql_analyzer/orchestration/extraction_workflow.py
from __future__ import annotations
from pathlib import Path
from tqdm.auto import tqdm
import loguru as lg # Expect logger
from typing import List, Dict, Any, Optional, Tuple

from plsql_analyzer.settings import AppConfig
from plsql_analyzer.persistence.database_manager import DatabaseManager
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor, ExtractedCallTuple
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
from plsql_analyzer.utils.file_helpers import FileHelpers


def clean_code(code: str) -> str:
    """
    Removes comments and replaces string literals with placeholders.
    Based on the user-provided `remove_string_literals_and_comments` function.
    """

    inside_quote = False
    inside_inline_comment = False
    inside_multiline_comment = False

    idx = 0
    clean_code_chars = [] # Use a list for efficiency, then join
    current_literal_chars = []

    while idx < len(code):
        current_char = code[idx]
        next_char = code[idx + 1] if (idx + 1) < len(code) else None

        if inside_inline_comment:
            if current_char == "\n":
                inside_inline_comment = False
                clean_code_chars.append('\n')
            idx += 1
            continue

        if inside_multiline_comment:
            if f"{current_char}{next_char}" == "*/":
                inside_multiline_comment = False
                idx += 2
            else:
                idx += 1
            continue
        
        if f"{current_char}{next_char}" == "/*" and not inside_quote:
            inside_multiline_comment = True
            idx += 2
            continue

        if f"{current_char}{next_char}" == "--" and not inside_quote:
            inside_inline_comment = True
            idx += 1 # Consume only the first '-' of '--'
            continue
        
        # Handle escaped single quotes within literals
        if inside_quote and current_char == "'" and next_char == "'":
            current_literal_chars.append("''") # Keep escaped quote
            idx += 2
            continue

        if current_char == "'":
            inside_quote = not inside_quote
            clean_code_chars.append("'")

            idx += 1
            continue

        clean_code_chars.append(current_char)
        
        idx += 1
    
    cleaned_code  = "".join(clean_code_chars)
    
    return cleaned_code

def clean_code_and_map_literals(code: str, logger:lg.Logger) -> Tuple[str, Dict[str, str]]:
        """
        Removes comments and replaces string literals with placeholders.
        Returns the cleaned code and a mapping of placeholders to original literals.
        """
        logger.debug("Cleaning code: removing comments and string literals.")
        literal_mapping: Dict[str, str] = {}
        inside_quote = False
        inside_inline_comment = False
        inside_multiline_comment = False

        idx = 0
        clean_code_chars = [] 
        current_literal_chars = []

        while idx < len(code):
            current_char = code[idx]
            next_char = code[idx + 1] if (idx + 1) < len(code) else None

            if inside_inline_comment:
                if current_char == "\n":
                    inside_inline_comment = False
                    clean_code_chars.append('\n')
                idx += 1
                continue

            if inside_multiline_comment:
                if f"{current_char}{next_char}" == "*/":
                    inside_multiline_comment = False
                    idx += 2
                else:
                    idx += 1
                continue
            
            if f"{current_char}{next_char}" == "/*" and not inside_quote:
                inside_multiline_comment = True
                idx += 2
                continue

            if f"{current_char}{next_char}" == "--" and not inside_quote:
                inside_inline_comment = True
                idx += 1 
                continue
            
            if inside_quote and current_char == "'" and next_char == "'":
                current_literal_chars.append("''") 
                idx += 2
                continue

            if current_char == "'":
                inside_quote = not inside_quote

                if not inside_quote: 
                    literal_name = f"<LITERAL_{len(literal_mapping)}>"
                    literal_mapping[literal_name] = "".join(current_literal_chars)
                    current_literal_chars = []
                    clean_code_chars.append(literal_name) 
                    clean_code_chars.append("'") 
                else:
                    clean_code_chars.append("'")

                idx += 1
                continue
            
            if inside_quote:
                current_literal_chars.append(current_char)
            else:
                clean_code_chars.append(current_char)
            
            idx += 1
        
        if inside_quote:
            literal_name = f"<LITERAL_{len(literal_mapping)}>"
            literal_mapping[literal_name] = "".join(current_literal_chars)
            current_literal_chars = []
            clean_code_chars.append(literal_name)
        
        cleaned_code_str  = "".join(clean_code_chars)
        logger.debug(f"Code cleaning complete. Original Code Length: {len(code)}, Cleaned code length: {len(cleaned_code_str)}, Literals found: {len(literal_mapping)}")
        return cleaned_code_str, literal_mapping

class ExtractionWorkflow:
    def __init__(self,
                    config: 'AppConfig', # Pass the loaded config module or a config object/dict
                    logger: lg.Logger,
                    db_manager: 'DatabaseManager',
                    structural_parser: 'PlSqlStructuralParser',
                    signature_parser: 'PLSQLSignatureParser',
                    call_extractor: 'CallDetailExtractor',
                    file_helpers: 'FileHelpers'):
        
        self.config = config
        self.logger = logger.bind(workflow="Extraction")
        self.db_manager = db_manager
        self.structural_parser = structural_parser
        self.signature_parser = signature_parser
        self.call_extractor = call_extractor
        self.file_helpers = file_helpers
        
        self.total_files_processed = 0
        self.total_files_skipped_unchanged = 0
        self.total_files_failed_hash = 0
        self.total_files_failed_structure_parse = 0
        self.total_objects_extracted = 0
        self.total_objects_failed_signature = 0
        self.total_objects_failed_calls = 0
        self.total_objects_failed_db_add = 0

    def _escape_angle_brackets(self, text: str|list|dict) -> str:

        # if isinstance(text, str):
        #     return text.replace("<", "\\<")
        
        # if isinstance(text, list):
        #     return [comp.replace("<", "\<") for comp in text if isinstance(comp, str)]
        
        # if isinstance(text, dict):
        #     new_dict = {}
        #     for key, value in text.items():
        #         new_key = key.replace("<", "\<") if isinstance(key, str) else key
        #         new_value = value.replace("<", "\<") if isinstance(value, str) else value

        #         new_dict[new_key] = new_value
            
        #     return new_dict

        return str(text).replace("<", "\\<")


    def _process_single_file(self, fpath: Path):
        self.logger.info(f"Processing File: {self.file_helpers.escape_angle_brackets(str(fpath))}")
        
        processed_fpath = self.file_helpers.get_processed_fpath(
            fpath, self.config.exclude_names_from_processed_path
        )
        current_file_hash = self.file_helpers.compute_file_hash(fpath)

        if not current_file_hash:
            self.logger.warning(f"Skipping {fpath} due to hashing error or file not found.")
            self.total_files_failed_hash +=1
            return

        stored_hash = self.db_manager.get_file_hash(str(processed_fpath))

        if stored_hash == current_file_hash:
            self.logger.info(f"Skipping (unchanged): {processed_fpath} (Hash: {current_file_hash[:10]}...)")
            self.total_files_skipped_unchanged +=1
            return
        
        self.logger.info(f"Change detected (or new file): {processed_fpath} "
                         f"(Stored: {stored_hash[:10] if stored_hash else 'None'}, Current: {current_file_hash[:10]}...)")

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
            
            # Clean the code 
            clean_code, literal_map = clean_code_and_map_literals(code_content, self.logger)
            code_lines = clean_code.splitlines() # Keep for extracting source snippets
        except Exception as e:
            self.logger.error(f"Failed to read file {fpath}: {self._escape_angle_brackets(e)}")
            return

        try:
            # Structural parsing returns package name found in code (if any) and dict of objects
            package_name_from_structural_parser, structurally_parsed_objects = self.structural_parser.parse(clean_code)
            structurally_parsed_objects: Dict
        except Exception as e:
            self.logger.exception(f"Critical failure during structural parsing of {fpath}: {self._escape_angle_brackets(e)}")
            self.total_files_failed_structure_parse +=1
            return
            
        # Derive the definitive package name for objects in this file
        # This combines path-based derivation with what the structural parser found (if anything)
        final_package_name_for_file_objects = self.file_helpers.derive_package_name_from_path(
            package_name_from_structural_parser,
            fpath,
            self.config.file_extensions_to_include,
            self.config.exclude_names_for_package_derivation
        )
        self.logger.info(f"Derived package context for objects in {fpath.name} as: '{final_package_name_for_file_objects}'")

        if not self.db_manager.update_file_hash(str(processed_fpath), current_file_hash):
            self.logger.error(f"Failed to update hash for {processed_fpath}. Aborting processing for this file.")
            # If hash update fails, we might not want to proceed with parsing this file.
            return

        file_level_processing_error_occurred = False
        for obj_key_name, list_of_obj_occurrences in structurally_parsed_objects.items():
            is_overloaded_structurally = len(list_of_obj_occurrences) > 1
            
            for idx, obj_structural_props in enumerate(list_of_obj_occurrences, start=1):
                obj_log_ctx = self.logger.bind(
                    file=fpath.name, 
                    obj_key=obj_key_name,
                    occurrence_idx=idx,
                    structural_type=obj_structural_props["type"]
                )
                
                if obj_structural_props.get("is_forward_decl", False):
                    obj_log_ctx.info(f"Skipping processing for item {obj_key_name} (occurrence {idx}) as it's a forward declaration.")
                    continue

                start_line_idx = obj_structural_props["start"] - 1 # 0-indexed for list slicing
                end_line_idx = obj_structural_props["end"] # exclusive for slicing if end is 1-indexed line number
                
                # Ensure indices are valid
                if not (0 <= start_line_idx < end_line_idx <= len(code_lines)):
                    obj_log_ctx.error(f"Invalid line numbers for {obj_key_name}: start={start_line_idx+1}, end={end_line_idx}. Max lines: {len(code_lines)}. Skipping.")
                    continue
                
                object_source_snippet = "\n".join(code_lines[start_line_idx:end_line_idx])

                # Signature Parsing
                parsed_signature_data: Optional[Dict[str, Any]] = None
                try:
                    # The input to signature_parser should be the declaration part of the object.
                    # The structural parser gives start/end of the whole object.
                    # Signature parser is designed to find signature within this.
                    parsed_signature_data = self.signature_parser.parse(object_source_snippet)
                except Exception as e:
                    obj_log_ctx.exception(f"Error during signature parsing for {obj_key_name}: {self._escape_angle_brackets(e)}")
                    self.total_objects_failed_signature += 1
                    file_level_processing_error_occurred = True
                    # Continue, object might be stored with minimal info

                actual_object_name = obj_structural_props.get("name_raw", obj_key_name) # From structural parser
                obj_params = []
                obj_return_type = None
                
                if parsed_signature_data:
                    actual_object_name_from_sig = parsed_signature_data.get("proc_name") or parsed_signature_data.get("func_name")
                    if actual_object_name_from_sig:
                        actual_object_name = actual_object_name_from_sig.strip().replace("\"", "")
                    obj_params = parsed_signature_data.get("params", [])
                    obj_return_type = parsed_signature_data.get("return_type")
                    obj_log_ctx.info(f"Signature parsed for {actual_object_name}: {len(obj_params)} params, Return: {obj_return_type is not None}")
                else:
                    obj_log_ctx.warning(f"Signature parsing failed or yielded no data for {obj_key_name}. Using structural info.")


                # Call Extraction
                extracted_calls: List[ExtractedCallTuple] = []
                try:
                    extracted_calls = self.call_extractor.extract_calls_with_details(object_source_snippet, literal_map)
                    obj_log_ctx.info(f"Extracted {len(extracted_calls)} calls for {actual_object_name}.")
                except Exception as e:
                    obj_log_ctx.exception(f"Error during call extraction for {actual_object_name}: {self._escape_angle_brackets(e)}")
                    self.total_objects_failed_calls += 1
                    file_level_processing_error_occurred = True


                # Create and Store PLSQL_CodeObject
                try:
                    # from ..core.code_object import PLSQL_CodeObject, CodeObjectType # Local import for type hint
                    
                    # Determine CodeObjectType enum from string
                    obj_type_enum = CodeObjectType.UNKNOWN
                    try:
                        obj_type_enum = CodeObjectType[obj_structural_props["type"].upper()]
                    except KeyError:
                        obj_log_ctx.error(f"Unknown object type string: {obj_structural_props['type']}")

                    # The `overloaded` flag should ideally be determined after resolving signatures for all
                    # objects with the same name in the file. For now, using structural overload flag.
                    # A more robust overload detection would group by final_package_name + actual_object_name
                    # and then check parameter signature differences.
                    
                    code_obj_instance = PLSQL_CodeObject(
                        name=actual_object_name,
                        package_name=final_package_name_for_file_objects, # This is the derived one
                        clean_code=clean_code, # Storing full source in DB can be heavy. Store if needed.
                        literal_map=literal_map,
                        type=obj_type_enum,
                        overloaded=is_overloaded_structurally, # This is based on name clashes in one file.
                        parsed_parameters=obj_params,
                        parsed_return_type=obj_return_type,
                        extracted_calls=extracted_calls,
                        # signature_raw_text=None, # TODO: extract signature text if needed
                        start_line=obj_structural_props["start"],
                        end_line=obj_structural_props["end"]
                    )
                    code_obj_instance.generate_id() # Crucial: ID generation
                    
                    if self.db_manager.add_codeobject(code_obj_instance, str(processed_fpath)):
                        obj_log_ctx.success(f"Successfully extracted and stored: {code_obj_instance.id}")
                        self.total_objects_extracted +=1
                    else:
                        obj_log_ctx.error(f"Failed to store extracted object {code_obj_instance.id} to DB.")
                        self.total_objects_failed_db_add +=1
                        
                except Exception as e:
                    obj_log_ctx.exception(f"Failed to create or store PLSQL_CodeObject for {actual_object_name}: {str(e)}")
                    self.total_objects_failed_db_add +=1 # Count this as a DB add failure generally
                    file_level_processing_error_occurred = True
        
        # After attempting to process all objects in the file:
        if file_level_processing_error_occurred:
            self.logger.warning(f"Due to processing errors in {fpath.name}, attempting to remove its record from the database.")
            if hasattr(self.db_manager, 'remove_file_record') and callable(getattr(self.db_manager, 'remove_file_record')):
                if self.db_manager.remove_file_record(str(processed_fpath)):
                    self.logger.info(f"Successfully removed file record for {processed_fpath} from DB due to errors.")
                else:
                    self.logger.error(f"Failed to remove file record for {processed_fpath} from DB after errors.")
            else:
                self.logger.error(f"DatabaseManager does not have a 'remove_file_record' method. Cannot remove file record for {processed_fpath}.")
                
            #     # Prevent this file from being counted as successfully processed by returning early.
            #     # The `self.total_files_processed += 1` is at the end of `_process_single_file`.
            # return

        self.total_files_processed += 1


    def run(self):
        self.logger.info("Starting PL/SQL Extraction Workflow...")
        
        source_folder = Path(self.config.source_code_root_dir)
        if not source_folder.is_dir():
            self.logger.critical(f"Source code directory does not exist or is not a directory: {source_folder}")
            return

        # Using rglob to find all files matching the extension recursively
        files_to_process = []
        for extension in self.config.file_extensions_to_include:
            self.logger.info(f"Searching for files with extension: {extension}")
            # Using rglob to find all files matching the extension recursively
            files_to_process.extend(list(source_folder.rglob(f"*.{extension}")))

        if not files_to_process:
            self.logger.warning("No files found to process. Exiting workflow.")
            return

        # Progress bar for files
        file_pbar = tqdm(files_to_process, desc="Overall File Progress", unit="file", leave=True)
        for fpath in file_pbar:
            file_pbar.set_postfix_str("\\".join(fpath.parts[-3:]), refresh=True)
            try:
                self._process_single_file(fpath)
            except Exception as e:
                # Catch any unexpected errors at the file level to prevent workflow halt
                self.logger.error(f"Unhandled exception while processing file {fpath}. Skipping this file.")
                self.logger.exception(e)
                break
        
        self.logger.info("PL/SQL Extraction Workflow Finished.")
        self.log_summary()

    def log_summary(self):
        self.logger.info("--- Extraction Summary ---")
        self.logger.info(f"Total files processed: {self.total_files_processed}")
        self.logger.info(f"Files skipped (unchanged): {self.total_files_skipped_unchanged}")
        self.logger.info(f"Files failed hashing: {self.total_files_failed_hash}")
        self.logger.info(f"Files failed structural parsing: {self.total_files_failed_structure_parse}")
        self.logger.info(f"Total code objects extracted and stored: {self.total_objects_extracted}")
        self.logger.info(f"Objects failed signature parsing: {self.total_objects_failed_signature}")
        self.logger.info(f"Objects failed call extraction: {self.total_objects_failed_calls}")
        self.logger.info(f"Objects failed database addition: {self.total_objects_failed_db_add}")
        self.logger.info("--------------------------")
