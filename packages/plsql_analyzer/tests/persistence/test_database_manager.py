import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, Optional

# Assuming conftest.py is in the parent directory or accessible via pythonpath
# from ..conftest import test_logger, temp_db_path (if running with pytest from root)
# For direct execution or simpler structure, ensure conftest.py is discoverable

from plsql_analyzer.persistence.database_manager import DatabaseManager, adapt_datetime_iso, convert_datetime

# Mock for PLSQL_CodeObject and its ObjectType enum
class MockObjectType(Enum):
    PROCEDURE = "PROCEDURE"
    FUNCTION = "FUNCTION"
    PACKAGE = "PACKAGE"
    PACKAGE_BODY = "PACKAGE_BODY"
    TYPE = "TYPE"
    TRIGGER = "TRIGGER"
    UNKNOWN = "UNKNOWN"

class MockPLSQLCodeObject:
    def __init__(self, id: Optional[str], name: str, obj_type: MockObjectType, package_name: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        self.id = id
        self.name = name
        self.type = obj_type
        self.package_name = package_name
        self._data = data if data is not None else {}
        # Ensure essential keys are present for to_dict as expected by DatabaseManager
        self._data.setdefault("declarations", [])
        self._data.setdefault("body", "")
        self._data.setdefault("dependencies", [])


    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value, # Use enum value
            "package_name": self.package_name,
            "source_lines": self._data.get("source_lines", [1,10]),
            "declarations": self._data.get("declarations"),
            "body_start_line": self._data.get("body_start_line", 5),
            "dependencies": self._data.get("dependencies"),
            # Add other fields that the actual PLSQL_CodeObject.to_dict() might return
        }

@pytest.fixture
def db_manager(temp_db_path: Path, test_logger):
    """Fixture to provide a DatabaseManager instance with a temporary DB path."""
    return DatabaseManager(db_path=temp_db_path, logger=test_logger)

@pytest.fixture
def initialized_db_manager(db_manager: DatabaseManager):
    """Fixture to provide a DatabaseManager instance with the database schema set up."""
    db_manager.setup_database()
    return db_manager

def test_database_manager_init_ensures_dir_exists(temp_db_path: Path, test_logger, caplog):
    """Test that initializing DatabaseManager creates the database directory."""
    db_parent_dir = temp_db_path.parent
    if db_parent_dir.exists(): # Clean up if exists from other test runs in same tmp
        for item in db_parent_dir.iterdir():
            if item.is_file(): item.unlink()
            else: pytest.fail("Unexpected subdir in temp_db_path.parent") # safety
    # else: # Directory does not exist, which is the state we want to test creation from

    assert not temp_db_path.exists(), "DB file should not exist before init"
    assert not db_parent_dir.exists() or not any(db_parent_dir.iterdir()), "DB parent dir should be empty or not exist"

    DatabaseManager(db_path=temp_db_path, logger=test_logger)
    assert db_parent_dir.exists(), "Database directory was not created"
    assert f"Ensured database directory exists: {db_parent_dir}" in caplog.text

def test_setup_database_creates_schema(initialized_db_manager: DatabaseManager):
    """Test that setup_database creates the necessary tables and indexes."""
    db_path = initialized_db_manager.db_path
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check for Processed_PLSQL_Files table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Processed_PLSQL_Files'")
        assert cursor.fetchone() is not None, "Processed_PLSQL_Files table not created"

        # Check for Extracted_PLSQL_CodeObjects table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Extracted_PLSQL_CodeObjects'")
        assert cursor.fetchone() is not None, "Extracted_PLSQL_CodeObjects table not created"

        # Check for indexes on Extracted_PLSQL_CodeObjects
        expected_indexes = [
            "idx_co_file_path", 
            "idx_co_package_name", 
            "idx_co_object_name", 
            "idx_co_object_type"
        ]
        for index_name in expected_indexes:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
            assert cursor.fetchone() is not None, f"Index {index_name} not created"

def test_datetime_adapter_converter():
    """Test the custom datetime adapter and converter."""
    dt_aware = datetime.now(timezone.utc)
    dt_naive = datetime.now()

    # Test adapter
    iso_aware = adapt_datetime_iso(dt_aware)
    assert dt_aware.isoformat() == iso_aware
    iso_naive = adapt_datetime_iso(dt_naive)
    assert dt_naive.isoformat() == iso_naive
    
    # Test converter
    # The converter expects bytes, as SQLite provides strings as bytes to converters
    converted_dt_aware = convert_datetime(iso_aware.encode('utf-8'))
    assert converted_dt_aware == dt_aware

    converted_dt_naive = convert_datetime(iso_naive.encode('utf-8'))
    assert converted_dt_naive == dt_naive

