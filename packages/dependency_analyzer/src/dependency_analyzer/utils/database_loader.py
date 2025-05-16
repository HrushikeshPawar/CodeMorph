"""
DatabaseLoader for the Dependency Analyzer.

This module is responsible for loading PL/SQL code object data from the
database populated by the `plsql_analyzer` package. It reconstructs
`PLSQL_CodeObject` instances, including their parsed parameters and
extracted call details.
"""
from __future__ import annotations
from typing import List
import loguru as lg

# Imports from plsql_analyzer package
# These assume plsql_analyzer is installed or accessible in PYTHONPATH
try:
    from plsql_analyzer.core.code_object import PLSQL_CodeObject
    from plsql_analyzer.persistence.database_manager import DatabaseManager
except ImportError as e:
    # Provide a more helpful error message if plsql_analyzer is not found
    lg.logger.critical(
        f"Failed to import from 'plsql_analyzer'. Ensure it's installed and in PYTHONPATH. Error: {e}"
    )
    raise

class DatabaseLoader:
    """
    Loads PL/SQL code objects and their details from the database.

    Interacts with the `DatabaseManager` from `plsql_analyzer` to query
    the necessary tables and reconstruct `PLSQL_CodeObject` instances
    that can be used by the `GraphConstructor`.
    """

    def __init__(self, db_manager: DatabaseManager, logger: lg.Logger):
        """
        Initializes the DatabaseLoader.

        Args:
            db_manager: An instance of `DatabaseManager` from `plsql_analyzer`
                        configured to connect to the target database.
            logger: A Loguru logger instance for logging messages.
        """
        self.db_manager = db_manager
        self.logger = logger.bind(class_name=self.__class__.__name__)
        self.logger.info("DatabaseLoader initialized.")

    def load_all_objects(self) -> List[PLSQL_CodeObject]:
        """
        Loads all PL/SQL code objects from the database.

        This method queries the `code_objects` table and, for each object,
        queries the `object_calls` table to retrieve its dependencies.
        It then reconstructs `PLSQL_CodeObject` instances.

        Returns:
            A list of `PLSQL_CodeObject` instances.
        """
        self.logger.info("Starting to load all code objects from the database.")
        code_objects_list: List[PLSQL_CodeObject] = []

        try:
            object_rows = self.db_manager.get_all_codeobjects()
            self.logger.info(f"Retrieved {len(object_rows)} raw object records from 'code_objects' table.")

            for obj_row_dict in object_rows:
                # obj_row_dict is already a dictionary if row_factory was sqlite3.Row
                self.logger.debug(f"Attempting to reconstruct PLSQL_CodeObject from row: {obj_row_dict.get('id', 'UNKNOWN_ID')}")
                try:
                    code_obj = PLSQL_CodeObject.from_dict(obj_row_dict)
                    self.logger.debug(f"Successfully reconstructed PLSQL_CodeObject: {code_obj.id}")
                    code_objects_list.append(code_obj)

                except Exception as e:
                    obj_id_for_log = obj_row_dict.get('id', 'UNKNOWN_ID')
                    self.logger.error(
                        f"Failed to reconstruct PLSQL_CodeObject for ID '{obj_id_for_log}': {e}. Skipping this object.",
                        exc_info=True
                    )
                    self.logger.debug(f"Problematic row data: {obj_row_dict}")


            self.logger.info(f"Successfully loaded and reconstructed {len(code_objects_list)} PLSQL_CodeObject instances.")

        except Exception as e: # Catch broader SQLite errors or other unexpected issues
            self.logger.critical(f"An error occurred during database operations: {e}", exc_info=True)
            # Depending on policy, might re-raise or return empty list
            return [] # Return empty list on critical failure

        return code_objects_list

if __name__ == "__main__":
    # This is an example of how to use the DatabaseLoader.
    # It requires a valid database populated by plsql_analyzer.

    # --- Setup for example ---
    from pathlib import Path
    # Assuming this script is in packages/dependency_analyzer/src/dependency_analyzer/loader/
    # Adjust path to config and logging_setup accordingly
    project_root_example = Path(__file__).resolve().parent.parent.parent.parent.parent
    
    # Add project root to sys.path to allow finding other packages
    import sys
    if str(project_root_example) not in sys.path:
        sys.path.insert(0, str(project_root_example))

    try:
        from dependency_analyzer import config as da_config
        from dependency_analyzer.utils.logging_setup import configure_logger as da_configure_logger
    except ImportError:
        print("Could not import dependency_analyzer config/logging. Ensure PYTHONPATH is set or run from project root.")
        sys.exit(1)

    # 1. Configure Logger
    da_config.ensure_artifact_dirs() # Ensure log directory exists
    example_logger = da_configure_logger(da_config.LOG_VERBOSE_LEVEL, da_config.LOGS_DIR)
    example_logger.info("--- DatabaseLoader Example ---")

    # 2. DatabaseManager (from plsql_analyzer)
    # Ensure DATABASE_PATH in da_config points to your plsql_analyzer.db
    if not da_config.DATABASE_PATH.exists():
        example_logger.error(f"Database file not found at: {da_config.DATABASE_PATH}")
        example_logger.error("Please ensure plsql_analyzer has run and created the database, or update DATABASE_PATH in config.")
    else:
        example_db_manager = DatabaseManager(da_config.DATABASE_PATH, example_logger)

        # 3. Initialize DatabaseLoader
        loader = DatabaseLoader(example_db_manager, example_logger)

        # 4. Load objects
        loaded_code_objects = loader.load_all_objects()

        if loaded_code_objects:
            example_logger.info(f"Successfully loaded {len(loaded_code_objects)} code objects.")
            for i, obj in enumerate(loaded_code_objects[:5]): # Print details of first 5 objects
                example_logger.info(
                    f"  Obj {i+1}: ID={obj.id}, Type={obj.type.name}, Name='{obj.name}', Pkg='{obj.package_name}', "
                    f"Overloaded={obj.overloaded}, Params#={len(obj.parsed_parameters)}, Calls#={len(obj.extracted_calls)}"
                )
                if obj.extracted_calls:
                    example_logger.debug(f"    Example call for {obj.id}: {obj.extracted_calls[0]}")
            if len(loaded_code_objects) > 5:
                example_logger.info(f"  ... and {len(loaded_code_objects) - 5} more objects.")
        else:
            example_logger.warning("No code objects were loaded. Check database content and logs.")

    example_logger.info("--- DatabaseLoader Example Finished ---")