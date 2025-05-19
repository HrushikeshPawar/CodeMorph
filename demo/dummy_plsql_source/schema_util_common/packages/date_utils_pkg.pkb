CREATE OR REPLACE PACKAGE BODY date_utils_pkg AS

  FUNCTION add_business_days (
    p_start_date IN DATE,
    p_num_days   IN INTEGER
  ) RETURN DATE IS
    v_current_date DATE := p_start_date;
    v_days_added   INTEGER := 0;
    v_direction    INTEGER := 1;
  BEGIN
    IF p_num_days = 0 THEN
      RETURN p_start_date;
    END IF;

    IF p_num_days < 0 THEN
      v_direction := -1;
    END IF;

    WHILE v_days_added < ABS(p_num_days) LOOP -- Test: WHILE LOOP
      v_current_date := v_current_date + v_direction;
      -- Assuming weekends are Sat (7) and Sun (1) for TO_CHAR(date, 'D') in some NLS settings
      -- This is a simplified check.
      IF TO_CHAR(v_current_date, 'DY', 'NLS_DATE_LANGUAGE=ENGLISH') NOT IN ('SAT', 'SUN') THEN -- Test: TO_CHAR call
        v_days_added := v_days_added + 1;
      END IF;
    END LOOP;

    RETURN v_current_date;
  EXCEPTION
    WHEN OTHERS THEN
      logger_pkg.log_error('Error in add_business_days', SQLCODE); -- Test: Call to another util package
      RETURN NULL;
  END add_business_days;

  FUNCTION format_date (
    p_date IN DATE
  ) RETURN VARCHAR2 IS
  BEGIN
    -- Test: Overloaded function calling another version of itself
    RETURN format_date(p_date, 'YYYY-MM-DD');
  END format_date;

  FUNCTION format_date (
    p_date        IN DATE,
    p_format_mask IN VARCHAR2
  ) RETURN VARCHAR2 IS
  BEGIN
    IF p_date IS NULL THEN
      RETURN NULL;
    END IF;
    RETURN TO_CHAR(p_date, p_format_mask);
  END format_date;

END date_utils_pkg;