def test_datetime_storage_and_retrieval(initialized_db_manager: DatabaseManager):
    """Test that datetime objects are stored and retrieved correctly."""
    fpath = "test_dt_file.sql"
    file_hash = "dt_hash"
    now_utc = datetime.now(timezone.utc)

    # Use update_file_hash as it stores a datetime
    initialized_db_manager.update_file_hash(fpath, file_hash)

    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_processed_ts FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
        row = cursor.fetchone()
        assert row is not None
        retrieved_ts = row["last_processed_ts"]
        assert isinstance(retrieved_ts, datetime)
        assert retrieved_ts.tzinfo == timezone.utc
        # Allow for slight difference due to DB write/read and precision
        assert abs((retrieved_ts - now_utc).total_seconds()) < 1 

def test_update_and_get_file_hash(initialized_db_manager: DatabaseManager, caplog):
    """Test updating and retrieving file hashes."""
    fpath = "test_file.sql"
    hash1 = "hash123"
    hash2 = "hash456"

    # Test get_file_hash for non-existent file
    assert initialized_db_manager.get_file_hash(fpath) is None
    assert f"No stored hash found for: {fpath}" in caplog.text

    # Test update_file_hash for a new file
    caplog.clear()
    assert initialized_db_manager.update_file_hash(fpath, hash1) is True
    assert f"Inserted/Replaced hash record for {fpath}" in caplog.text
    
    stored_hash1 = initialized_db_manager.get_file_hash(fpath)
    assert stored_hash1 == hash1

    # Verify timestamp was set
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_processed_ts FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
        ts1 = cursor.fetchone()["last_processed_ts"]
        assert isinstance(ts1, datetime)

    # Test update_file_hash for an existing file (should replace)
    # Ensure time moves forward enough to see a change in timestamp
    # Forcing a slight delay or mocking datetime.now is an option, but usually not needed if operations are quick
    # For robustness, we can check it's at least the same or newer.
    caplog.clear()
    assert initialized_db_manager.update_file_hash(fpath, hash2) is True
    assert f"Inserted/Replaced hash record for {fpath}" in caplog.text

    stored_hash2 = initialized_db_manager.get_file_hash(fpath)
    assert stored_hash2 == hash2

    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_processed_ts FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
        ts2 = cursor.fetchone()["last_processed_ts"]
        assert isinstance(ts2, datetime)
        assert ts2 >= ts1 # Timestamp should be updated or same if operations are very fast

def test_add_and_get_all_codeobjects(initialized_db_manager: DatabaseManager, caplog):
    """Test adding and retrieving code objects."""
    fpath1 = "file1.sql"
    fpath2 = "file2.sql"
    initialized_db_manager.update_file_hash(fpath1, "hash1")
    initialized_db_manager.update_file_hash(fpath2, "hash2")

    obj1_data = {"declarations": ["v_num NUMBER;"], "body": "BEGIN NULL; END;"}
    obj1 = MockPLSQLCodeObject(id="pkg1.proc1", name="Proc1", obj_type=MockObjectType.PROCEDURE, package_name="Pkg1", data=obj1_data)
    
    obj2_data = {"body": "RETURN TRUE;"}
    obj2 = MockPLSQLCodeObject(id="func1", name="Func1", obj_type=MockObjectType.FUNCTION, data=obj2_data)

    assert initialized_db_manager.add_codeobject(obj1, fpath1) is True
    assert f"Inserted/Replaced Pkg1.Proc1 (ID: {obj1.id}) for {fpath1}" in caplog.text
    caplog.clear()
    assert initialized_db_manager.add_codeobject(obj2, fpath2) is True
    assert f"Inserted/Replaced Func1 (ID: {obj2.id}) for {fpath2}" in caplog.text

    retrieved_objects = initialized_db_manager.get_all_codeobjects()
    assert len(retrieved_objects) == 2

    retrieved_obj1_dict = next((o for o in retrieved_objects if o["id"] == obj1.id), None)
    retrieved_obj2_dict = next((o for o in retrieved_objects if o["id"] == obj2.id), None)

    assert retrieved_obj1_dict is not None
    assert retrieved_obj2_dict is not None

    # Verify augmented fields
    assert retrieved_obj1_dict["db_id"] == obj1.id
    assert retrieved_obj1_dict["db_package_name"] == obj1.package_name
    assert retrieved_obj1_dict["db_object_name"] == obj1.name
    assert retrieved_obj1_dict["db_object_type"] == obj1.type.value

    # Verify original data from to_dict()
    expected_obj1_dict = obj1.to_dict()
    for k, v in expected_obj1_dict.items():
        assert retrieved_obj1_dict[k] == v
    
    expected_obj2_dict = obj2.to_dict()
    for k, v in expected_obj2_dict.items():
        assert retrieved_obj2_dict[k] == v
    
    # Check processing_ts was set
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT processing_ts FROM Extracted_PLSQL_CodeObjects WHERE id = ?", (obj1.id,))
        ts = cursor.fetchone()["processing_ts"]
        assert isinstance(ts, datetime)
        assert ts.tzinfo == timezone.utc

