CREATE OR REPLACE PACKAGE employee_pkg AUTHID CURRENT_USER AS -- Test: AUTHID

  -- Test: User-defined record type
  TYPE t_employee_rec IS RECORD (
    id         NUMBER, -- Placeholder for EMPLOYEES.ID%TYPE
    name       VARCHAR2(100), -- Placeholder for EMPLOYEES.NAME%TYPE
    salary     NUMBER,
    dept_id    NUMBER
  );

  -- Test: User-defined collection type
  TYPE t_employee_id_list IS TABLE OF NUMBER INDEX BY PLS_INTEGER; -- Placeholder for EMPLOYEES.ID%TYPE

  -- Test: Package-level constant
  g_default_dept_id CONSTANT NUMBER := 10; -- Placeholder for DEPARTMENTS.ID%TYPE

  -- Test: Forward declaration (get_manager_name is defined later in body, used by an internal proc before its full def)
  FUNCTION get_manager_details_internal (p_emp_id IN NUMBER) RETURN t_employee_rec; -- private, calls get_manager_name
  FUNCTION get_manager_name (p_emp_id IN NUMBER) RETURN VARCHAR2;


  PROCEDURE add_employee (
    p_name    IN VARCHAR2,
    p_salary  IN NUMBER,
    p_dept_id IN NUMBER DEFAULT g_default_dept_id -- Test: Using package constant as default
  );

  FUNCTION get_employee (
    p_emp_id IN NUMBER -- Placeholder for EMPLOYEES.ID%TYPE
  ) RETURN t_employee_rec;

  -- Test: Quoted identifier
  PROCEDURE "Update_Employee_Info" (
    p_emp_id     IN NUMBER,
    p_new_salary IN NUMBER
  );

  FUNCTION get_direct_reports (p_manager_id IN NUMBER) RETURN t_employee_id_list;

END employee_pkg;
/