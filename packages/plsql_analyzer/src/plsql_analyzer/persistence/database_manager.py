# plsql_analyzer/persistence/database_manager.py
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import loguru as lg # Assuming logger is passed

if TYPE_CHECKING:
    from plsql_analyzer.core.code_object import PLSQL_CodeObject


# SQLite type adapters/converters
def adapt_datetime_iso(val: datetime) -> str:
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

def convert_datetime(val: bytes) -> datetime: # val is bytes
    """Convert ISO 8601 datetime string from DB to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime) # Name should be "datetime" not "TIMESTAMP" for auto-detection by PARSE_DECLTYPES


class DatabaseManager:
    def __init__(self, db_path: Path, logger: lg.Logger):
        self.db_path = db_path
        self.logger = logger.bind(db_path=str(db_path))
        self._ensure_db_dir_exists()

    def _ensure_db_dir_exists(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Ensured database directory exists: {self.db_path.parent}")

    def _connect(self) -> sqlite3.Connection:
        self.logger.trace("Trying to connect to DB")
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        self.logger.trace("Database connection established.")
        return conn

    def setup_database(self):
        self.logger.info("Setting up database schemas (if needed).")
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Processed_PLSQL_Files (
                        file_path TEXT PRIMARY KEY,
                        file_hash TEXT NOT NULL,
                        last_processed_ts DATETIME NOT NULL 
                    )
                """) # Use DATETIME for sqlite3.PARSE_DECLTYPES
                self.logger.debug("Checked/Created TABLE: Processed_PLSQL_Files")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Extracted_PLSQL_CodeObjects (
                        id TEXT PRIMARY KEY, -- Using the generated ID from PLSQL_CodeObject
                        file_path TEXT NOT NULL,
                        package_name TEXT,
                        object_name TEXT NOT NULL,
                        object_type TEXT NOT NULL,
                        codeobject_data TEXT NOT NULL, -- JSON representation of the PLSQL_CodeObject
                        processing_ts DATETIME NOT NULL,
                        FOREIGN KEY (file_path) REFERENCES Processed_PLSQL_Files (file_path)
                            ON DELETE CASCADE
                    )
                """)
                self.logger.debug("Checked/Created TABLE: Extracted_PLSQL_CodeObjects")

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_co_file_path ON Extracted_PLSQL_CodeObjects (file_path)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_co_package_name ON Extracted_PLSQL_CodeObjects (package_name)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_co_object_name ON Extracted_PLSQL_CodeObjects (object_name)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_co_object_type ON Extracted_PLSQL_CodeObjects (object_type)
                """)
                self.logger.debug("Checked/Created INDEXES for Extracted_PLSQL_CodeObjects")
                conn.commit()
                self.logger.success("Database setup verification/completed.")
        except sqlite3.Error as e:
            self.logger.error("Database setup failed.")
            self.logger.exception(e)
            raise # Re-raise to halt execution if DB setup fails

    def get_file_hash(self, fpath: str) -> Optional[str]:
        self.logger.debug(f"Querying stored hash for {fpath}")
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_hash FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
                result = cursor.fetchone()
                if result:
                    self.logger.debug(f"Found stored hash: {result['file_hash'][:10]}... for: {fpath}")
                    return result["file_hash"]
                else:
                    self.logger.debug(f"No stored hash found for: {fpath}")
                    return None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve hash for: {fpath}")
            self.logger.exception(e)
            # Should this raise? Or just return None and let workflow decide?
            # For now, returning None is less disruptive.
            return None

    def update_file_hash(self, fpath: str, file_hash: str) -> bool:
        self.logger.debug(f"Updating Hash for: {fpath}")
        now_ts = datetime.now(timezone.utc)
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # Clear old code objects associated with this file path before updating hash
                # This handles cases where a file is changed and objects are removed/renamed
                cursor.execute("DELETE FROM Extracted_PLSQL_CodeObjects WHERE file_path = ?", (fpath,))
                self.logger.debug(f"Deleted old code objects for {fpath} before hash update.")

                cursor.execute(
                    "INSERT OR REPLACE INTO Processed_PLSQL_Files (file_path, file_hash, last_processed_ts) VALUES (?, ?, ?)",
                    (fpath, file_hash, now_ts)
                )
                conn.commit()
                self.logger.debug(f"Inserted/Replaced hash record for {fpath}")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Database transaction failed for hash update of {fpath}")
            self.logger.exception(e)
            return False

    def remove_file_record(self, fpath: str) -> bool:
        """Removes a file record and its associated code objects from the database."""
        self.logger.debug(f"Attempting to remove file record for: {fpath}")
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # The ON DELETE CASCADE constraint on Extracted_PLSQL_CodeObjects.file_path
                # will ensure associated code objects are also deleted.
                cursor.execute("DELETE FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
                conn.commit()
                if cursor.rowcount > 0:
                    self.logger.info(f"Successfully removed file record and associated code objects for {fpath}.")
                    return True
                else:
                    self.logger.warning(f"No file record found for {fpath} to remove. Considered successful as record is not present.")
                    return True # If the goal is to ensure the record is not there, not finding it is also a success.
        except sqlite3.Error as e:
            self.logger.error(f"Database error while removing file record for {fpath}.")
            self.logger.exception(e)
            return False

    def add_codeobject(self, codeobject: 'PLSQL_CodeObject', fpath: str) -> bool:
        obj_repr_for_log = f"{codeobject.package_name}.{codeobject.name}" if codeobject.package_name else codeobject.name
        self.logger.debug(f"Adding codeobject {obj_repr_for_log} (ID: {codeobject.id}) for file {fpath}")
        now_ts = datetime.now(timezone.utc)
        
        if not codeobject.id:
            self.logger.error(f"Code object {obj_repr_for_log} has no ID. Cannot add to DB.")
            return False

        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                code_obj_dict_for_db = codeobject.to_dict()
                
                # The 'source' key might be very large. Consider if it's truly needed in the main JSON.
                # If full source is in code_obj_dict_for_db['source'], ensure it's handled.
                # The current to_dict does not include full source.
                # source_code = code_obj_dict_for_db.pop('source', None) # Example if source was included

                cursor.execute(
                    """INSERT OR REPLACE INTO Extracted_PLSQL_CodeObjects 
                       (id, file_path, package_name, object_name, object_type, codeobject_data, processing_ts) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        codeobject.id,
                        str(fpath),
                        codeobject.package_name,
                        codeobject.name,
                        codeobject.type.value.upper(),
                        json.dumps(code_obj_dict_for_db, indent=4),
                        now_ts
                    )
                )
                conn.commit()
                self.logger.debug(f"Inserted/Replaced {obj_repr_for_log} (ID: {codeobject.id}) for {fpath}")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Database transaction failed for {obj_repr_for_log} (ID: {codeobject.id})")
            self.logger.exception(e)
            return False
            
    def get_all_codeobjects(self) -> list[dict]:
        """Retrieves all code objects from the database."""
        self.logger.debug("Fetching all code objects from database.")
        objects = []
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, package_name, object_name, object_type, codeobject_data FROM Extracted_PLSQL_CodeObjects")
                for row in cursor.fetchall():
                    obj_data = json.loads(row["codeobject_data"])
                    # # Augment with direct columns if not already in JSON or for quick access
                    # obj_data['db_id'] = row['id'] 
                    # obj_data['db_package_name'] = row['package_name']
                    # obj_data['db_object_name'] = row['object_name']
                    # obj_data['db_object_type'] = row['object_type']
                    objects.append(obj_data)
            self.logger.info(f"Retrieved {len(objects)} code objects from the database.")
        except sqlite3.Error as e:
            self.logger.error("Failed to retrieve code objects from database.")
            self.logger.exception(e)
        return objects
