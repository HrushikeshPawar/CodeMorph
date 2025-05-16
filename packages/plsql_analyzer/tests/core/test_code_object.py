# tests/core/test_code_object.py
import pytest
import hashlib
import json
from typing import List, Dict, NamedTuple

from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
# Attempt to import the actual CallDetailsTuple first
try:
    from plsql_analyzer.parsing.call_extractor import CallDetailsTuple
except ImportError:
    # Define a mock if the actual one is not available or for isolated testing
    class CallDetailsTuple(NamedTuple):
        call_name: str
        line_no: int
        start_idx: int
        end_idx: int
        positional_params: List[str]
        named_params: Dict[str, str]

class TestPLSQLCodeObject:

    def test_instantiation_defaults(self):
        obj = PLSQL_CodeObject(name="proc1", package_name="pkg1")
        assert obj.name == "proc1"
        assert obj.package_name == "pkg1"
        assert obj.type == CodeObjectType.UNKNOWN
        assert not obj.overloaded
        assert obj.parsed_parameters == []
        assert obj.parsed_return_type is None
        assert obj.extracted_calls == []
        assert obj.id is None # ID not generated until generate_id() or to_dict()

    @pytest.mark.xfail(reason="Moved from `ExtractedCallTuple` to `CallDetailsTuple`")
    def test_instantiation_with_values(self):
        params = [{"name": "p_id", "type": "NUMBER", "mode": "IN"}]
        calls = [ExtractedCallTuple("other_proc", 10, 100, 110)]
        obj = PLSQL_CodeObject(
            name="Func1",
            package_name="PKG.SubPack",
            source="FUNCTION Func1 RETURN BOOLEAN IS BEGIN END;",
            type=CodeObjectType.FUNCTION,
            overloaded=True,
            parsed_parameters=params,
            parsed_return_type="BOOLEAN",
            extracted_calls=calls,
            start_line=5,
            end_line=10
        )
        assert obj.name == "func1" # names are casefolded
        assert obj.package_name == "pkg.subpack" # casefolded
        assert obj.source is not None
        assert obj.type == CodeObjectType.FUNCTION
        assert obj.overloaded
        assert obj.parsed_parameters == params
        assert obj.parsed_return_type == "BOOLEAN"
        assert obj.extracted_calls == calls
        assert obj.start_line == 5
        assert obj.end_line == 10

    def test_cleanup_package_name(self):
        # Case 1: Object name is last part of package_name
        obj1 = PLSQL_CodeObject(name="my_proc", package_name="pkg_a.my_proc")
        assert obj1.package_name == "pkg_a"

        # Case 2: Object name not in package_name
        obj2 = PLSQL_CodeObject(name="my_proc", package_name="pkg_b")
        assert obj2.package_name == "pkg_b"

        # Case 3: Package name is empty
        obj3 = PLSQL_CodeObject(name="my_proc", package_name="")
        assert obj3.package_name == ""
        
        # Case 4: Object name is part of a more complex package_name
        obj4 = PLSQL_CodeObject(name="my_proc", package_name="schema_x.pkg_a.my_proc")
        assert obj4.package_name == "schema_x.pkg_a"

        # Case 5: Name and package_name are the same (e.g. standalone proc where pkg_name derived from filename)
        obj5 = PLSQL_CodeObject(name="my_proc", package_name="my_proc")
        assert obj5.package_name == ""

    def test_generate_id_simple(self):
        obj = PLSQL_CodeObject(name="proc_simple", package_name="pkg_test")
        obj.generate_id()
        assert obj.id == "pkg_test.proc_simple"

        obj_no_pkg = PLSQL_CodeObject(name="proc_solo", package_name="")
        obj_no_pkg.generate_id()
        assert obj_no_pkg.id == "proc_solo"

    def test_generate_id_overloaded_with_params(self):
        params1 = [{"name": "p_id", "type": "NUMBER", "mode": "IN"}]
        obj1 = PLSQL_CodeObject(name="over_proc", package_name="pkg", overloaded=True, parsed_parameters=params1)
        obj1.generate_id()
        id1 = obj1.id

        params2 = [{"name": "p_name", "type": "VARCHAR2", "mode": "IN"}]
        obj2 = PLSQL_CodeObject(name="over_proc", package_name="pkg", overloaded=True, parsed_parameters=params2)
        obj2.generate_id()
        id2 = obj2.id
        
        assert id1 != id2
        assert id1.startswith("pkg.over_proc-")
        assert len(id1.split('-')[1]) == 64 # sha256 hexdigest

        # Same parameters, different order (should yield same ID due to sorting in generate_id)
        params3_order1 = [
            {"name": "p_a", "type": "T1", "mode": "IN"},
            {"name": "p_b", "type": "T2", "mode": "OUT"}
        ]
        params3_order2 = [
            {"name": "p_b", "type": "T2", "mode": "OUT"},
            {"name": "p_a", "type": "T1", "mode": "IN"}
        ]
        obj3a = PLSQL_CodeObject(name="order_proc", package_name="pkg", overloaded=True, parsed_parameters=params3_order1)
        obj3a.generate_id()
        obj3b = PLSQL_CodeObject(name="order_proc", package_name="pkg", overloaded=True, parsed_parameters=params3_order2)
        obj3b.generate_id()
        assert obj3a.id == obj3b.id

    def test_generate_id_overloaded_no_params(self):
        # If overloaded=True but no parameters, ID should be base name
        obj = PLSQL_CodeObject(name="over_no_param", package_name="pkg", overloaded=True, parsed_parameters=[])
        obj.generate_id()
        assert obj.id == "pkg.over_no_param"

    def test_generate_id_not_overloaded_with_params(self):
        # If not overloaded, params should not affect ID hash part
        params = [{"name": "p_id", "type": "NUMBER", "mode": "IN"}]
        obj = PLSQL_CodeObject(name="not_over", package_name="pkg", overloaded=False, parsed_parameters=params)
        obj.generate_id()
        assert obj.id == "pkg.not_over"

    @pytest.mark.xfail(reason="Moved from `ExtractedCallTuple` to `CallDetailsTuple`")
    def test_to_dict_serialization(self):
        params = [{"name": "p_id", "type": "NUMBER", "mode": "IN", "default_value": "1"}]
        calls = [ExtractedCallTuple("another_proc", 10, 100, 110)]
        obj = PLSQL_CodeObject(
            name="MyFunc",
            package_name="TestPkg",
            type=CodeObjectType.FUNCTION,
            overloaded=True,
            parsed_parameters=params,
            parsed_return_type="VARCHAR2",
            extracted_calls=calls,
            start_line=1, end_line=20
        )
        obj_dict = obj.to_dict()

        assert obj_dict["id"] is not None # ID generated by to_dict if not present
        assert obj_dict["name"] == "myfunc"
        assert obj_dict["package_name"] == "testpkg"
        assert obj_dict["type"] == "FUNCTION"
        assert obj_dict["overloaded"] is True
        assert obj_dict["parameters"] == params
        assert obj_dict["return_type"] == "VARCHAR2"
        assert obj_dict["extracted_calls"] == [{"call_name": "another_proc", "line_no": 10, "start_idx": 100, "end_idx": 110}]
        assert obj_dict["source_code_lines"] == {"start": 1, "end": 20}


