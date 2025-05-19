CREATE OR REPLACE PACKAGE BODY employee_pkg AS

  -- Private procedure defined before its caller (get_manager_details_internal)
  -- This is to ensure forward declared get_manager_name is called before its full definition appears
  FUNCTION get_employee_raw_data (p_emp_id IN NUMBER) RETURN t_employee_rec IS
    v_rec t_employee_rec;
  BEGIN
    -- Simulate DB fetch
    IF p_emp_id = 1 THEN
      v_rec.id := 1; v_rec.name := 'John Doe'; v_rec.salary := 50000; v_rec.dept_id := 10;
    ELSIF p_emp_id = 2 THEN
      v_rec.id := 2; v_rec.name := 'Jane Smith (Manager)'; v_rec.salary := 70000; v_rec.dept_id := 10;
    ELSE
      v_rec.id := p_emp_id; v_rec.name := 'Unknown'; v_rec.salary := 0; v_rec.dept_id := g_default_dept_id;
    END IF;
    RETURN v_rec;
  END get_employee_raw_data;


  -- Test: Forward Declaration - get_manager_name is used here by get_manager_details_internal
  -- but its full definition is later in this package body.
  FUNCTION get_manager_details_internal (p_emp_id IN NUMBER) RETURN t_employee_rec IS
    v_emp_rec t_employee_rec;
    v_manager_name VARCHAR2(100);
    v_manager_id NUMBER; -- Assume logic to find manager_id
  BEGIN
    util_common.logger_pkg.log_debug('Fetching internal manager details for emp: ' || p_emp_id);
    -- Simulate getting manager_id
    IF p_emp_id = 1 THEN v_manager_id := 2; END IF;

    IF v_manager_id IS NOT NULL THEN
      v_manager_name := get_manager_name(p_emp_id => v_manager_id); -- Call to forward-declared function
      v_emp_rec := get_employee_raw_data(v_manager_id); -- Call a helper
      v_emp_rec.name := v_manager_name || ' (Manager of ' || p_emp_id || ')';
    ELSE
      v_emp_rec.name := 'No Manager';
    END IF;
    RETURN v_emp_rec;
  END get_manager_details_internal;


  PROCEDURE add_employee (
    p_name    IN VARCHAR2,
    p_salary  IN NUMBER,
    p_dept_id IN NUMBER DEFAULT g_default_dept_id
  ) IS
    v_new_emp_id NUMBER;
    PRAGMA AUTONOMOUS_TRANSACTION; -- Test: PRAGMA
  BEGIN
    util_common.logger_pkg.log_debug('Adding employee: ' || p_name); -- Test: Call to utility package from different schema

    -- Simulate sequence usage
    -- SELECT app_core.employee_id_seq.NEXTVAL INTO v_new_emp_id FROM DUAL; (Conceptual)
    v_new_emp_id := NVL(p_dept_id,0) * 1000 + FLOOR(DBMS_RANDOM.VALUE(1,999)); -- Test: NVL, FLOOR, DBMS_RANDOM.VALUE calls

    -- Simulate INSERT
    -- INSERT INTO app_core.employees (id, name, salary, department_id)
    -- VALUES (v_new_emp_id, p_name, p_salary, p_dept_id);
    util_common.logger_pkg.log_message(p_level => 3, p_message => 'Employee ' || p_name || ' added with ID: ' || v_new_emp_id);

    COMMIT;
  EXCEPTION
    WHEN OTHERS THEN
      util_common.logger_pkg.log_error('Failed to add employee: ' || p_name);
      ROLLBACK;
  END add_employee;

  FUNCTION get_employee (
    p_emp_id IN NUMBER
  ) RETURN t_employee_rec IS
  BEGIN
    util_common.logger_pkg.log_debug('Fetching employee: ' || p_emp_id);
    -- Simulate fetching from DB and populating t_employee_rec
    RETURN get_employee_raw_data(p_emp_id);
  END get_employee;

  PROCEDURE "Update_Employee_Info" ( -- Test: Quoted Identifier in Body
    p_emp_id     IN NUMBER,
    p_new_salary IN NUMBER
  ) IS
  BEGIN
    -- Simulate UPDATE
    -- UPDATE app_core.employees SET salary = p_new_salary WHERE id = p_emp_id;
    util_common.logger_pkg.log_info('Updated salary for employee: ' || p_emp_id);
  END "Update_Employee_Info";

  -- Full definition of forward-declared function
  FUNCTION get_manager_name (p_emp_id IN NUMBER) RETURN VARCHAR2 IS
    v_manager_rec t_employee_rec;
    v_manager_id NUMBER; -- Placeholder logic
  BEGIN
    -- This is a simplified conceptual recursion / hierarchical lookup
    -- In a real scenario, this would query where employees.manager_id = p_emp_id for some relationship
    -- For testing forward declaration, its mere presence and prior use is key.
    -- Simulate finding a manager ID
    IF p_emp_id = 1 THEN v_manager_id := 2; -- John Doe's manager is Jane Smith
    ELSIF p_emp_id = 2 THEN v_manager_id := NULL; -- Jane Smith has no manager (top level)
    ELSE v_manager_id := NULL;
    END IF;

    IF v_manager_id IS NOT NULL THEN
       v_manager_rec := get_employee_raw_data(v_manager_id);
       RETURN v_manager_rec.name;
    ELSE
       RETURN 'N/A - Top Level or No Manager';
    END IF;
  END get_manager_name;

  FUNCTION get_direct_reports (p_manager_id IN NUMBER) RETURN t_employee_id_list IS
    v_report_list t_employee_id_list;
    v_idx PLS_INTEGER := 0;
  BEGIN
    -- Simulate cursor loop
    -- FOR rec IN (SELECT id FROM app_core.employees WHERE manager_id = p_manager_id) LOOP -- Test: FOR LOOP with SELECT
    --   v_idx := v_idx + 1;
    --   v_report_list(v_idx) := rec.id;
    -- END LOOP;
    IF p_manager_id = 2 THEN -- Jane Smith is manager
        v_idx := v_idx + 1; v_report_list(v_idx) := 1; -- John Doe reports to Jane
    END IF;
    RETURN v_report_list;
  END get_direct_reports;

END employee_pkg;
/