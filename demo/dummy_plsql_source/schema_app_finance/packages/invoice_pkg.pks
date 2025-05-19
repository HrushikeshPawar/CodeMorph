CREATE OR REPLACE PACKAGE invoice_pkg AS

  PROCEDURE create_invoice_for_project (
    p_project_id IN NUMBER -- Placeholder for APP_CORE.PROJECTS.ID%TYPE
  );

  FUNCTION get_invoice_amount (
    p_invoice_id IN NUMBER -- Placeholder for INVOICES.ID%TYPE
  ) RETURN NUMBER;

  -- Test: Procedure that might call UTL_HTTP or UTL_FILE
  PROCEDURE send_invoice (
    p_invoice_id IN NUMBER
  );

END invoice_pkg;
/