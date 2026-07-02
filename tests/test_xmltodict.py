# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import xmltodict

# 4. Auxiliary: Standard Library
from collections import OrderedDict
from xml.parsers.expat import ExpatError
import xml.parsers.expat


def test_parse_simple_xml_to_dict():
    xml_input = "<root><message>Hello</message></root>"
    expected_output = {"root": {"message": "Hello"}}

    result = xmltodict.parse(xml_input)

    assert result == expected_output

def test_parse_repeated_child_elements_yields_list():
    xml_input = "<root><item>1</item><item>2</item><item>3</item></root>"

    result = xmltodict.parse(xml_input)

    assert "root" in result
    assert result["root"]["item"] == ["1", "2", "3"]

def test_parse_element_with_attributes_and_text():
    xml_input = '<user id="123">Alice</user>'

    result = xmltodict.parse(xml_input)

    assert "user" in result
    assert "@id" in result["user"]
    assert "#text" in result["user"]
    assert result["user"]["@id"] == "123"
    assert result["user"]["#text"] == "Alice"

def test_unparse_and_parse_roundtrip_preserves_structure():
    original_dict = {
        "root": {
            "item": [
                {"@id": "1", "#text": "A"},
                {"@id": "2", "#text": "B"}
            ]
        }
    }

    xml_string = xmltodict.unparse(original_dict)
    roundtrip_dict = xmltodict.parse(xml_string)

    assert roundtrip_dict == original_dict

def test_parse_preserves_namespace_prefixes_in_keys():
    xml_input = '<root xmlns:x="http://example.com/x"><x:item>value</x:item></root>'

    result = xmltodict.parse(xml_input)

    assert "root" in result
    assert "x:item" in result["root"]
    assert result["root"]["x:item"] == "value"
    assert result["root"]["@xmlns:x"] == "http://example.com/x"

def test_parse_deeply_nested_xml_structure():
    xml_input = """
    <root>
        <user>
            <address>
                <city>New York</city>
            </address>
        </user>
    </root>
    """
    result = xmltodict.parse(xml_input)

    # Verify 3 levels of nesting: root -> user -> address -> city
    assert "root" in result
    assert "user" in result["root"]
    assert "address" in result["root"]["user"]
    assert result["root"]["user"]["address"]["city"] == "New York"

def test_parse_force_list_converts_single_element_to_list():
    xml_input = "<root><item>1</item></root>"

    result = xmltodict.parse(xml_input, force_list=("item",))

    # Verify the result is ["1"] instead of the string "1"
    assert isinstance(result["root"]["item"], list)
    assert result["root"]["item"] == ["1"]

def test_parse_with_custom_attr_prefix_and_cdata_key():
    xml_input = '<user id="7">Bob</user>'

    result = xmltodict.parse(xml_input, attr_prefix="$", cdata_key="text")

    # Verify the custom keys "$id" and "text" are used
    assert "$id" in result["user"]
    assert result["user"]["$id"] == "7"

    assert "text" in result["user"]
    assert result["user"]["text"] == "Bob"

    # Verify default keys are not present
    assert "@id" not in result["user"]
    assert "#text" not in result["user"]

def test_parse_ignores_attributes_when_xml_attribs_is_false():
    xml_input = '<user id="9"><name>Alice</name></user>'

    result = xmltodict.parse(xml_input, xml_attribs=False)

    # Verify the @id key is entirely absent from the output
    assert "@id" not in result["user"]

    # Verify the rest of the parsing succeeded
    assert result["user"]["name"] == "Alice"

def test_parse_uses_custom_dict_constructor():
    xml_input = "<root><child>value</child></root>"

    result = xmltodict.parse(xml_input, dict_constructor=OrderedDict)

    # Assert that the returned object and its nested mappings are instances of OrderedDict
    assert isinstance(result, OrderedDict)
    assert isinstance(result["root"], OrderedDict)
    assert result["root"]["child"] == "value"

def test_unparse_pretty_and_full_document_roundtrips_successfully():
    input_dict = {"root": {"child": "data"}}

    xml_str = xmltodict.unparse(input_dict, pretty=True, full_document=True)

    # Verify formatting and full document declaration
    assert "<?xml version=\"1.0\" encoding=\"utf-8\"?>" in xml_str
    assert "<root>" in xml_str
    assert "\n" in xml_str

    # Verify roundtrip
    roundtripped = xmltodict.parse(xml_str)
    assert roundtripped == input_dict

