from pathlib import Path
from typing import List, Any
from pydantic import BaseModel, Field, field_validator
import os

class AppConfig(BaseModel):
    """
    Centralized application configuration using Pydantic for type safety and validation.
    """
    # Core configuration fields
    source_code_root_dir: Path = Field(..., description="Root directory containing source code to analyze.")
    output_base_dir: Path = Field(
        default=Path("generated/artifacts").resolve(),
        description="Base directory for all generated artifacts, logs, and outputs."
    )

    log_verbose_level: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Verbosity level for logging (0=ERROR, 1=INFO, 2=DEBUG, 3=TRACE)."
    )

    database_filename: str = Field(
        default="PLSQL_CodeObjects.db",
        description="Filename for the SQLite database storing analysis results."
    )

    file_extensions_to_include: List[str] = Field(
        default_factory=lambda: ["sql"],
        description="Glob patterns for files to include in analysis."
    )

    exclude_names_from_processed_path: List[str] = Field(
        default_factory=lambda: [],
        description="Directory names to exclude from analysis."
    )

    # Parts of the file path to exclude when deriving the package name from the file path.
    exclude_names_for_package_derivation: List[str] = Field(
        default_factory=lambda: ["PROCEDURES", "PACKAGE_BODIES", "FUNCTIONS"],
        description="Directory names to exclude from package name derivation."
    )

    enable_profiler: bool = Field(
        default=False,
        description="Enable or disable profiling during analysis."
    )
    
    force_reprocess: set[str] = Field(
        default_factory=set,
        description="List of file paths to force reprocess, bypassing hash checks."
    )
    
    clear_history_for_file: set[str] = Field(
        default_factory=set,
        description="List of processed file paths to clear history for from the database."
    )

    call_extractor_keywords_to_drop: List[str] = Field(
        default_factory=lambda: CALL_EXTRACTOR_KEYWORDS_TO_DROP,
        description="List of keywords to drop during call extraction."
    )

    @property
    def artifacts_dir(self) -> Path:
        return self.output_base_dir

    @property
    def logs_dir(self) -> Path:
        return self.output_base_dir / "logs" / "plsql_analyzer"

    @property
    def database_path(self) -> Path:
        return self.output_base_dir / self.database_filename

    def ensure_artifact_dirs(self) -> None:
        """Create necessary output directories if they do not exist."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @field_validator('source_code_root_dir', 'output_base_dir', mode='before')
    @classmethod
    def expand_and_resolve_path(cls, v: Any) -> Path:
        if not isinstance(v, (str, Path)):
            # Return 'v' to let Pydantic attempt its standard parsing and validation for non-str/Path types.
            # This will likely lead to a more informative ValidationError if 'v' is unsuitable for a Path field.
            return v

        path_str = str(v)  # Ensure 'v' is a string for os.path functions
        
        expanded_path_str = os.path.expanduser(path_str)
        expanded_path_str = os.path.expandvars(expanded_path_str)
        
        return Path(expanded_path_str).resolve()

#  Keywords to drop during call extraction to reduce noise from common PL/SQL constructs
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