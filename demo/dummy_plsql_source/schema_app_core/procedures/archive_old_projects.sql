CREATE OR REPLACE PROCEDURE archive_old_projects (
  p_cutoff_date IN DATE
) AUTHID DEFINER AS -- Test: AUTHID
  CURSOR c_old_projects IS -- Test: Explicit Cursor Declaration
    SELECT id, name FROM app_core.projects WHERE end_date < p_cutoff_date;
  v_project_rec c_old_projects%ROWTYPE; -- Test: Cursor %ROWTYPE
BEGIN
  util_common.logger_pkg.log_info('Archiving projects older than: ' || util_common.date_utils_pkg.format_date(p_cutoff_date)); -- Test: Call to schema.pkg.func

  OPEN c_old_projects; -- Test: OPEN cursor
  LOOP
    FETCH c_old_projects INTO v_project_rec; -- Test: FETCH cursor
    EXIT WHEN c_old_projects%NOTFOUND; -- Test: Cursor attribute %NOTFOUND

    util_common.logger_pkg.log_debug('Archiving project: ' || v_project_rec.name);
    -- Simulate archive logic
    -- project_pkg.archive_project_data(v_project_rec.id); -- Conceptual call to a non-existent proc for dep graph
  END LOOP;
  CLOSE c_old_projects; -- Test: CLOSE cursor
EXCEPTION
  WHEN OTHERS THEN
    util_common.logger_pkg.log_error('Error archiving projects.');
END archive_old_projects;
/