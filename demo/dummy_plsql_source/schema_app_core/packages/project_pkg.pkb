CREATE OR REPLACE PACKAGE BODY project_pkg AS

  PROCEDURE create_project (
    p_name        IN VARCHAR2,
    p_lead_emp_id IN NUMBER
  ) IS
    v_lead_employee employee_pkg.t_employee_rec; -- Test: Using type from another package
  BEGIN
    util_common.logger_pkg.log_info('Creating project: ' || p_name);
    v_lead_employee := employee_pkg.get_employee(p_emp_id => p_lead_emp_id); -- Test: Inter-package call (same schema)

    IF v_lead_employee.id IS NULL THEN
      util_common.logger_pkg.log_error('Invalid lead employee ID: ' || p_lead_emp_id);
      RAISE_APPLICATION_ERROR(-20001, 'Invalid lead employee.'); -- Test: RAISE_APPLICATION_ERROR
    END IF;
    -- Simulate INSERT into PROJECTS table
    NULL;
  END create_project;

  FUNCTION get_project_details (
    p_project_id IN NUMBER
  ) RETURN app_core.projects%ROWTYPE IS
    v_project_rec app_core.projects%ROWTYPE;
  BEGIN
    -- Simulate SELECT * INTO v_project_rec FROM app_core.projects WHERE id = p_project_id;
    IF p_project_id = 100 THEN
        v_project_rec.id := 100; v_project_rec.name := 'CodeMorph Test Project';
        v_project_rec.start_date := SYSDATE; v_project_rec.lead_emp_id := 2;
    END IF;
    RETURN v_project_rec;
  END get_project_details;

  PROCEDURE assign_employee_to_project (
    p_project_id IN NUMBER,
    p_emp_id     IN NUMBER,
    p_role       IN VARCHAR2
  ) IS
    v_emp_exists BOOLEAN;
  BEGIN
    v_emp_exists := (employee_pkg.get_employee(p_emp_id).id IS NOT NULL);
    IF NOT v_emp_exists THEN
      RAISE_APPLICATION_ERROR(-20002, 'Employee not found for assignment.');
    END IF;
    -- Simulate INSERT into PROJECT_ASSIGNMENTS
    util_common.logger_pkg.log_debug('Assigned '||p_emp_id||' to project '||p_project_id||' as '||p_role);
  END assign_employee_to_project;

  FUNCTION get_assigned_employees (
    p_project_id IN NUMBER
  ) RETURN employee_pkg.t_employee_id_list IS
    v_emp_list employee_pkg.t_employee_id_list;
  BEGIN
    -- Simulate querying PROJECT_ASSIGNMENTS
    IF p_project_id = 100 THEN
        v_emp_list(1) := 1; -- John Doe
    END IF;
    RETURN v_emp_list;
  END get_assigned_employees;

END project_pkg;
/