# --- New tests for serialization and deserialization ---

@pytest.fixture
def sample_call_details_tuple_class() -> type[CallDetailsTuple]:
    """Provides the CallDetailsTuple class (mock or real)."""
    return CallDetailsTuple

@pytest.fixture
def basic_code_object_data_for_serde(sample_call_details_tuple_class) -> Dict:
    """Provides data for a basic PLSQL_CodeObject for serde tests."""
    return {
        'name': 'test_procedure_serde',
        'package_name': 'test_package_serde',
        'clean_code': 'BEGIN NULL; END; -- serde',
        'literal_map': {'<LITERAL_S0>': 'serde_abc'},
        'type': CodeObjectType.PROCEDURE,
        'overloaded': False,
        'parsed_parameters': [{'name': 'p_param_serde', 'type': 'VARCHAR2', 'mode': 'IN'}],
        'parsed_return_type': None,
        'extracted_calls': [
            sample_call_details_tuple_class(
                call_name='another_call_serde', 
                line_no=11, 
                start_idx=110, 
                end_idx=120, 
                positional_params=['s_a'], 
                named_params={'s_b': 's_c'}
            )._asdict() # Store as dict, as to_dict would
        ],
        'source_code_lines': {'start': 110, 'end': 120}
    }

@pytest.fixture
def minimal_code_object_data_for_serde() -> Dict:
    """Provides data for a minimal PLSQL_CodeObject for serde tests."""
    return {
        'name': 'min_func_serde',
        'package_name': '', 
        'type': CodeObjectType.FUNCTION,
    }