def test_add_codeobject_no_id_fails(initialized_db_manager: DatabaseManager, caplog):
    """Test that adding a code object with no ID fails and logs an error."""
    fpath = "test_file_no_id.sql"
    initialized_db_manager.update_file_hash(fpath, "hash_no_id") # Prerequisite

    code_obj_no_id = MockPLSQLCodeObject(id=None, name="NoIDProc", obj_type=MockObjectType.PROCEDURE)
    
    assert initialized_db_manager.add_codeobject(code_obj_no_id, fpath) is False
    assert f"Code object {code_obj_no_id.name} has no ID. Cannot add to DB." in caplog.text

def test_get_all_codeobjects_empty_db(initialized_db_manager: DatabaseManager):
    """Test retrieving code objects from an empty (but initialized) database."""
    assert initialized_db_manager.get_all_codeobjects() == []

def test_update_file_hash_deletes_old_codeobjects(initialized_db_manager: DatabaseManager, caplog):
    """Test that update_file_hash deletes code objects associated with the old file hash."""
    fpath = "test_file_rehash.sql"
    hash1 = "initial_hash_rehash"
    hash2 = "updated_hash_rehash"

    initialized_db_manager.update_file_hash(fpath, hash1)

    code_obj = MockPLSQLCodeObject(id="rehash_obj", name="TestRehash", obj_type=MockObjectType.PROCEDURE)
    assert initialized_db_manager.add_codeobject(code_obj, fpath) is True
    
    # Verify object exists
    objects = initialized_db_manager.get_all_codeobjects()
    assert any(o["id"] == code_obj.id for o in objects)

    # Update the hash for the same file
    caplog.clear()
    assert initialized_db_manager.update_file_hash(fpath, hash2) is True
    assert f"Deleted old code objects for {fpath} before hash update." in caplog.text
    
    # Verify the old object is gone
    objects_after_rehash = initialized_db_manager.get_all_codeobjects()
    assert not any(o["id"] == code_obj.id for o in objects_after_rehash), \
        "Old code object was not deleted after file hash update"

def test_foreign_key_cascade_delete_on_processed_file_deletion(initialized_db_manager: DatabaseManager):
    """
    Test that deleting a record from Processed_PLSQL_Files cascades
    and deletes associated records from Extracted_PLSQL_CodeObjects.
    """
    fpath = "test_file_fk_cascade.sql"
    file_hash = "fk_hash_cascade"

    initialized_db_manager.update_file_hash(fpath, file_hash)

    code_obj1 = MockPLSQLCodeObject(id="fk_obj1", name="TestFK1", obj_type=MockObjectType.PROCEDURE)
    code_obj2 = MockPLSQLCodeObject(id="fk_obj2", name="TestFK2", obj_type=MockObjectType.FUNCTION, package_name="MyPkg")
    
    assert initialized_db_manager.add_codeobject(code_obj1, fpath) is True
    assert initialized_db_manager.add_codeobject(code_obj2, fpath) is True

    # Verify objects exist
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Extracted_PLSQL_CodeObjects WHERE file_path = ?", (fpath,))
        assert cursor.fetchone()[0] == 2

    # Manually delete the record from Processed_PLSQL_Files
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Processed_PLSQL_Files WHERE file_path = ?", (fpath,))
        conn.commit()
        assert cursor.rowcount == 1, "Processed_PLSQL_Files record not deleted"

    # Verify associated code objects are also deleted due to CASCADE
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Extracted_PLSQL_CodeObjects WHERE file_path = ?", (fpath,))
        assert cursor.fetchone()[0] == 0, "Code objects not deleted by cascade rule"

    # Also check via the manager's method
    all_objects = initialized_db_manager.get_all_codeobjects()
    assert not any(o["id"] == code_obj1.id for o in all_objects)
    assert not any(o["id"] == code_obj2.id for o in all_objects)

