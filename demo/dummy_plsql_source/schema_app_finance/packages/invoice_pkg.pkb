CREATE OR REPLACE PACKAGE BODY invoice_pkg AS

  PROCEDURE create_invoice_for_project (
    p_project_id IN NUMBER
  ) IS
    v_project_details app_core.projects%ROWTYPE; -- Test: Inter-schema %ROWTYPE usage
    v_invoice_id NUMBER;
  BEGIN
    v_project_details := app_core.project_pkg.get_project_details(p_project_id => p_project_id); -- Test: Call to another schema's package

    IF v_project_details.id IS NULL THEN
      util_common.logger_pkg.log_error('Project not found for invoicing: ' || p_project_id);
      RETURN;
    END IF;

    -- Simulate sequence
    -- SELECT app_finance.invoice_id_seq.NEXTVAL INTO v_invoice_id FROM DUAL;
    v_invoice_id := p_project_id * 10; -- Dummy ID generation

    -- Simulate INSERT into INVOICES
    util_common.logger_pkg.log_message(3, 'Invoice ' || v_invoice_id || ' created for project ' || v_project_details.name);
  END create_invoice_for_project;

  FUNCTION get_invoice_amount (
    p_invoice_id IN NUMBER
  ) RETURN NUMBER IS
  BEGIN
    -- Simulate SELECT amount FROM app_finance.invoices WHERE id = p_invoice_id;
    RETURN p_invoice_id * 100.50; -- Dummy amount
  END get_invoice_amount;

  PROCEDURE send_invoice (
    p_invoice_id IN NUMBER
  ) IS
    v_request UTL_HTTP.REQ; -- Test: UTL_HTTP type usage (placeholder)
    v_response UTL_HTTP.RESP;
    v_file UTL_FILE.FILE_TYPE; -- Test: UTL_FILE type usage
    v_url VARCHAR2(2000) := 'http://example.com/api/invoice';
  BEGIN
    util_common.logger_pkg.log_debug('Attempting to send invoice: ' || p_invoice_id);
    -- Simulate calls to UTL packages
    -- v_request := UTL_HTTP.BEGIN_REQUEST(url => v_url, method => 'POST');
    -- UTL_HTTP.SET_HEADER(r => v_request, name => 'Content-Type', value => 'application/json');
    -- ... write body ...
    -- v_response := UTL_HTTP.GET_RESPONSE(r => v_request);
    -- UTL_HTTP.END_RESPONSE(resp => v_response);

    -- v_file := UTL_FILE.FOPEN(location => 'INVOICE_DIR', filename => 'inv_'||p_invoice_id||'.txt', open_mode => 'w');
    -- UTL_FILE.PUT_LINE(file => v_file, buffer => 'Invoice content for ID: ' || p_invoice_id);
    -- UTL_FILE.FCLOSE(v_file);

    -- For parser, actual calls would be:
    IF p_invoice_id > 0 THEN
        dummy_utl_http_call(v_url); -- Simulate a call
        dummy_utl_file_write('inv_'||p_invoice_id||'.txt'); -- Simulate another
    END IF;
    util_common.logger_pkg.log_info('Invoice ' || p_invoice_id || ' marked as sent.');
  EXCEPTION
    WHEN OTHERS THEN
       util_common.logger_pkg.log_error('Failed to send invoice: ' || p_invoice_id);
       -- IF UTL_HTTP.GET_DETAILED_SQLERRM IS NOT NULL THEN ...
       -- (Conceptual - this function doesn't exist, but checking for call like syntax)
       -- get_detailed_error_info(UTL_HTTP.GET_DETAILED_SQLERRM);
  END send_invoice;

  -- Dummy procedures to be detected by call extractor if not in keywords_to_drop
  PROCEDURE dummy_utl_http_call (p_url VARCHAR2) IS BEGIN NULL; END;
  PROCEDURE dummy_utl_file_write (p_fname VARCHAR2) IS BEGIN NULL; END;


END invoice_pkg;
/