def test_parse_applies_postprocessor_transformation():
    xml_str = "<root><message>Hello</message></root>"

    def postprocessor(path, key, value):
        if key == "message" and value == "Hello":
            return key, "HELLO"
        return key, value

    result = xmltodict.parse(xml_str, postprocessor=postprocessor)

    assert result["root"]["message"] == "HELLO"

def test_module_exposes_parse_and_unparse():
    assert hasattr(xmltodict, "parse")
    assert callable(xmltodict.parse)

    assert hasattr(xmltodict, "unparse")
    assert callable(xmltodict.unparse)

def test_parse_and_unparse_valid_and_nested_xml():
    # Basic XML roundtripping
    basic_xml = "<root><name>test</name><value>123</value></root>"
    basic_dict = xmltodict.parse(basic_xml)

    assert basic_dict == {"root": {"name": "test", "value": "123"}}

    unparsed_basic = xmltodict.unparse(basic_dict, full_document=False)
    assert unparsed_basic == basic_xml

    # Deeply nested XML
    nested_xml = "<root><level1><level2><level3>value</level3></level2></level1></root>"
    nested_dict = xmltodict.parse(nested_xml)

    assert nested_dict == {"root": {"level1": {"level2": {"level3": "value"}}}}

def test_parse_malformed_xml_and_escaped_unicode_characters():
    # Malformed XML
    malformed_xml = "<root><name>test<value>123</value></root>"
    with pytest.raises(ExpatError):
        xmltodict.parse(malformed_xml)

    # Unicode and escaped entities
    unicode_xml = "<root><name>测试&amp;字符</name><value>123</value></root>"
    unicode_dict = xmltodict.parse(unicode_xml)

    assert unicode_dict["root"]["name"] == "测试&字符"
    assert unicode_dict["root"]["value"] == "123"

def test_parse_large_xml_payload_with_repeated_elements():
    items = []
    for i in range(600):
        items.append(f"<item id='{i}'><name>Item {i}</name><value>{i}</value></item>")

    xml_payload = f"<root>{''.join(items)}</root>"

    result = xmltodict.parse(xml_payload)

    assert "root" in result
    assert "item" in result["root"]
    assert isinstance(result["root"]["item"], list)
    assert len(result["root"]["item"]) == 600

    assert result["root"]["item"][0] == {"@id": "0", "name": "Item 0", "value": "0"}
    assert result["root"]["item"][599] == {"@id": "599", "name": "Item 599", "value": "599"}

def test_parse_valid_xml_returns_hierarchical_dictionary():
    xml_string = "<root><level1><level2><level3>deep_value</level3></level2></level1></root>"

    result = xmltodict.parse(xml_string)

    expected_output = {'root': {'level1': {'level2': {'level3': 'deep_value'}}}}
    assert result == expected_output

def test_parse_element_with_attributes_creates_prefixed_keys():
    xml_string = '<user id="9942" status="active" role="admin"><name>Alice</name></user>'

    result = xmltodict.parse(xml_string)

    expected_output = {'user': {'@id': '9942', '@status': 'active', '@role': 'admin', 'name': 'Alice'}}
    assert result == expected_output

def test_parse_element_with_attributes_and_text_uses_cdata_key():
    xml_string = '<message priority="high" timestamp="2023-10-25">  Critical System Failure  </message>'

    result = xmltodict.parse(xml_string)

    expected_output = {'message': {'@priority': 'high', '@timestamp': '2023-10-25', '#text': 'Critical System Failure'}}
    assert result == expected_output

def test_parse_empty_elements_evaluate_to_none():
    xml_string_standard = "<data><value>123.45</value></data>"
    result_standard = xmltodict.parse(xml_string_standard)
    assert result_standard == {'data': {'value': '123.45'}}

    xml_string_empty = "<data><empty></empty></data>"
    result_empty = xmltodict.parse(xml_string_empty)
    assert result_empty == {'data': {'empty': None}}

    xml_string_self_closing = "<data><empty/></data>"
    result_self_closing = xmltodict.parse(xml_string_self_closing)
    assert result_self_closing == {'data': {'empty': None}}

