# tests/parsing/test_signature_parser.py
from __future__ import annotations
import loguru as lg
import pytest
from plsql_analyzer.orchestration.extraction_workflow import clean_code_and_map_literals
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser

class TestPLSQLSignatureParser:

    @pytest.fixture
    def parser(self, test_logger: lg.Logger) -> PLSQLSignatureParser:
        return PLSQLSignatureParser(logger=test_logger)

    def test_simple_procedure_no_params(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE do_something IS"
        result = parser.parse(sig)
        assert result is not None
        assert result["proc_name"] == "do_something"
        assert result["params"] == []

    def test_procedure_with_in_param(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE process_data (p_id IN NUMBER) AS"
        result = parser.parse(sig)
        assert result["proc_name"] == "process_data"
        assert len(result["params"]) == 1
        param = result["params"][0]
        assert param["name"] == "p_id"
        assert param["mode"] == "IN"
        assert param["type"] == "NUMBER"
        assert param["default_value"] is None

    def test_procedure_with_multiple_params_modes_default(self, parser: PLSQLSignatureParser):
        sig = """
        PROCEDURE complex_proc (
            p_input    IN     VARCHAR2,
            p_output   OUT    NUMBER,
            p_in_out   IN OUT DATE,
            p_optional IN     BOOLEAN DEFAULT TRUE,
            p_nocopy   IN OUT NOCOPY my_pkg.my_record_type%ROWTYPE
        ) IS
        """
        result = parser.parse(sig)
        assert result["proc_name"] == "complex_proc"
        assert len(result["params"]) == 5
        
        p1 = result["params"][0]
        assert p1["name"] == "p_input" and p1["mode"] == "IN" and p1["type"] == "VARCHAR2"

        p2 = result["params"][1]
        assert p2["name"] == "p_output" and p2["mode"] == "OUT" and p2["type"] == "NUMBER"

        p3 = result["params"][2]
        assert p3["name"] == "p_in_out" and p3["mode"] == "IN OUT" and p3["type"] == "DATE"

        p4 = result["params"][3]
        assert p4["name"] == "p_optional" and p4["mode"] == "IN" and p4["type"] == "BOOLEAN" and p4["default_value"] == "TRUE"
        
        p5 = result["params"][4]
        assert p5["name"] == "p_nocopy" and p5["mode"] == "IN OUT" and p5["type"] == "my_pkg.my_record_type%ROWTYPE"
        # assert p5["has_nocopy"] is True - KEY DROPPED


    def test_simple_function(self, parser: PLSQLSignatureParser):
        sig = "FUNCTION get_name (p_user_id IN NUMBER) RETURN VARCHAR2 IS"
        result = parser.parse(sig)
        assert result["func_name"] == "get_name"
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "p_user_id"
        assert result["return_type"] == "VARCHAR2"

    def test_function_no_params(self, parser: PLSQLSignatureParser):
        sig = "FUNCTION get_sysdate RETURN DATE AS"
        result = parser.parse(sig)
        assert result["func_name"] == "get_sysdate"
        assert result["params"] == []
        assert result["return_type"] == "DATE"

    def test_create_or_replace_procedure(self, parser: PLSQLSignatureParser):
        sig = "CREATE OR REPLACE EDITIONABLE PROCEDURE schema_name.my_proc (param1 IN VARCHAR2(100 CHAR)) IS"
        result = parser.parse(sig)
        assert result["proc_name"] == "schema_name.my_proc"
        assert len(result["params"]) == 1
        param = result["params"][0]
        assert param["name"] == "param1"
        assert param["type"] == "VARCHAR2(100 CHAR)" # originalTextFor captures the full type string

    def test_type_with_percent_type(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE use_rowtype (p_emp_rec IN employees%ROWTYPE) IS"
        result = parser.parse(sig)
        assert result["params"][0]["type"] == "employees%ROWTYPE"

    def test_quoted_identifiers(self, parser: PLSQLSignatureParser):
        sig = 'FUNCTION "My Function" ("P_ID" IN "My Schema"."My Type") RETURN "BOOLEAN" IS'
        result = parser.parse(sig)
        assert result["func_name"] == '"My Function"'
        assert len(result["params"]) == 1
        param = result["params"][0]
        assert param["name"] == '"P_ID"'
        assert param["type"] == '"My Schema"."My Type"' # Qualified and quoted type
        assert result["return_type"] == '"BOOLEAN"'

    def test_param_default_with_function_call(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE log_message (p_msg IN VARCHAR2, p_ts IN TIMESTAMP DEFAULT SYSTIMESTAMP) IS"
        result = parser.parse(sig)
        param_ts = result["params"][1]
        assert param_ts["default_value"] == "SYSTIMESTAMP"

    def test_param_default_with_string_literal(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE greet (p_name IN VARCHAR2 := 'Guest') IS" # Using := for default
        result = parser.parse(sig)
        name = result["params"][0]
        assert name["default_value"] == "'Guest'"


    def test_empty_signature_string(self, parser: PLSQLSignatureParser):
        assert parser.parse("") is None
        assert parser.parse("   \n\t  ") is None

    def test_invalid_signature_string(self, parser: PLSQLSignatureParser):
        # This is not a valid start of a signature recognizable by the parser
        assert parser.parse("SELECT * FROM DUAL;") is None 
        assert parser.parse("BEGIN DBMS_OUTPUT.PUT_LINE('Hello'); END;") is None

    def test_signature_with_trailing_semicolon(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE proc_with_semi (p_val IN NUMBER) IS;" # Standalone signature
        result = parser.parse(sig)
        assert result is not None
        assert result["proc_name"] == "proc_with_semi"
        assert len(result["params"]) == 1

    def test_type_with_spaces_and_parentheses(self, parser: PLSQLSignatureParser):
        sig = "PROCEDURE test_type (p_data IN VARCHAR2 (2000 BYTE)) IS"
        result = parser.parse(sig)
        assert result is not None
        assert result["params"][0]["type"] == "VARCHAR2 (2000 BYTE)"

    def test_complex_type_from_real_world_if_any(self, parser: PLSQLSignatureParser):
        # Example: TABLE OF some_type - current grammar might struggle with this fully.
        # The current type is `original_text_for(type_with_attr | type_with_size | type_base)`
        # which should capture it as a string if `type_base` (qualified_identifier) is flexible enough.
        # `qualified_identifier` is `DelimitedList(identifier, delim=DOT, combine=True)`
        # `identifier` is `Word(alphas + "_#$", alphanums + "_#$") | QuotedString`
        # This might not capture "TABLE OF" part correctly within the `type` structure before `DEFAULT`.
        
        # Let's test a type that `qualified_identifier` should handle.
        sig = "PROCEDURE use_pkg_type (p_rec IN my_package.t_my_record) IS"
        result = parser.parse(sig)
        assert result is not None
        assert result["params"][0]["type"] == "my_package.t_my_record"

        # For "TABLE OF", the current `type` using `original_text_for` might grab it,
        # as long as it's followed by a clear delimiter like DEFAULT or end of param list.
        sig_table_of = "PROCEDURE process_list (p_list IN my_pkg.t_string_table) IS"
        # Assuming t_string_table is defined as TABLE OF VARCHAR2(100)
        # The parser will see "my_pkg.t_string_table" as the type name.
        result_table_of = parser.parse(sig_table_of)
        assert result_table_of is not None
        assert result_table_of["params"][0]["type"] == "my_pkg.t_string_table"

        # If the type itself is complex like "SYS.ODCINUMBERLIST"
        sig_complex_sys = "PROCEDURE use_sys_type (p_numbers IN SYS.ODCINUMBERLIST) IS"
        result_complex_sys = parser.parse(sig_complex_sys)
        assert result_complex_sys is not None
        assert result_complex_sys["params"][0]["type"] == "SYS.ODCINUMBERLIST"
    
    # From Client Code
    def test_snippets_from_client_code(self, parser: PLSQLSignatureParser):

        sig = """PROCEDURE AOM_OUTBOUND (
                                    p_date DATE DEFAULT SYSDATE,
                                    p_tasks_p VARCHAR2 DEFAULT NULL,
                                    v_comments VARCHAR(2000)
                                    ) IS --++ EAZUETA - CQ 10316

      output_file                 UTL_FILE.FILE_TYPE;
      v_filename                  VARCHAR2(100);
      l_database_name             VARCHAR2(30);
      g_log_file_location         VARCHAR2(100);
      g_log_file_location_w       VARCHAR2(100); --++ EAZUETA - CQ 19339: Added variable for West only
      l_history_id                NUMBER;
      l_rowid                     ROWID;
      x_errors                    VARCHAR2(500);
      x_retcode                   NUMBER;
      l_charts                    CHARTS%ROWTYPE;
      x_rowid                     ROWID;
      v_comments                  VARCHAR(2000);    --++ EAZUETA - CQ 10236 - OE Autodialer
      v_comm_wqid                 thot.ft_workqueues.description%type;"""
        
        sig, _ = clean_code_and_map_literals(sig, parser.logger)
        result = parser.parse(sig)
        assert result is not None
        assert result["proc_name"] == "AOM_OUTBOUND"
        assert result["params"] == [
            {'name': 'p_date', 'mode': 'IN', 'type': 'DATE', 'default_value': 'SYSDATE'},
            {'name': 'p_tasks_p', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'v_comments', 'mode': 'IN', 'type': 'VARCHAR(2000)', 'default_value': None}
        ]

        sig = """   PROCEDURE ABC.report_and_stop (p_errcode       IN INTEGER  DEFAULT SQLCODE
                              ,p_errmsg       IN VARCHAR2 DEFAULT NULL
                              ,p_log_flag     IN BOOLEAN  DEFAULT TRUE
                              ,p_reraise_flag IN BOOLEAN  DEFAULT TRUE -- [ SSPDT_PrescriptionAPI_Sprint15-001 - RVarguez - 01/08/2017 - Sprint 15
                              ,p_context      IN VARCHAR2 DEFAULT NULL
                              ,p_program_name IN VARCHAR2 DEFAULT NULL
                              ,p_param1       IN VARCHAR2 DEFAULT NULL
                              ,p_param2       IN VARCHAR2 DEFAULT NULL
                              ,p_param3       IN VARCHAR2 DEFAULT NULL
                              ,p_param4       IN VARCHAR2 DEFAULT NULL
                              ,p_param5       IN VARCHAR2 DEFAULT NULL
                              ,p_param6       IN VARCHAR2 DEFAULT NULL
                              ,p_param7       IN VARCHAR2 DEFAULT NULL
                              ,p_param8       IN VARCHAR2 DEFAULT NULL
                              ,p_param9       IN VARCHAR2 DEFAULT NULL
                              ,p_param10      IN VARCHAR2 DEFAULT NULL
                              -- ] SSPDT_PrescriptionAPI_Sprint15-001 - RVarguez - 01/08/2017 - Sprint 15
                              )
   IS
      v_errcode   PLS_INTEGER := NVL (p_errcode, SQLCODE);
      v_errmsg    VARCHAR2(1000) := NVL (p_errmsg, SQLERRM);
      v_prc_name  CONSTANT VARCHAR2(30) := 'report_and_stop';
      -- [ SSPDT_PrescriptionAPI_Sprint15-001 - RVarguez - 01/08/2017 - Sprint 15
      v_context   ws_owner.sds_message_log.context%TYPE; 
      v_message   ws_owner.sds_message_log.message%TYPE; 
      -- ] SSPDT_PrescriptionAPI_Sprint15-001 - RVarguez - 01/08/2017 - Sprint 15
   BEGIN"""
        
        sig, _ = clean_code_and_map_literals(sig, parser.logger)
        result = parser.parse(sig)
        assert result is not None
        assert result["proc_name"] == "ABC.report_and_stop"
        assert result["params"] == [
            {'name': 'p_errcode', 'mode': 'IN', 'type': 'INTEGER', 'default_value': 'SQLCODE'},
            {'name': 'p_errmsg', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_log_flag', 'mode': 'IN', 'type': 'BOOLEAN', 'default_value': 'TRUE'},
            {'name': 'p_reraise_flag', 'mode': 'IN', 'type': 'BOOLEAN', 'default_value': 'TRUE'},
            {'name': 'p_context', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_program_name', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param1', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param2', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param3', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param4', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param5', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param6', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param7', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param8', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param9', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'},
            {'name': 'p_param10', 'mode': 'IN', 'type': 'VARCHAR2', 'default_value': 'NULL'}
        ]
        