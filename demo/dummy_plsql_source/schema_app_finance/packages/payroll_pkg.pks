CREATE OR REPLACE PACKAGE payroll_pkg AS

  PROCEDURE process_employee_payroll (
    p_emp_id IN NUMBER -- Placeholder for APP_CORE.EMPLOYEES.ID%TYPE
  );

  -- Test: Overloading
  FUNCTION calculate_tax (
    p_salary IN NUMBER
  ) RETURN NUMBER;

  FUNCTION calculate_tax (
    p_salary      IN NUMBER,
    p_region_code IN VARCHAR2
  ) RETURN NUMBER;

  PROCEDURE generate_payslip (
    p_emp_id         IN NUMBER,
    p_pay_period_end IN DATE
  );

END payroll_pkg;
/