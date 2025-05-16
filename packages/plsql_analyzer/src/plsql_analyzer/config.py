# plsql_analyzer/config.py
from pathlib import Path

# Determine the base directory of the project
# This assumes config.py is in plsql_analyzer/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "generated"
BASE_DIR.mkdir(exist_ok=True)

ARTIFACTS_DIR = BASE_DIR / "artifacts"
LOGS_DIR = ARTIFACTS_DIR / "logs" / "plsql_analyzer"
DATABASE_PATH = ARTIFACTS_DIR / "PLSQL_Analysis_Test.db"

# --- User Configurable Settings ---
# Adjust this path to point to the root directory of your PL/SQL source code
# For example: SOURCE_CODE_ROOT_DIR = Path("C:/Users/YourUser/Documents/PLSQL_Sources")
# Or relative: SOURCE_CODE_ROOT_DIR = BASE_DIR.parent / "my_plsql_code_folder",
SOURCE_CODE_ROOT_DIR = BASE_DIR.parent / "data" / "Bulk Download" / "fop_owner" # Example, change this
# SOURCE_CODE_ROOT_DIR = BASE_DIR.parent / "data" / "Bulk Download"


FILE_EXTENSION = "sql" # or "pkg", "pks", "pkb", "prc", "fnc" etc.

# Verbosity level for console logging
# 0 = WARNING, 1 = INFO, 2 = DEBUG, 3 = TRACE
LOG_VERBOSE_LEVEL = 0

# Parts of the file path to exclude when forming the "processed_fpath" for DB records
# This helps in making the stored paths relative or cleaner if code is moved.
# Example: if your files are in /mnt/project_X/sources/moduleA/file.sql
# and SOURCE_CODE_ROOT_DIR points to /mnt/project_X/sources,
# EXCLUDE_FROM_PROCESSED_PATH = [str(BASE_DIR.parent)] might be useful if you move "project_X"
EXCLUDE_FROM_PROCESSED_PATH = ['C:\\',
    'Users',
    'C9B6J9',
    'Projects',
    'CodeMorph',
    'data',
    'Bulk Download',] # Example: Exclude the parent of the source root

# Parts of the file path to exclude when deriving the package name from the file path.
EXCLUDE_FROM_PATH_FOR_PACKAGE_DERIVATION = EXCLUDE_FROM_PROCESSED_PATH + ["PROCEDURES", "PACKAGE_BODIES", "FUNCTIONS"]


# Keywords to drop during call extraction to reduce noise from common PL/SQL constructs
# These are case-insensitive.
CALL_EXTRACTOR_KEYWORDS_TO_DROP = [
    # Aggregate Function:
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "LISTAGG",

    # Analytic Function:
    "ROW_NUMBER",
    "RANK",
    "DENSE_RANK",
    "LAG",
    "LEAD",

    # Command:
    "CREATE",
    "ALTER",
    "DROP",
    "CREATE TABLE",
    "ALTER TABLE",
    "DROP TABLE",
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "COMMIT",
    "ROLLBACK",
    "GRANT",
    "REVOKE",
    "MERGE",
    "FROM",
    "SAVEPOINT",
    "CREATE OR REPLACE PROCEDURE",
    "CREATE OR REPLACE FUNCTION",
    "CREATE OR REPLACE PACKAGE",
    "CREATE OR REPLACE TRIGGER",
    "CREATE OR REPLACE VIEW",
    "CREATE TYPE",

    # Expression:
    "CASE",

    # Function:
    "UPPER",
    "LOWER",
    "SUBSTR",
    "INSTR",
    "LENGTH",
    "REPLACE",
    "TRIM",
    "ROUND",
    "TRUNC",
    "MOD",
    "CEIL",
    "FLOOR",
    "SYSDATE",
    "CURRENT_DATE",
    "ADD_MONTHS",
    "MONTHS_BETWEEN",
    "LAST_DAY",
    "EXTRACT",
    "TO_CHAR",
    "TO_DATE",
    "TO_NUMBER",
    "NVL",
    "NVL2",
    "COALESCE",
    "DECODE",
    "UTL_FILE.FOPEN",
    "DBMS_RANDOM.VALUE",
    "DBMS_RANDOM.STRING",
    "DBMS_METADATA.GET_DDL",
    "SQLCODE",
    "SQLERRM",
    "DBMS_LOB.GETLENGTH",
    "DBMS_LOB.SUBSTR",
    "DBMS_SQL.OPEN_CURSOR",
    "DBMS_SQL.EXECUTE",

    # Procedure:
    "DBMS_OUTPUT.PUT_LINE",
    "DBMS_OUTPUT.ENABLE",
    "UTL_FILE.PUT_LINE",
    "UTL_FILE.GET_LINE",
    "UTL_FILE.FCLOSE",
    "DBMS_LOCK.SLEEP",
    "DBMS_SCHEDULER.CREATE_JOB",
    "DBMS_SCHEDULER.RUN_JOB",
    "RAISE_APPLICATION_ERROR",
    "DBMS_SQL.PARSE",
    "DBMS_SQL.CLOSE_CURSOR",

    # PL/SQL Structure and Control Flow:
    "DECLARE",
    "BEGIN",
    "END",
    "IF",
    "THEN",
    "ELSIF",
    "ELSE",
    "END IF",
    "LOOP",
    "END LOOP",
    "WHILE",
    "FOR",
    "IN",
    "REVERSE",
    "EXIT",
    "CONTINUE",
    "GOTO",
    "RETURN",
    "'NULL'",
    "NULL",
    "AND",
    "OR",

    # PL/SQL Declarations and Types:
    "CONSTANT",
    "DEFAULT",
    "PROCEDURE",
    "FUNCTION",
    "PACKAGE",
    "BODY",
    "TYPE",
    "SUBTYPE",
    "RECORD",
    "TABLE",
    "VARRAY",
    "IS",
    "AS",
    "PRAGMA",
    "VARCHAR2",
    "NVARCHAR2",
    "NUMBER",
    "PLS_INTEGER",
    "BINARY_INTEGER",
    "BINARY_FLOAT",
    "BINARY_DOUBLE",
    "BOOLEAN",
    "DATE",
    "TIMESTAMP",
    "TIMESTAMP WITH TIME ZONE",
    "TIMESTAMP WITH LOCAL TIME ZONE",
    "INTERVAL YEAR TO MONTH",
    "INTERVAL DAY TO SECOND",
    "CLOB",
    "NCLOB",
    "BLOB",
    "BFILE",
    "ROWID",
    "UROWID",
    "CHAR",
    "NCHAR",
    "LONG",
    "RAW",
    "LONG RAW",

    # PL/SQL Cursor Keywords:
    "CURSOR",
    "OPEN",
    "FETCH",
    "CLOSE",
    "BULK COLLECT",
    "FORALL",

    # PL/SQL Exception Handling Keywords:
    "EXCEPTION",
    "WHEN",
    "OTHERS",
    "RAISE",

    # PL/SQL Attributes:
    "'%TYPE'",
    "'%ROWTYPE'",
    "'%FOUND'",
    "'%NOTFOUND'",
    "'%ROWCOUNT'",
    "'%ISOPEN'",
]


# Remove Files
REMOVE_FPATH = ["NCPDP_OWNER\PACKAGE_BODIES\RXC_EDI_DUM_NCPDP_UTIL_PKG.sql"]

# Ensure artifact directories exist
def ensure_artifact_dirs():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
