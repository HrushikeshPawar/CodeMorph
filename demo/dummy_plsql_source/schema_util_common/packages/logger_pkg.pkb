CREATE OR REPLACE PACKAGE BODY logger_pkg AS

  PROCEDURE log_message (
    p_level   IN t_log_level,
    p_message IN VARCHAR2
  ) IS
  BEGIN
    IF p_level <= g_current_log_level THEN
      -- In a real scenario, this would write to a table or use DBMS_OUTPUT
      -- For testing, we'll just ensure the call structure is parsed.
      DBMS_OUTPUT.PUT_LINE(TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD HH24:MI:SS.FF TZR') || ' [' || p_level || ']: ' || p_message); -- Test: DBMS_OUTPUT call, TO_CHAR
    END IF;
  EXCEPTION
    WHEN OTHERS THEN -- Test: Basic exception handling
      NULL; -- Suppress errors in logging itself
  END log_message;

  PROCEDURE log_debug (
    p_message IN VARCHAR2
  ) IS
  BEGIN
    -- Test: Internal package call
    log_message(p_level => 4, p_message => p_message);
  END log_debug;

  PROCEDURE log_error (
    p_message    IN VARCHAR2,
    p_error_code IN INTEGER DEFAULT SQLCODE
  ) IS
    v_full_message VARCHAR2(4000);
  BEGIN
    v_full_message := 'ERROR (' || p_error_code || '): ' || p_message;
    log_message(p_level => 1, p_message => v_full_message);
  END log_error;

END logger_pkg;
