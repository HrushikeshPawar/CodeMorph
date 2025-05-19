CREATE OR REPLACE PACKAGE project_pkg AS

  PROCEDURE create_project (
    p_name        IN VARCHAR2,
    p_lead_emp_id IN NUMBER -- Placeholder for EMPLOYEES.ID%TYPE
  );

  -- Test: %ROWTYPE for return
  FUNCTION get_project_details (
    p_project_id IN NUMBER -- Placeholder for PROJECTS.ID%TYPE
  ) RETURN app_core.projects%ROWTYPE; -- Conceptual table

  PROCEDURE assign_employee_to_project (
    p_project_id IN NUMBER,
    p_emp_id     IN NUMBER,
    p_role       IN VARCHAR2
  );

  -- Test: Return type is a collection defined in another package (same schema)
  FUNCTION get_assigned_employees (
    p_project_id IN NUMBER
  ) RETURN employee_pkg.t_employee_id_list;

END project_pkg;
/