def test_add_codeobject_replace(initialized_db_manager: DatabaseManager):
    """Test that adding a code object with an existing ID replaces the old one."""
    fpath = "test_file_replace.sql"
    initialized_db_manager.update_file_hash(fpath, "hash_replace")

    obj_id = "replaceable_obj"
    obj_v1_data = {"declarations": ["v_old VARCHAR2(10);"]}
    obj_v1 = MockPLSQLCodeObject(id=obj_id, name="Replaceable", obj_type=MockObjectType.PROCEDURE, data=obj_v1_data)
    
    assert initialized_db_manager.add_codeobject(obj_v1, fpath) is True
    
    retrieved_v1 = initialized_db_manager.get_all_codeobjects()
    assert len(retrieved_v1) == 1
    assert retrieved_v1[0]["declarations"] == obj_v1_data["declarations"]

    obj_v2_data = {"declarations": ["v_new NUMBER;"]} # Different data
    obj_v2 = MockPLSQLCodeObject(id=obj_id, name="Replaceable", obj_type=MockObjectType.PROCEDURE, data=obj_v2_data) # Same ID

    assert initialized_db_manager.add_codeobject(obj_v2, fpath) is True

    retrieved_v2 = initialized_db_manager.get_all_codeobjects()
    assert len(retrieved_v2) == 1 # Should still be one object
    assert retrieved_v2[0]["id"] == obj_id
    assert retrieved_v2[0]["declarations"] == obj_v2_data["declarations"] # Data should be updated
    assert retrieved_v2[0]["name"] == obj_v2.name # Other fields should also reflect v2 if changed

def test_remove_file_record_success(initialized_db_manager: DatabaseManager, caplog):
    """Test successfully removing a file record and its associated code objects."""
    fpath = "test_file_to_remove.sql"
    file_hash = "hash_to_remove"

    # Add a file record
    assert initialized_db_manager.update_file_hash(fpath, file_hash) is True

    # Add associated code objects
    obj1 = MockPLSQLCodeObject(id="rem_obj1", name="RemoveObj1", obj_type=MockObjectType.PROCEDURE)
    obj2 = MockPLSQLCodeObject(id="rem_obj2", name="RemoveObj2", obj_type=MockObjectType.FUNCTION)
    assert initialized_db_manager.add_codeobject(obj1, fpath) is True
    assert initialized_db_manager.add_codeobject(obj2, fpath) is True

    # Verify file and objects exist
    assert initialized_db_manager.get_file_hash(fpath) == file_hash
    all_objects = initialized_db_manager.get_all_codeobjects()
    assert any(o["id"] == obj1.id for o in all_objects)
    assert any(o["id"] == obj2.id for o in all_objects)
    
    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Extracted_PLSQL_CodeObjects WHERE file_path = ?", (fpath,))
        assert cursor.fetchone()[0] == 2

    caplog.clear()
    # Remove the file record
    assert initialized_db_manager.remove_file_record(fpath) is True
    assert f"Successfully removed file record and associated code objects for {fpath}" in caplog.text

    # Verify file record is removed
    assert initialized_db_manager.get_file_hash(fpath) is None

    # Verify associated code objects are removed (due to ON DELETE CASCADE)
    all_objects_after_remove = initialized_db_manager.get_all_codeobjects()
    assert not any(o["id"] == obj1.id for o in all_objects_after_remove)
    assert not any(o["id"] == obj2.id for o in all_objects_after_remove)

    with initialized_db_manager._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Extracted_PLSQL_CodeObjects WHERE file_path = ?", (fpath,))
        assert cursor.fetchone()[0] == 0, "Code objects were not deleted after removing file record"

def test_remove_file_record_non_existent(initialized_db_manager: DatabaseManager, caplog):
    """Test attempting to remove a file record that does not exist."""
    fpath_non_existent = "non_existent_file.sql"

    caplog.clear()
    assert initialized_db_manager.remove_file_record(fpath_non_existent) is True
    assert f"No file record found for {fpath_non_existent} to remove. Considered successful as record is not present." in caplog.text

    # Verify no side effects (e.g., other records deleted)
    fpath_existing = "existing_file.sql"
    hash_existing = "existing_hash"
    initialized_db_manager.update_file_hash(fpath_existing, hash_existing)
    obj_existing = MockPLSQLCodeObject(id="existing_obj", name="ExistingObj", obj_type=MockObjectType.PROCEDURE)
    initialized_db_manager.add_codeobject(obj_existing, fpath_existing)

    initialized_db_manager.remove_file_record(fpath_non_existent) # Call again to ensure no impact

    assert initialized_db_manager.get_file_hash(fpath_existing) == hash_existing
    all_objects = initialized_db_manager.get_all_codeobjects()
    assert any(o["id"] == obj_existing.id for o in all_objects)
