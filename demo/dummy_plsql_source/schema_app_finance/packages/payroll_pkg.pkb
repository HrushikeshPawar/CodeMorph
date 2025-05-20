CREATE OR REPLACE PACKAGE BODY payroll_pkg AS

  PROCEDURE process_employee_payroll (
    p_emp_id IN NUMBER
  ) IS
    v_emp_rec schema_app_core.employee_pkg.t_employee_rec; -- Test: Inter-schema package type usage
    v_formatted_date VARCHAR2(50);
    v_net_pay NUMBER;
    v_tax_amount NUMBER;
  BEGIN
    schema_util_common.logger_pkg.log_debug('Processing payroll for employee: ' || p_emp_id);
    v_emp_rec := schema_app_core.employee_pkg.get_employee(p_emp_id => p_emp_id); -- Test: Inter-schema package call

    IF v_emp_rec.id IS NULL THEN
      schema_util_common.logger_pkg.log_error('Employee not found for payroll: ' || p_emp_id);
      RETURN;
    END IF;

    v_formatted_date := schema_util_common.date_utils_pkg.format_date(SYSDATE, 'DD-MON-YYYY HH24:MI'); -- Test: Inter-schema utility call

    -- Test: More complex logic for ACC
    CASE -- Test: CASE statement
      WHEN v_emp_rec.salary < 30000 THEN
        v_tax_amount := calculate_tax(p_salary => v_emp_rec.salary); -- Call to overloaded function
      WHEN v_emp_rec.salary < 60000 THEN
        v_tax_amount := calculate_tax(p_salary => v_emp_rec.salary, p_region_code => 'STATE_A'); -- Call to specific overload
      ELSE
        IF v_emp_rec.dept_id = schema_app_core.employee_pkg.g_default_dept_id THEN -- Test: Use constant from other schema.pkg
            v_tax_amount := calculate_tax(p_salary => v_emp_rec.salary, p_region_code => 'HIGH_EARNER_DEFAULT_DEPT');
        ELSE
            v_tax_amount := calculate_tax(p_salary => v_emp_rec.salary, p_region_code => 'HIGH_EARNER_OTHER_DEPT');
        END IF;
    END CASE;

    v_net_pay := v_emp_rec.salary - v_tax_amount;
    schema_util_common.logger_pkg.log_info('Payroll for ' || v_emp_rec.name || ' processed on ' || v_formatted_date || '. Net: ' || v_net_pay);

    -- Simulate dynamic SQL
    -- EXECUTE IMMEDIATE 'INSERT INTO audit_log (msg) VALUES (:msg)' USING 'Payroll processed for ' || p_emp_id;
    -- Test: Call to DBMS_SQL or similar (if used directly)
    DECLARE
        v_cursor INTEGER;
        v_rows_processed INTEGER;
    BEGIN
        v_cursor := DBMS_SQL.OPEN_CURSOR; -- Test: DBMS_SQL call
        DBMS_SQL.PARSE(v_cursor, 'BEGIN NULL; END;', DBMS_SQL.NATIVE);
        v_rows_processed := DBMS_SQL.EXECUTE(v_cursor);
        DBMS_SQL.CLOSE_CURSOR(v_cursor);
    EXCEPTION WHEN OTHERS THEN DBMS_SQL.CLOSE_CURSOR(v_cursor); RAISE;
    END;

  END process_employee_payroll;

  FUNCTION calculate_tax (
    p_salary IN NUMBER
  ) RETURN NUMBER IS
  BEGIN
    -- Default region tax calculation
    RETURN p_salary * 0.10; -- Basic 10% tax
  END calculate_tax;

  FUNCTION calculate_tax (
    p_salary      IN NUMBER,
    p_region_code IN VARCHAR2
  ) RETURN NUMBER IS
    v_processed_region VARCHAR2(100);
    v_rate NUMBER := 0.10; -- default rate
  BEGIN
    v_processed_region := schema_util_common.string_utils_pkg.to_title_case(p_region_code); -- Test: Call utility

    IF v_processed_region = 'State_A' THEN
      v_rate := 0.12;
    ELSIF v_processed_region LIKE 'High_Earner%' THEN
      v_rate := 0.25;
    END IF;

    RETURN p_salary * v_rate;
  END calculate_tax;

  PROCEDURE generate_payslip (
    p_emp_id         IN NUMBER,
    p_pay_period_end IN DATE
  ) IS
  BEGIN
    process_employee_payroll(p_emp_id => p_emp_id); -- Test: Internal call
    -- Simulate INSERT into PAYSLIPS
    -- SELECT app_finance.payslip_id_seq.NEXTVAL ... (Conceptual)

    SYS.DBMS_OUTPUT.PUT_LINE('Payslip generated for employee ' || p_emp_id); -- Test: Call to SYS package
    schema_util_common.logger_pkg.log_info('Payslip generated for: ' || p_emp_id || ' for period ending ' || schema_util_common.date_utils_pkg.format_date(p_pay_period_end));
  END generate_payslip;

END payroll_pkg;
/