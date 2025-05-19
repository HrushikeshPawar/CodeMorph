-- Test: Orphaned object
CREATE OR REPLACE PROCEDURE old_unused_procedure AS
BEGIN
  NULL; -- Does nothing, not called by anything
END old_unused_procedure;
/