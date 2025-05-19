CREATE OR REPLACE PACKAGE date_utils_pkg AS

  -- Test: More complex logic for ACC (loops, date checks)
  FUNCTION add_business_days (
    p_start_date IN DATE,
    p_num_days   IN INTEGER
  ) RETURN DATE;

  -- Test: Overloading
  FUNCTION format_date (
    p_date IN DATE
  ) RETURN VARCHAR2;

  FUNCTION format_date (
    p_date        IN DATE,
    p_format_mask IN VARCHAR2
  ) RETURN VARCHAR2;

  PRAGMA RESTRICT_REFERENCES(format_date, WNDS, WNPS, RNDS, RNPS); -- Test: PRAGMA

END date_utils_pkg;
