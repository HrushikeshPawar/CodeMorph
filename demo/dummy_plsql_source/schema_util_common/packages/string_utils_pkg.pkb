CREATE OR REPLACE PACKAGE BODY string_utils_pkg AS

  FUNCTION to_title_case (
    p_string IN VARCHAR2
  ) RETURN VARCHAR2 IS
    v_result VARCHAR2(32767);
  BEGIN
    -- Simplified title case for testing structure
    IF p_string IS NULL THEN
      RETURN NULL;
    END IF;
    v_result := UPPER(SUBSTR(p_string, 1, 1)) || LOWER(SUBSTR(p_string, 2)); -- Test: UPPER, SUBSTR, LOWER calls
    RETURN v_result;
  END to_title_case;

  FUNCTION safe_substr (
    p_string IN VARCHAR2,
    p_start  IN INTEGER,
    p_length IN INTEGER
  ) RETURN VARCHAR2 IS
  BEGIN
    IF p_string IS NULL OR p_start IS NULL OR p_length IS NULL OR p_length <= 0 OR p_start <= 0 THEN
      RETURN NULL;
    END IF;
    IF p_start > LENGTH(p_string) THEN -- Test: LENGTH call
      RETURN NULL;
    END IF;
    RETURN SUBSTR(p_string, p_start, p_length);
  EXCEPTION
    WHEN OTHERS THEN
      RETURN NULL;
  END safe_substr;

END string_utils_pkg;
