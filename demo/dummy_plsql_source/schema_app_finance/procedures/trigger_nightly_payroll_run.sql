-- Test: Entry point object
CREATE OR REPLACE PROCEDURE trigger_nightly_payroll_run AUTHID DEFINER AS
  CURSOR c_all_employees IS
    SELECT id FROM app_core.employees; -- Placeholder for actual active employees query
BEGIN
  schema_util_common.logger_pkg.log_info('Starting nightly payroll run.');

  FOR emp_rec IN c_all_employees LOOP
    BEGIN
      payroll_pkg.generate_payslip(p_emp_id => emp_rec.id, p_pay_period_end => TRUNC(SYSDATE, 'MM') -1 ); -- Call to package
    EXCEPTION
      WHEN OTHERS THEN
        schema_util_common.logger_pkg.log_error('Failed payroll for emp: ' || emp_rec.id);
    END;
  END LOOP;

  schema_util_common.logger_pkg.log_info('Nightly payroll run completed.');
END trigger_nightly_payroll_run;
/