CREATE OR REPLACE PACKAGE string_utils_pkg AS

  FUNCTION to_title_case (
    p_string IN VARCHAR2
  ) RETURN VARCHAR2;

  -- Test: Basic IF/THEN logic for ACC
  FUNCTION safe_substr (
    p_string IN VARCHAR2,
    p_start  IN INTEGER,
    p_length IN INTEGER
  ) RETURN VARCHAR2;

END string_utils_pkg;