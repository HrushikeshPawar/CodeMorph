# tests/utils/test_file_helpers.py
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open # For mocking file operations
from plsql_analyzer.utils.file_helpers import FileHelpers

class TestFileHelpers:

    @pytest.fixture
    def file_helpers_instance(self, test_logger) -> FileHelpers:
        return FileHelpers(logger=test_logger)

    def test_escape_angle_brackets(self, file_helpers_instance):
        assert file_helpers_instance.escape_angle_brackets("<a><b>") == "\\<a\\>\\<b\\>"
        assert file_helpers_instance.escape_angle_brackets("no brackets") == "no brackets"

    @patch("pathlib.Path.is_file")
    @patch("builtins.open", new_callable=mock_open, read_data=b"file content for hash")
    def test_compute_file_hash_success(self, mock_file_open, mock_is_file, file_helpers_instance, tmp_path):
        mock_is_file.return_value = True
        test_file = tmp_path / "test.sql" # Path object needed
        
        # Expected sha256 hash for "file content for hash"
        expected_hash = "cdd92c6671dfba1a5e8f34378babe91032332959179f750a5f20c10a04679821"
        
        actual_hash = file_helpers_instance.compute_file_hash(test_file)
        assert actual_hash == expected_hash
        mock_file_open.assert_called_once_with(test_file, 'rb')

    @patch("pathlib.Path.is_file")
    def test_compute_file_hash_file_not_found(self, mock_is_file, file_helpers_instance, tmp_path):
        mock_is_file.return_value = False # Simulate file not existing
        test_file = tmp_path / "non_existent.sql"
        assert file_helpers_instance.compute_file_hash(test_file) is None

    def test_compute_file_hash_invalid_algorithm(self, file_helpers_instance, tmp_path):
        # This test needs a file that actually exists to get past the is_file check,
        # or we mock is_file to True. Let's create a dummy file.
        test_file = tmp_path / "dummy.txt"
        test_file.write_text("content")
        assert file_helpers_instance.compute_file_hash(test_file, algorithm="invalid_algo") is None

    # Tests for get_processed_fpath_str
    # These depend on Path.resolve() and Path.is_relative_to() which behave differently across OS
    # For robust tests, one might need to mock Path objects more heavily or test on specific OS.
    # Let's try with some common scenarios.

    @pytest.mark.parametrize("fpath_str, exclusions, expected_str_posix", [
        ("project/src/module/file.sql", ["project", "src"], "module/file.sql"),
        ("project/src/module/file.sql", ["project"], "src/module/file.sql"),
        ("C:\\project\\src\\module\\file.sql", ["C:", "project", "src"], "module/file.sql"),
        ("data/file.sql", ["unrelated"], "data/file.sql"), # No common base in exclusions
        ("project/file.sql", ["project", "src"], "file.sql") # Exclusion is deeper
    ])
    def test_get_processed_fpath(self, file_helpers_instance, fpath_str, exclusions, expected_str_posix):
        # Actual call
        fpath = Path(*fpath_str.split('\\')) if "\\" in fpath_str else Path(*fpath_str.split('/'))
        result = file_helpers_instance.get_processed_fpath(fpath, exclusions)
        assert result == Path(expected_str_posix)


    # Tests for derive_package_name_from_path
    @pytest.mark.parametrize("pkg_from_code, fpath_str, file_ext, exclude_from_pkg_derivation, expected_pkg_name", [
        (None, "project/src/moduleA/sub_mod_b/file.sql", ["sql"], ["project", "src"], "modulea.sub_mod_b.file"),
        ("modulea.sub_mod_b", "project/src/moduleA/sub_mod_b/file.sql", ["sql"], ["project", "src"], "modulea.sub_mod_b.file"),
        ("A.B", "project/src/moduleA/sub_mod_b/file.sql", ["sql"], ["project", "src"], "a.b.modulea.sub_mod_b.file"), # Such a case won't happen in real life, but let's test it
        ("core_pkg", "project/src/core_pkg/file.sql", ["sql"], ["project", "src"], "core_pkg.file"),
        (None, "project/src/file.sql", ["sql"], ["project", "src"], "file"), # No path parts left
        ("mypkg", "file.sql", ["sql"], [], "mypkg.file"), # No path parts, only code
        (None, "project/sources/PKG_OWNER/OBJECT_NAME.sql", ["sql"], ["project", "sources"], "pkg_owner.object_name"),
        ("EXISTING", "project/module/file.sql", ["sql"], ["project", "module", "file"], "existing"),
    ])
    def test_derive_package_name_from_path(self, file_helpers_instance, pkg_from_code, fpath_str, file_ext, exclude_from_pkg_derivation, expected_pkg_name, mocker):
        # We need to mock Path behavior for parts and parent traversal
        mock_fpath = Path(*fpath_str.split('/')) # Use actual Path to test its traversal logic as much as possible

        # Mocking Path constructor for the entire test if needed, or just parts used by function.
        # The function itself uses fpath.parent, current_dir.name, current_dir != current_dir.parent
        # These are standard Path attributes and should work if Path(fpath_str) is a valid Path object.

        result = file_helpers_instance.derive_package_name_from_path(
            pkg_from_code, mock_fpath, file_ext, exclude_from_pkg_derivation
        )
        assert result == expected_pkg_name