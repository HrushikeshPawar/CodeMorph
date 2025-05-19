CREATE OR REPLACE FUNCTION is_employee_active (
  p_emp_id IN NUMBER -- Placeholder for EMPLOYEES.ID%TYPE
) RETURN BOOLEAN IS
  v_hire_date DATE;
BEGIN
  -- Simulate fetching hire_date
  -- SELECT hire_date INTO v_hire_date FROM app_core.employees WHERE id = p_emp_id;
  IF p_emp_id = 1 THEN v_hire_date := SYSDATE - 100; END IF;

  IF v_hire_date IS NOT NULL AND v_hire_date <= SYSDATE THEN
    RETURN TRUE;
  ELSE
    RETURN FALSE;
  END IF;
END is_employee_active;
/