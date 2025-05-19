CREATE OR REPLACE PACKAGE logger_pkg AS

  -- Test: User-defined type for package variable
  SUBTYPE t_log_level IS PLS_INTEGER RANGE 0..4; -- 0=Off, 1=Error, 2=Warn, 3=Info, 4=Debug

  -- Test: Package-level variable
  g_current_log_level t_log_level := 3; -- Default to INFO

  PROCEDURE log_message (
    p_level   IN t_log_level,
    p_message IN VARCHAR2
  );

  PROCEDURE log_debug (
    p_message IN VARCHAR2
  );

  -- Test: Default parameter value (SQLCODE)
  PROCEDURE log_error (
    p_message    IN VARCHAR2,
    p_error_code IN INTEGER DEFAULT SQLCODE -- Test: Using SQLCODE as default
  );

END logger_pkg;
