# plsql_analyzer/utils/file_helpers.py
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import List, Optional
import loguru as lg  # Expect logger to be passed or use a module-level one

class FileHelpers:
    def __init__(self, logger: lg.Logger):
        self.logger = logger.bind(helper_class="FileHelpers")

    def compute_file_hash(self, fpath: Path, algorithm: str = "sha256") -> Optional[str]:
        """Calculate the hash of a file."""
        self.logger.trace(f"Computing {algorithm} hash for file: {fpath}")
        try:
            if not fpath.is_file():
                self.logger.error(f"File not found for hashing: {fpath}")
                return None

            hash_func = hashlib.new(algorithm)
            with open(fpath, 'rb') as f:
                while chunk := f.read(2**16): # Read in 64k chunks
                    hash_func.update(chunk)
            hex_digest = hash_func.hexdigest()
            self.logger.trace(f"Computed hash for {fpath}: {hex_digest[:10]}...")
            return hex_digest
        except FileNotFoundError: # Should be caught by is_file(), but good to have
            self.logger.error(f"Error: File not found at `{fpath}` during hash computation.")
            return None
        except ValueError: # For invalid algorithm name
            self.logger.error(f"Error: Invalid hashing algorithm: `{algorithm}` for file {fpath}.")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred during hash computation for {fpath}: {e}")
            self.logger.exception(e)
            return None

    def get_processed_fpath(self, fpath: Path, exclude_from_path: List[str]) -> Path:
        """
        Creates a string representation of the file path, excluding specified parent directories.
        This is useful for storing a relative or cleaner path in the database.
        """
        self.logger.trace(f"Processing fpath string for {fpath} excluding {exclude_from_path}")
        try:
            new_fpath_parts = []
            # Normalize exclusion list to lowercase for case-insensitive comparison
            exclude_from_path_lower = [x.casefold() for x in exclude_from_path]

            # Iterate through each part of the original file path
            for part in fpath.parts:
                # Log the current part being considered
                self.logger.trace(f"Considering path part: '{part}'")
                # If the current part (case-insensitive) is not in the exclusion list, add it
                if part.casefold() not in exclude_from_path_lower:
                    self.logger.trace(f"Including path part: '{part}'")
                    new_fpath_parts.append(part)
                else:
                    self.logger.trace(f"Excluding path part: '{part}' (found in exclusion list)")
            
            # Reconstruct the path from the filtered parts
            # Using Path(*new_fpath_parts) might not be ideal if new_fpath_parts is empty
            # or if it results in a relative path when an absolute one might be expected.
            # However, the goal is a string representation.
           
            if not new_fpath_parts:
                # If all parts were excluded, return the original filename or a placeholder
                self.logger.warning(f"All parts of path {fpath} were excluded. Returning filename: {fpath.name}")
                return fpath.name # Or consider fpath.as_posix() if full path is better fallback

            # Create a new Path object from the remaining parts
            processed_path = Path(*new_fpath_parts)
            self.logger.trace(f"Processed path for {fpath} is: {processed_path}")

            return processed_path

        except Exception as e:
            # This can happen with Path.is_relative_to if paths are on different drives on Windows
            self.logger.warning(f"Could not determine relative path for {fpath} against exclusions. Falling back to full path. Error: {e}")
            return fpath

    def derive_package_name_from_path(self,
                                   package_name_from_code: Optional[str],
                                   fpath: Path,
                                   file_extensions: List[str],
                                   exclude_parts_for_pkg_derivation: List[str]) -> str:
        """
        Derives a package name from the file path, prepending parts of the
        path to an existing package name found in the code, if any.
        Excludes specified directory names (case-insensitively) from being part of the package name.
        Uniqueness of combined parts is also checked case-insensitively.
        The final package name string is casefolded.
        """

        self.logger.trace(f"Deriving package name for file '{fpath}'. Initial package from code: '{package_name_from_code}'. Excluding path parts: {exclude_parts_for_pkg_derivation}. File extensions: {file_extensions}")

        # Normalize exclusion parts to lowercase for case-insensitive comparison
        exclude_parts_lower = [part.casefold() for part in exclude_parts_for_pkg_derivation]

        # 1. Collect path-derived components (stripped, original case)
        # These are potential prefixes to be added to the package name.
        derived_path_components_original_case = []
        for path_segment in fpath.parts:
            # Log the current path segment being processed
            self.logger.trace(f"Processing path segment: '{path_segment}'")

            # Remove file extension (if present) from the current path segment
            # NOTE: This logic might incorrectly remove parts of directory names if they match '.{file_extension}'
            file_extension = None
            for ext in file_extensions:
                if path_segment.endswith(f'.{ext}'):
                    file_extension = ext
                    self.logger.trace(f"File extension found: '{file_extension}' for segment '{path_segment}'")
                    break

            if file_extension:
                name_part = path_segment.replace(f'.{file_extension}', '')
            else:
                name_part = path_segment

            if name_part != path_segment:
                self.logger.trace(f"Segment '{path_segment}' potentially stripped extension to '{name_part}'")

            # Case-insensitive check for exclusion
            if name_part.casefold() not in exclude_parts_lower:
                self.logger.trace(f"Segment '{path_segment}' (name_part '{name_part}') not in exclusion list.")
                # Split the remaining part by '.' (e.g., "schema.object")
                # and add non-empty, stripped sub-components
                sub_components = name_part.split('.')
                for sc in sub_components:
                    stripped_sc = sc.strip()
                    if stripped_sc: # Ensure non-empty after stripping
                        self.logger.trace(f"Adding derived component: '{stripped_sc}'")
                        derived_path_components_original_case.append(stripped_sc)
                    else:
                        self.logger.trace(f"Skipping empty sub-component from '{name_part}'")
            else:
                self.logger.trace(f"Path segment '{path_segment}' (name_part '{name_part}') excluded based on exclusion list.")
        
        self.logger.trace(f"Path-derived components (original case, stripped): {derived_path_components_original_case}")

        # 2. Initialize lists for building the final package name:
        #    - `seen_components`: stores casefolded versions for ensuring uniqueness.
        seen_components = []

        # Add parts from 'package_name_from_code' first, preserving their original casing for joining,
        # but using casefolded versions for uniqueness tracking.
        if package_name_from_code:
            initial_parts_stripped = [p.strip() for p in package_name_from_code.split('.') if p.strip()]
            for part in initial_parts_stripped:
                # Since these are the first parts, they are unique by definition so far.
                seen_components.append(part.casefold()) # Store casefolded for uniqueness check
        
        self.logger.trace(f"After processing package_name_from_code: {seen_components}")

        # 3. Prepend path-derived components if they are not already present (case-insensitively)
        #    Iterate in reverse to prepend correctly (e.g., 'folder', 'subfolder' -> 'folder.subfolder')
        for path_component_orig_case in derived_path_components_original_case:
            path_component_casefolded = path_component_orig_case.casefold()
            
            if path_component_casefolded not in seen_components:
                # Prepend the component for joining
                seen_components.append(path_component_casefolded)
                self.logger.trace(f"Prepended path component '{path_component_orig_case}'. Current ordered parts: {seen_components}")
            else:
                self.logger.trace(f"Path component '{path_component_orig_case}' (casefolded '{path_component_casefolded}') already effectively present, skipping.")
        
        # 4. Join to form the final package name string and then casefold it for consistent output.
        intermediate_package_name_str = ".".join(seen_components)
        final_package_name_casefolded = intermediate_package_name_str.casefold()

        self.logger.debug(f"Derived final package name for '{fpath}' as: '{final_package_name_casefolded}' (from intermediate form: '{intermediate_package_name_str}')")
        return final_package_name_casefolded

    def escape_angle_brackets(self, text:str) -> str:
        # For logging, to prevent loguru from interpreting < > as tags
        return text.replace("<", "\\<").replace(">", "\\>")
