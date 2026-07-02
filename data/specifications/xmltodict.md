Project: `nested_markup_converter`


## 1. High-Level Goal
Implement a Python library named `nested_markup_converter` that provides bidirectional conversion between XML strings and Python dictionaries. The library must handle deep nesting, XML attributes, text content, namespaces, and custom formatting rules while preserving the hierarchical structure of the data.

## 2. Module Structure & Exceptions
* **Module Name:** Create a module named `nested_markup_converter`.
* **Custom Exception:** Define a custom exception class named `ParsingInterrupted` that inherits from `Exception`. Expose this at the module level.
* **Standard Library Dependencies:** You must use `xml.parsers.expat` for XML parsing.

## 3. Public API: `parse` Function

Implement a module-level function named `parse` that converts an XML string into a Python dictionary.

### Signature
```python
def parse(
    xml_input, 
    force_list=(), 
    attr_prefix="@", 
    cdata_key="#text", 
    xml_attribs=True, 
    dict_constructor=dict, 
    postprocessor=None, 
    process_namespaces=False, 
    namespace_separator=":", 
    item_depth=0, 
    item_callback=None
)
```

### Parsing Rules & Behaviors
* **Basic Elements:** Convert XML tags into dictionary keys and their text content into string values (e.g., `<name>Alice</name>` becomes `{"name": "Alice"}`).
* **Nesting:** Recursively convert nested XML elements into nested dictionaries.
* **Empty Elements:** If an element is empty (e.g., `<empty></empty>` or `<empty/>`), its parsed value must be `None`, not an empty string.
* **Text Stripping:** You must strip leading and trailing whitespace from all text content.
* **Unicode & Entities:** The parser must correctly unescape standard XML entities (e.g., `&amp;` to `&`) and natively support Unicode characters.
* **Malformed XML:** If `xml_input` is empty, contains unclosed tags, or is otherwise malformed, you must raise `xml.parsers.expat.ExpatError`.

### Argument-Specific Logic
* **`xml_attribs` & `attr_prefix`:** 
  * If `xml_attribs=True` (default), parse XML attributes. Store them in the dictionary using the attribute name prefixed by `attr_prefix` (default `"@"`).
  * If `xml_attribs=False`, completely ignore and discard all XML attributes.
* **`cdata_key`:** If an XML element contains *both* attributes and text content, represent the element as a dictionary. Store the text content in this dictionary under the key specified by `cdata_key` (default `"#text"`).
* **Sibling Aggregation & `force_list`:** 
  * If multiple sibling elements share the same tag name, aggregate their parsed values into a Python `list` under that single key.
  * If a tag name is present in the `force_list` iterable, its parsed value MUST be wrapped in a `list`, even if there is only one occurrence of that element.
* **`dict_constructor`:** Use this callable (default `dict`) to instantiate all dictionary objects created during parsing. If a user passes `collections.OrderedDict`, the entire returned hierarchy must consist of `OrderedDict` instances.
* **`process_namespaces` & `namespace_separator`:**
  * If `False` (default), preserve namespace prefixes exactly as written in the XML (e.g., `x:item` remains `"x:item"`, and `xmlns:x` becomes `"@xmlns:x"`).
  * If `True`, resolve namespace prefixes to their URIs. The resulting dictionary key must be formatted as `<URI><namespace_separator><local_name>` (e.g., `"http://example.com/ns|item"`).
* **`postprocessor`:** If provided, this callable must be invoked for every parsed key-value pair. It receives `(path, key, value)` and must return a tuple `(new_key, new_value)`. The dictionary must store the returned key and value instead of the original ones.
* **`item_depth` & `item_callback`:** If `item_depth` > 0 and `item_callback` is provided, invoke `item_callback(path, item)` for every element parsed at that specific depth (where the root element is depth 1, its children are depth 2, etc.). If the callback returns `False`, immediately raise the custom `nested_markup_converter.ParsingInterrupted` exception.

---

## 4. Public API: `unparse` Function

Implement a module-level function named `unparse` that converts a Python dictionary back into an XML string.

### Signature
```python
def unparse(
    input_dict, 
    full_document=True, 
    attr_prefix="@", 
    cdata_key="#text", 
    pretty=False, 
    indent="\t"
)
```

### Unparsing Rules & Behaviors
* **Root Validation:** The `input_dict` must contain exactly ONE root key. If the dictionary contains multiple root keys, you must raise a `ValueError` with a message that includes the exact phrase: `"Document must have exactly one root"`.
* **Basic Conversion:** Convert dictionary keys into XML tags and their string values into inner text.
* **Lists to Siblings:** If a dictionary value is a `list`, generate multiple sibling XML elements sharing the same tag name (the key) for each item in the list.
* **Roundtripping:** The output of `unparse` must be perfectly parsable by `parse` to recreate the original dictionary structure.

### Argument-Specific Logic
* **`full_document`:** 
  * If `True` (default), prepend the standard XML declaration to the output string: `<?xml version="1.0" encoding="utf-8"?>`.
  * If `False`, omit the XML declaration entirely.
* **`attr_prefix`:** Any dictionary key that starts with the `attr_prefix` string (default `"@"`) must be converted into an XML attribute of its parent element, rather than a child XML element.
* **`cdata_key`:** If a dictionary key matches the `cdata_key` string (default `"#text"`), its value must be inserted as the raw inner text of the parent XML element, rather than creating a new child tag.
* **`pretty` & `indent`:** 
  * If `pretty=True`, format the resulting XML string with newlines and indentation to reflect the hierarchical structure.
  * Use the string provided in `indent` (default `"\t"`) for each level of nesting.
  * If `full_document=True` and `pretty=True`, ensure there is a newline immediately following the `<?xml ... ?>` declaration.