@pytest.fixture
def overloaded_code_object_data_for_serde(basic_code_object_data_for_serde) -> Dict:
    """Provides data for an overloaded PLSQL_CodeObject for serde tests."""
    data = basic_code_object_data_for_serde.copy()
    data['name'] = 'overloaded_func_serde'
    data['overloaded'] = True
    data['parsed_parameters'] = [
        {'name': 'p_param_serde1', 'type': 'NUMBER', 'mode': 'IN'},
        {'name': 'p_param_serde2', 'type': 'DATE', 'mode': 'OUT'}
    ]
    return data


class TestPLSQLCodeObjectSerializationDeserialization:

    def test_serialization_to_dict_detailed(self, basic_code_object_data_for_serde, sample_call_details_tuple_class):
        """Test serializing a PLSQL_CodeObject to a dictionary with all fields."""
        b_data = basic_code_object_data_for_serde
        # Convert list of dicts to list of CallDetailsTuple instances for constructor
        calls_tuples = [sample_call_details_tuple_class(**cd_dict) for cd_dict in b_data['extracted_calls']]

        obj = PLSQL_CodeObject(
            name=b_data['name'],
            package_name=b_data['package_name'],
            clean_code=b_data['clean_code'],
            literal_map=b_data['literal_map'],
            type=b_data['type'],
            overloaded=b_data['overloaded'],
            parsed_parameters=b_data['parsed_parameters'],
            parsed_return_type=b_data['parsed_return_type'],
            extracted_calls=calls_tuples, # Pass list of CallDetailsTuple instances
            start_line=b_data['source_code_lines']['start'],
            end_line=b_data['source_code_lines']['end']
        )
        
        obj_dict = obj.to_dict()

        assert obj_dict['id'] is not None
        assert obj_dict['name'] == b_data['name'].strip().casefold() 
        assert obj_dict['package_name'] == b_data['package_name'].strip().casefold()
        assert obj_dict['type'] == b_data['type'].value.upper()
        assert obj_dict['overloaded'] == b_data['overloaded']
        assert obj_dict['parsed_parameters'] == b_data['parsed_parameters']
        assert obj_dict['parsed_return_type'] == b_data['parsed_return_type']
        assert obj_dict['source_code_lines']['start'] == b_data['source_code_lines']['start']
        assert obj_dict['source_code_lines']['end'] == b_data['source_code_lines']['end']
        assert obj_dict['clean_code'] == b_data['clean_code']
        assert obj_dict['literal_map'] == b_data['literal_map']
        # Extracted calls in basic_code_object_data_for_serde are already dicts
        assert obj_dict['extracted_calls'] == b_data['extracted_calls'] 

    def test_deserialization_from_dict_detailed(self, basic_code_object_data_for_serde, sample_call_details_tuple_class):
        """Test deserializing a dictionary back to a PLSQL_CodeObject with all fields."""
        dict_for_from_dict = basic_code_object_data_for_serde.copy()
        # Convert enum type to its string value for the input data, as it would be from JSON/DB
        dict_for_from_dict['type'] = basic_code_object_data_for_serde['type'].value.upper()
        
        # Manually generate an ID as to_dict would, to simulate stored data
        # Names are casefolded by constructor, so use fixture data directly as it's pre-casefolded for name/package
        name_cf = basic_code_object_data_for_serde['name'].strip().casefold()
        pkg_name_cf = basic_code_object_data_for_serde['package_name'].strip().casefold()
        if pkg_name_cf:
            base_id = f"{pkg_name_cf}.{name_cf}"
        else:
            base_id = name_cf
        dict_for_from_dict['id'] = base_id

        obj = PLSQL_CodeObject.from_dict(dict_for_from_dict, sample_call_details_tuple_class)

        b_data = basic_code_object_data_for_serde
        assert obj.id == base_id
        assert obj.name == name_cf
        assert obj.package_name == pkg_name_cf
        assert obj.type == b_data['type'] # from_dict converts string back to enum
        assert obj.overloaded == b_data['overloaded']
        assert obj.parsed_parameters == b_data['parsed_parameters']
        assert obj.parsed_return_type == b_data['parsed_return_type']
        assert obj.start_line == b_data['source_code_lines']['start']
        assert obj.end_line == b_data['source_code_lines']['end']
        assert obj.clean_code == b_data['clean_code']
        assert obj.literal_map == b_data['literal_map']
        
        assert len(obj.extracted_calls) == len(b_data['extracted_calls'])
        if obj.extracted_calls:
            original_call_dict = b_data['extracted_calls'][0]
            deserialized_call_tuple = obj.extracted_calls[0]
            assert isinstance(deserialized_call_tuple, sample_call_details_tuple_class)
            # Compare fields of the CallDetailsTuple
            assert deserialized_call_tuple.call_name == original_call_dict['call_name']
            assert deserialized_call_tuple.line_no == original_call_dict['line_no']
            assert deserialized_call_tuple.start_idx == original_call_dict['start_idx']
            assert deserialized_call_tuple.end_idx == original_call_dict['end_idx']
            assert deserialized_call_tuple.positional_params == original_call_dict['positional_params']
            assert deserialized_call_tuple.named_params == original_call_dict['named_params']

    def test_serialization_deserialization_roundtrip(self, basic_code_object_data_for_serde, sample_call_details_tuple_class):
        """Test that serializing then deserializing yields an equivalent object."""
        b_data = basic_code_object_data_for_serde
        calls_tuples = [sample_call_details_tuple_class(**cd_dict) for cd_dict in b_data['extracted_calls']]

        original_obj = PLSQL_CodeObject(
            name=b_data['name'],
            package_name=b_data['package_name'],
            clean_code=b_data['clean_code'],
            literal_map=b_data['literal_map'],
            type=b_data['type'],
            overloaded=b_data['overloaded'],
            parsed_parameters=b_data['parsed_parameters'],
            parsed_return_type=b_data['parsed_return_type'],
            extracted_calls=calls_tuples,
            start_line=b_data['source_code_lines']['start'],
            end_line=b_data['source_code_lines']['end']
        )
        # ID is generated by to_dict if not present, or by generate_id() if called.
        # For roundtrip, ensure it's generated before to_dict for a stable comparison.
        original_obj.generate_id() 

        obj_dict = original_obj.to_dict()
        
        assert isinstance(obj_dict['type'], str) # to_dict converts enum to string

        deserialized_obj = PLSQL_CodeObject.from_dict(obj_dict, sample_call_details_tuple_class)

        # Compare all relevant attributes
        assert deserialized_obj.id == original_obj.id
        assert deserialized_obj.name == original_obj.name # Already casefolded
        assert deserialized_obj.package_name == original_obj.package_name # Already casefolded
        assert deserialized_obj.type == original_obj.type
        assert deserialized_obj.overloaded == original_obj.overloaded
        assert deserialized_obj.parsed_parameters == original_obj.parsed_parameters
        assert deserialized_obj.parsed_return_type == original_obj.parsed_return_type
        assert deserialized_obj.start_line == original_obj.start_line
        assert deserialized_obj.end_line == original_obj.end_line
        assert deserialized_obj.clean_code == original_obj.clean_code
        assert deserialized_obj.literal_map == original_obj.literal_map
        # CallDetailsTuple is a NamedTuple, so direct list comparison should work if contents are identical
        assert deserialized_obj.extracted_calls == original_obj.extracted_calls 

    def test_deserialization_minimal_data(self, minimal_code_object_data_for_serde, sample_call_details_tuple_class):
        """Test deserialization with only mandatory fields and verify defaults."""
        dict_for_from_dict = minimal_code_object_data_for_serde.copy()
        dict_for_from_dict['type'] = minimal_code_object_data_for_serde['type'].value.upper()
        
        obj = PLSQL_CodeObject.from_dict(dict_for_from_dict, sample_call_details_tuple_class)
        m_data = minimal_code_object_data_for_serde
        name_cf = m_data['name'].strip().casefold()
        pkg_name_cf = m_data['package_name'].strip().casefold() if m_data['package_name'] else ""


        assert obj.name == name_cf
        assert obj.package_name == pkg_name_cf 
        assert obj.type == m_data['type']
        assert obj.clean_code is None
        assert obj.literal_map is None 
        assert obj.overloaded is False 
        assert obj.parsed_parameters == [] 
        assert obj.parsed_return_type is None 
        assert obj.extracted_calls == [] 
        assert obj.start_line is None 
        assert obj.end_line is None 
        
        expected_id = name_cf # No package name, so ID is just the name
        # from_dict ensures ID is present, either from dict or by calling generate_id()
        assert obj.id == expected_id 

    def test_deserialization_overloaded_object(self, overloaded_code_object_data_for_serde, sample_call_details_tuple_class):
        """Test deserialization of an overloaded object, ensuring ID is correctly handled/generated."""
        dict_for_from_dict = overloaded_code_object_data_for_serde.copy()
        o_data = overloaded_code_object_data_for_serde
        dict_for_from_dict['type'] = o_data['type'].value.upper()

        name_cf = o_data['name'].strip().casefold()
        pkg_name_cf = o_data['package_name'].strip().casefold()

        # Calculate expected ID to simulate it being stored in the dict
        base_id = f"{pkg_name_cf}.{name_cf}" if pkg_name_cf else name_cf
        params_for_hash = sorted(o_data['parsed_parameters'], key=lambda p: p.get('name',''))
        param_hash_str = json.dumps(params_for_hash, sort_keys=True, indent=0)
        expected_id = f"{base_id}-{hashlib.sha256(param_hash_str.encode()).hexdigest()}"
        dict_for_from_dict['id'] = expected_id # Simulate stored ID

        obj = PLSQL_CodeObject.from_dict(dict_for_from_dict, sample_call_details_tuple_class)

        assert obj.id == expected_id
        assert obj.name == name_cf
        assert obj.package_name == pkg_name_cf
        assert obj.type == o_data['type']
        assert obj.overloaded == o_data['overloaded']
        assert obj.parsed_parameters == o_data['parsed_parameters']

    def test_type_deserialization_unknown_type_string(self, sample_call_details_tuple_class):
        """Test deserialization when the type string from dict is not a valid CodeObjectType member."""
        name_cf = 'unknown_typed_obj_serde'.strip().casefold()
        pkg_name_cf = 'test_pkg_serde'.strip().casefold()
        expected_id = f"{pkg_name_cf}.{name_cf}"
        data = {
            'name': name_cf, # Already casefolded for consistency
            'package_name': pkg_name_cf,
            'type': 'NON_EXISTENT_TYPE', 
            'id': expected_id 
        }
        obj = PLSQL_CodeObject.from_dict(data, sample_call_details_tuple_class)
        assert obj.type == CodeObjectType.UNKNOWN

    def test_type_deserialization_type_missing(self, sample_call_details_tuple_class):
        """Test deserialization when the type key is missing from the dict."""
        name_cf = 'missing_type_obj_serde'.strip().casefold()
        pkg_name_cf = 'test_pkg_serde'.strip().casefold()
        expected_id = f"{pkg_name_cf}.{name_cf}"
        data = {
            'name': name_cf,
            'package_name': pkg_name_cf,
            # 'type': key is missing
            'id': expected_id
        }
        obj = PLSQL_CodeObject.from_dict(data, sample_call_details_tuple_class)
        assert obj.type == CodeObjectType.UNKNOWN 

    def test_extracted_calls_reconstruction_detailed(self, sample_call_details_tuple_class):
        """Test detailed reconstruction of extracted_calls list with multiple items."""
        call_data_list = [
            {'call_name': 'call1_serde', 'line_no': 1, 'start_idx': 0, 'end_idx': 5, 'positional_params': ['s_a'], 'named_params': {}},
            {'call_name': 'call2_serde', 'line_no': 2, 'start_idx': 10, 'end_idx': 15, 'positional_params': [], 'named_params': {'s_p': '1'}}
        ]
        name_cf = 'caller_func_serde'.strip().casefold()
        pkg_name_cf = 'utils_serde'.strip().casefold()
        expected_id = f"{pkg_name_cf}.{name_cf}"
        data_dict = {
            'name': name_cf,
            'package_name': pkg_name_cf,
            'type': 'FUNCTION', 
            'extracted_calls': call_data_list,
            'id': expected_id
        }
        obj = PLSQL_CodeObject.from_dict(data_dict, sample_call_details_tuple_class)
        
        assert len(obj.extracted_calls) == 2
        assert isinstance(obj.extracted_calls[0], sample_call_details_tuple_class)
        assert isinstance(obj.extracted_calls[1], sample_call_details_tuple_class)
        
        assert obj.extracted_calls[0].call_name == 'call1_serde'
        assert obj.extracted_calls[0].positional_params == ['s_a']
        
        assert obj.extracted_calls[1].call_name == 'call2_serde'
        assert obj.extracted_calls[1].named_params == {'s_p': '1'}

    def test_source_code_lines_deserialization_variations(self, sample_call_details_tuple_class):
        """Test deserialization of source_code_lines (start_line, end_line) with variations."""
        # Case 1: Both start and end present
        name_cf1 = 'lined_obj_serde'.strip().casefold()
        pkg_name_cf1 = 'src_serde'.strip().casefold()
        id1 = f"{pkg_name_cf1}.{name_cf1}"
        data_full = {
            'name': name_cf1, 'package_name': pkg_name_cf1, 'type': 'PROCEDURE',
            'source_code_lines': {'start': 50, 'end': 100}, 'id': id1
        }
        obj_full = PLSQL_CodeObject.from_dict(data_full, sample_call_details_tuple_class)
        assert obj_full.start_line == 50
        assert obj_full.end_line == 100

        # Case 2: source_code_lines key is missing entirely
        name_cf2 = 'no_lines_key_obj_serde'.strip().casefold()
        pkg_name_cf2 = 'src_serde'.strip().casefold()
        id2 = f"{pkg_name_cf2}.{name_cf2}"
        data_no_lines_key = {
            'name': name_cf2, 'package_name': pkg_name_cf2, 'type': 'PROCEDURE', 'id': id2
        }
        obj_no_lines_key = PLSQL_CodeObject.from_dict(data_no_lines_key, sample_call_details_tuple_class)
        assert obj_no_lines_key.start_line is None
        assert obj_no_lines_key.end_line is None

        # Case 3: source_code_lines is present but empty dict
        name_cf3 = 'empty_lines_dict_obj_serde'.strip().casefold()
        pkg_name_cf3 = 'src_serde'.strip().casefold()
        id3 = f"{pkg_name_cf3}.{name_cf3}"
        data_empty_lines_dict = {
            'name': name_cf3, 'package_name': pkg_name_cf3, 'type': 'PROCEDURE',
            'source_code_lines': {}, 'id': id3
        }
        obj_empty_lines_dict = PLSQL_CodeObject.from_dict(data_empty_lines_dict, sample_call_details_tuple_class)
        assert obj_empty_lines_dict.start_line is None
        assert obj_empty_lines_dict.end_line is None

        # Case 4: Partially missing start/end in source_code_lines
        name_cf4a = 'partial_lines_obj_serde'.strip().casefold()
        pkg_name_cf4a = 'src_serde'.strip().casefold()
        id4a = f"{pkg_name_cf4a}.{name_cf4a}"
        data_partial_lines = {
            'name': name_cf4a, 'package_name': pkg_name_cf4a, 'type': 'PROCEDURE',
            'source_code_lines': {'start': 10}, 'id': id4a
        }
        obj_partial_lines = PLSQL_CodeObject.from_dict(data_partial_lines, sample_call_details_tuple_class)
        assert obj_partial_lines.start_line == 10
        assert obj_partial_lines.end_line is None

        name_cf4b = 'partial_lines_end_obj_serde'.strip().casefold()
        pkg_name_cf4b = 'src_serde'.strip().casefold()
        id4b = f"{pkg_name_cf4b}.{name_cf4b}"
        data_partial_lines_end_only = {
            'name': name_cf4b, 'package_name': pkg_name_cf4b, 'type': 'PROCEDURE',
            'source_code_lines': {'end': 200}, 'id': id4b
        }
        obj_partial_lines_end_only = PLSQL_CodeObject.from_dict(data_partial_lines_end_only, sample_call_details_tuple_class)
        assert obj_partial_lines_end_only.start_line is None
        assert obj_partial_lines_end_only.end_line == 200