def test_parse_multiple_sibling_elements_aggregates_to_list():
    xml_input = '<inventory><item>Apple</item><item id="2">Banana</item><item>Cherry</item></inventory>'
    expected_output = {'inventory': {'item': ['Apple', {'@id': '2', '#text': 'Banana'}, 'Cherry']}}

    result = xmltodict.parse(xml_input)

    assert result == expected_output

def test_parse_with_force_list_wraps_single_element_in_list():
    xml_input = '<root><item>A</item><single>B</single></root>'

    result = xmltodict.parse(xml_input, force_list=('single',))

    assert result['root']['single'] == ['B']
    assert result['root']['item'] == 'A'

def test_parse_with_process_namespaces_expands_uri_in_keys():
    xml_input = '<root xmlns:ns="http://example.com/ns"><ns:item>Value</ns:item></root>'

    result = xmltodict.parse(xml_input, process_namespaces=True, namespace_separator='|')

    assert 'http://example.com/ns|item' in result['root']
    assert 'ns:item' not in result['root']
    assert result['root']['http://example.com/ns|item'] == 'Value'

def test_unparse_valid_dictionary_generates_equivalent_xml_string():
    input_dict = {'catalog': {'book': {'title': 'Dune', 'author': 'Frank Herbert'}}}
    expected_xml = '<?xml version="1.0" encoding="utf-8"?><catalog><book><title>Dune</title><author>Frank Herbert</author></book></catalog>'

    generated_xml = xmltodict.unparse(input_dict)

    # xmltodict.unparse typically inserts a newline after the XML declaration.
    # We remove newlines to strictly match the requested expected output string format.
    assert generated_xml.replace('\n', '') == expected_xml.replace('\n', '')

    # Roundtrip Assertion
    assert xmltodict.parse(xmltodict.unparse(input_dict)) == input_dict

def test_unparse_with_attribute_prefix_generates_xml_attributes():
    input_dict = {'user': {'@id': '12345', 'name': 'Alice'}}

    generated_xml = xmltodict.unparse(input_dict, attr_prefix='@')

    assert '<user id="12345">' in generated_xml
    assert '<name>Alice</name>' in generated_xml
    assert '<@id>12345</@id>' not in generated_xml

def test_unparse_with_cdata_key_generates_element_text_content():
    input_dict = {'node': {'@class': 'highlight', '#text': 'Important Content'}}

    # full_document=False is required to omit the <?xml ... ?> declaration for an exact match
    result = xmltodict.unparse(input_dict, cdata_key='#text', full_document=False)

    assert result == '<node class="highlight">Important Content</node>'
    assert '<#text>' not in result

def test_unparse_with_pretty_and_full_document_flags_generates_formatted_xml():
    input_dict = {"root": {"child": "data"}}

    result = xmltodict.unparse(
        input_dict,
        pretty=True,
        indent="\t",
        full_document=True
    )

    assert result.startswith('<?xml version="1.0" encoding="utf-8"?>\n')
    assert '\n\t<child>data</child>\n' in result

def test_parse_malformed_xml_raises_expat_error():
    malformed_inputs = [
        "<root><child>data</root>",
        "",
        "   invalid <root></root>"
    ]

    for invalid_xml in malformed_inputs:
        with pytest.raises(xml.parsers.expat.ExpatError):
            xmltodict.parse(invalid_xml)

def test_unparse_multiple_root_keys_raises_value_error():
    invalid_input = {"root_one": {"child": "A"}, "root_two": {"child": "B"}}

    with pytest.raises(ValueError) as exc_info:
        xmltodict.unparse(invalid_input)

    assert "Document must have exactly one root" in str(exc_info.value)

def test_parse_item_callback_returning_false_raises_parsing_interrupted():
    xml_input = "<stream><item>1</item><item>STOP</item><item>3</item></stream>"

    def callback(path, item):
        if item == "STOP":
            return False
        return True

    with pytest.raises(xmltodict.ParsingInterrupted):
        # item_depth=2 targets the <item> elements (depth 1 is <stream>)
        xmltodict.parse(xml_input, item_depth=2, item_callback=callback)
