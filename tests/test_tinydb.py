# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage

# 4. Auxiliary: Standard Library
import datetime
import os
import re


@pytest.fixture
def db():
    """
    Provides an isolated, in-memory TinyDB instance for each test.
    This is the idiomatic way to test TinyDB without leaving file artifacts.
    """
    return TinyDB(storage=MemoryStorage)

def test_search_returns_matching_inserted_documents(db):
    db.insert({"name": "Alice", "age": 25})
    db.insert({"name": "Bob", "age": 30})
    db.insert({"name": "Charlie", "age": 35})

    User = Query()
    results = db.search(User.age >= 30)

    assert len(results) == 2

    # Verify the exact contents of the returned documents
    returned_names = {doc["name"] for doc in results}
    returned_ages = {doc["age"] for doc in results}

    assert returned_names == {"Bob", "Charlie"}
    assert returned_ages == {30, 35}

def test_table_insertions_are_isolated(db):
    tasks = db.table("tasks")
    logs = db.table("logs")

    tasks.insert({"task": "Write tests", "priority": "high"})
    tasks.insert({"task": "Review PRs", "priority": "medium"})

    # Verify tasks table has 2 documents and logs table is completely unaffected
    assert len(tasks.all()) == 2
    assert len(logs.all()) == 0

    logs.insert({"level": "INFO", "message": "System initialized"})

    # Verify logs table now has 1 document and tasks table remains unaffected
    assert len(tasks.all()) == 2
    assert len(logs.all()) == 1

def test_update_and_remove_apply_only_to_queried_documents(db):
    db.insert({"title": "task-1", "done": False})
    db.insert({"title": "task-2", "done": False})
    db.insert({"title": "task-3", "done": False})

    Task = Query()

    # Apply update payload to specific condition
    db.update({"done": True}, Task.title == "task-2")

    # Verify only the matching document was updated
    completed_tasks = db.search(Task.done == True)
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["title"] == "task-2"

    pending_tasks = db.search(Task.done == False)
    assert len(pending_tasks) == 2

    # Apply remove to specific condition
    db.remove(Task.done == True)

    # Verify only the matching document was deleted
    remaining_tasks = db.all()
    assert len(remaining_tasks) == 2
    assert not any(doc["title"] == "task-2" for doc in remaining_tasks)

def test_where_shorthand_evaluates_correctly_in_search(db):
    db.insert({"name": "Akira", "city": "Tokyo"})
    db.insert({"name": "Kenji", "city": "Kyoto"})
    db.insert({"name": "Sakura", "city": "Tokyo"})

    # Using the exact shorthand syntax requested
    results = db.search(where("city") == "Tokyo")

    assert len(results) == 2
    for doc in results:
        assert doc["city"] == "Tokyo"

    returned_names = {doc["name"] for doc in results}
    assert returned_names == {"Akira", "Sakura"}

def test_get_returns_document_object(db):
    db.insert({"name": "Alice", "role": "Admin"})
    db.insert({"name": "Bob", "role": "Editor"})
    db.insert({"name": "Charlie", "role": "Viewer"})

    User = Query()

    # Query for a specific document
    result = db.get(User.name == "Bob")

    # Verify it returns exactly one document as a dictionary (not a list)
    assert isinstance(result, dict)
    assert result["name"] == "Bob"
    assert result["role"] == "Editor"

def test_insert_multiple_returns_list_of_doc_ids(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    docs = [{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}]
    ids = db.insert_multiple(docs)

    assert isinstance(ids, list)
    assert len(ids) == len(docs)

    all_docs = db.all()
    assert len(all_docs) == len(docs)
    for doc in docs:
        assert doc in all_docs

def test_contains_and_count_evaluate_queries_correctly(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    db.insert_multiple([
        {"name": "Alice", "age": 25},
        {"name": "Bob", "age": 30},
        {"name": "Charlie", "age": 35}
    ])

    User = Query()

    assert db.contains(User.name == "Alice") is True
    assert db.contains(User.name == "Dora") is False

    assert db.count(User.age >= 30) == 2

def test_database_persists_data_across_instances(tmp_path):
    db_path = tmp_path / "persist.json"

    db1 = TinyDB(db_path)
    db1.insert({"test_key": "test_value"})
    db1.close()

    db2 = TinyDB(db_path)
    all_docs = db2.all()

    assert len(all_docs) == 1
    assert all_docs[0]["test_key"] == "test_value"
    db2.close()

def test_truncate_clears_specific_table_without_affecting_others(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    table1 = db.table("table1")
    table2 = db.table("table2")

    table1.insert_multiple([{"id": 1}, {"id": 2}])
    table2.insert_multiple([{"id": 3}, {"id": 4}, {"id": 5}])

    assert len(table1) == 2
    assert len(table2) == 3

    table1.truncate()

    assert len(table1) == 0
    assert len(table2) == 3
    assert table2.all() == [{"id": 3}, {"id": 4}, {"id": 5}]

def test_update_modifies_specific_documents_by_id(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)
    table = db.table("my_table")

    doc_id = table.insert({"name": "John", "status": "active"})
    table.insert({"name": "Jane", "status": "active"})

    table.update({"status": "inactive"}, doc_ids=[doc_id])

    updated_doc = table.get(doc_id=doc_id)
    assert updated_doc["status"] == "inactive"
    assert updated_doc["name"] == "John"

    other_docs = table.search(Query().name == "Jane")
    assert len(other_docs) == 1
    assert other_docs[0]["status"] == "active"

def test_remove_deletes_specific_documents_by_id(tmp_path):
    db = TinyDB(str(tmp_path / "db.json"))

    id1 = db.insert({"name": "doc1"})
    id2 = db.insert({"name": "doc2"})
    id3 = db.insert({"name": "doc3"})

    # Remove specific document by ID
    db.remove(doc_ids=[id2])

    # Verify only the specified document was deleted
    assert db.get(doc_id=id1) is not None
    assert db.get(doc_id=id2) is None
    assert db.get(doc_id=id3) is not None
    assert len(db) == 2

    db.close()

def test_tables_returns_names_of_populated_tables(tmp_path):
    db = TinyDB(str(tmp_path / "db.json"))

    # Create custom tables and insert data
    t1 = db.table("t1")
    t2 = db.table("t2")

    t1.insert({"data": "value1"})
    t2.insert({"data": "value2"})

    tables = db.tables()

    # Assert custom tables appear in the output
    assert "t1" in tables
    assert "t2" in tables
    assert isinstance(tables, (set, list))

    db.close()

def test_crud_operations_with_edge_case_documents(tmp_path):
    db = TinyDB(str(tmp_path / "db.json"))

    # Insert empty dict
    db.insert({})

    # Insert strings with unicode and special characters
    db.insert({"text": "特殊字符: 中文测试 😀 \n\t"})

    # Insert deeply nested dictionary (9 levels deep)
    db.insert({"l1": {"l2": {"l3": {"l4": {"l5": {"l6": {"l7": {"l8": {"l9": "deep"}}}}}}}}})

    assert len(db) == 3

    q = Query()

    # Query against non-existent field
    assert len(db.search(q.non_existent_field == "value")) == 0

    # Update using condition on non-existent field
    db.update({"updated": True}, q.non_existent_field == "value")

    # Remove using condition on non-existent field
    db.remove(q.non_existent_field == "value")

    # Verify length remains unchanged after non-existent field operations
    assert len(db) == 3

    # Retrieve using a Query condition
    doc = db.get(q.text == "特殊字符: 中文测试 😀 \n\t")
    assert doc is not None

    # Update existing documents matching a condition
    db.update({"updated": True}, q.text == "特殊字符: 中文测试 😀 \n\t")
    assert db.get(q.text == "特殊字符: 中文测试 😀 \n\t")["updated"] is True

    # Remove documents matching a condition
    db.remove(q.text == "特殊字符: 中文测试 😀 \n\t")
    assert len(db) == 2

    db.close()

def test_bulk_operations_and_truncation(tmp_path):
    db = TinyDB(str(tmp_path / "db.json"))

    # Insert 800 records sequentially
    for i in range(800):
        db.insert({"id": i, "data": "bulk"})

    assert len(db) == 800

    # Retrieve all
    all_docs = db.all()
    assert len(all_docs) == 800

    # Update all records that possess a specific key using Query().exists()
    q = Query()
    db.update({"bulk_updated": True}, q.id.exists())

    # Verify update
    for doc in db.all():
        assert doc.get("bulk_updated") is True

    # Truncate
    db.truncate()
    assert len(db) == 0

    db.close()

def test_initialize_with_filepath_creates_or_opens_local_file(tmp_path):
    # Non-existent path: dynamically generated temporary path
    new_db_path = tmp_path / "tinydb_new_7734.json"
    db_new = TinyDB(str(new_db_path))
    db_new.insert({"init": True})
    db_new.close()

    # Verify file was created
    assert new_db_path.exists()

    # Existing path: pre-seeded with valid JSON
    existing_db_path = tmp_path / "existing.json"
    existing_db_path.write_text('{"_default": {"1": {"seeded": true}}}', encoding="utf-8")

    db_existing = TinyDB(str(existing_db_path))

    # Verify existing data is parsed without overwriting
    assert len(db_existing) == 1
    assert db_existing.get(doc_id=1) == {"seeded": True}

    db_existing.close()

def test_context_manager_exit_closes_underlying_file_resource(tmp_path):
    db_path = tmp_path / "scoped_lifecycle_db.json"

    with TinyDB(db_path) as db:
        db.insert({"test": "data"})

    with pytest.raises(ValueError, match="I/O operation on closed file"):
        db.insert({"test": "data"})

def test_initialize_with_invalid_or_restricted_path_raises_os_error(tmp_path):
    # 1. Attempting to open a directory as a database file raises IsADirectoryError/PermissionError
    with pytest.raises(OSError):
        TinyDB(str(tmp_path))

    # 2. Attempting to open a database file in a non-existent directory raises FileNotFoundError
    invalid_path = tmp_path / "missing_dir" / "db.json"
    with pytest.raises(OSError):
        TinyDB(str(invalid_path))

def test_insert_valid_document_returns_unique_id_and_persists_data(tmp_path):
    db = TinyDB(tmp_path / "db.json")
    payload = {
        "user": "alice_99",
        "metadata": {"age": 30, "tags": ["admin", "active"]},
        "score": 99.5,
        "is_active": True,
        "notes": None
    }

    doc_id = db.insert(payload)

    assert isinstance(doc_id, int)

    retrieved = db.get(doc_id=doc_id)
    assert retrieved == payload

def test_insert_unserializable_data_raises_type_error(tmp_path):
    db = TinyDB(tmp_path / "db.json")

    payload1 = {"timestamp": datetime.datetime(2024, 2, 29, 12, 0, 0)}
    with pytest.raises(TypeError):
        db.insert(payload1)

    payload2 = {"unique_ids": {1, 2, 3, 4}}
    with pytest.raises(TypeError):
        db.insert(payload2)

    payload3 = {"reference": object()}
    with pytest.raises(TypeError):
        db.insert(payload3)

    assert len(db) == 0

def test_insert_multiple_records_returns_unique_identifiers(tmp_path):
    db = TinyDB(tmp_path / "db.json")
    payloads = [
        {"id": "alpha", "count": 0},
        {"id": "beta", "active": True},
        {"id": "gamma", "tags": ["x", "y"]}
    ]

    doc_ids = db.insert_multiple(payloads)

    assert isinstance(doc_ids, list)
    assert len(doc_ids) == len(payloads)
    assert len(set(doc_ids)) == len(payloads)

    for doc_id, original_payload in zip(doc_ids, payloads):
        assert isinstance(doc_id, int)
        assert db.get(doc_id=doc_id) == original_payload

def test_insert_multiple_empty_iterable_returns_empty_list_and_does_not_mutate_state(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Insert a baseline record to ensure the file is created and has content
    db.insert({"baseline": "data"})

    initial_count = len(db.all())
    initial_size = os.path.getsize(db_path)

    # Test with empty list
    result_list = db.insert_multiple([])
    assert result_list == []
    assert len(db.all()) == initial_count
    assert os.path.getsize(db_path) == initial_size

    # Test with empty tuple
    result_tuple = db.insert_multiple(())
    assert result_tuple == []
    assert len(db.all()) == initial_count
    assert os.path.getsize(db_path) == initial_size


def test_search_matching_condition_returns_all_satisfying_records(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Pre-populate with exactly 5 records as specified
    db.insert_multiple([
        {"status": "active", "priority": 1},
        {"status": "active", "priority": 1},
        {"status": "active", "priority": 1},
        {"status": "inactive", "priority": 1},
        {"status": "inactive", "priority": 1},
    ])

    # Execute search
    results = db.search(Query().status == "active")

    # Assert exactly 3 records are returned
    assert len(results) == 3

    # Assert none of the returned records contain "status": "inactive"
    for record in results:
        assert record.get("status") == "active"
        assert record.get("status") != "inactive"


def test_search_unmatched_condition_returns_empty_list_without_error(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Pre-populate with a valid record
    db.insert({"role": "user"})

    # Test known key with non-existent value
    result_admin = db.search(Query().role == "admin")
    assert result_admin == []

    # Test completely non-existent key
    result_sales = db.search(Query().department == "sales")
    assert result_sales == []


def test_get_with_condition_returns_first_match_or_none(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Pre-populate sequentially
    db.insert({"category": "book", "title": "Alpha"})
    db.insert({"category": "book", "title": "Beta"})

    # Test condition that matches multiple records (should return the first match)
    result_book = db.get(Query().category == "book")
    assert result_book is not None
    assert result_book.get("title") == "Alpha"
    assert result_book.get("category") == "book"

    # Test condition that matches zero records (should return None)
    result_movie = db.get(Query().category == "movie")
    assert result_movie is None


def test_get_by_valid_and_invalid_doc_id_returns_record_or_none(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Insert data and capture the generated unique integer identifier
    inserted_data = {"user": "alice_89", "role": "admin", "active": True}
    doc_id = db.insert(inserted_data)

    # Test retrieval with the valid doc_id
    result_valid = db.get(doc_id=doc_id)
    assert result_valid is not None
    assert result_valid == inserted_data

    # Test retrieval with a highly improbable invalid doc_id
    result_invalid = db.get(doc_id=9999999)
    assert result_invalid is None

def test_update_with_condition_merges_data_and_adds_new_fields():
    db = TinyDB(storage=MemoryStorage)
    original_records = [
        {"id": 101, "status": "pending", "retries": 0},
        {"id": 102, "status": "pending", "retries": 0}
    ]
    inserted_ids = db.insert_multiple(original_records)

    update_payload = {"status": "complete", "processed_at": "2023-10-27T10:00:00Z"}
    condition = Query().status == 'pending'

    updated_ids = db.update(update_payload, condition)

    # Verify it returns the modified document IDs
    assert updated_ids == inserted_ids

    # Verify the exact merged state
    for doc_id in updated_ids:
        doc = db.get(doc_id=doc_id)
        assert doc["status"] == "complete"
        assert doc["processed_at"] == "2023-10-27T10:00:00Z"
        assert doc["retries"] == 0
        assert doc["id"] in (101, 102)

def test_update_with_unmatched_condition_returns_empty_list_and_preserves_state():
    db = TinyDB(storage=MemoryStorage)
    original_record = {"type": "config", "theme": "dark", "version": 2}
    db.insert(original_record)

    update_payload = {"theme": "light"}
    unmatched_condition = Query().type == 'legacy_config'

    updated_ids = db.update(update_payload, unmatched_condition)

    # Verify it returns an empty list
    assert updated_ids == []

    # Verify the database state is completely unmodified
    search_results = db.search(Query().type == 'config')
    assert len(search_results) == 1
    assert search_results[0] == original_record
    assert search_results[0]["theme"] == "dark"

def test_remove_by_condition_deletes_records_and_returns_former_ids():
    db = TinyDB(storage=MemoryStorage)
    inserted_records = [
        {"group": "A", "val": 10},
        {"group": "B", "val": 20},
        {"group": "A", "val": 30}
    ]
    inserted_ids = db.insert_multiple(inserted_records)

    condition = Query().group == 'A'

    removed_ids = db.remove(condition)

    # Verify it returns the exact integer IDs generated for the first and third records
    assert removed_ids == [inserted_ids[0], inserted_ids[2]]

    # Verify subsequent searches for those records return an empty collection
    assert db.search(condition) == []

    # Verify non-matching records are completely unaffected
    remaining = db.search(Query().group == 'B')
    assert len(remaining) == 1
    assert remaining[0]["val"] == 20

def test_remove_without_arguments_raises_runtime_error():
    db = TinyDB(storage=MemoryStorage)

    # Pre-populate the database with exactly 3 distinct records
    db.insert_multiple([
        {"record_id": 1, "name": "first"},
        {"record_id": 2, "name": "second"},
        {"record_id": 3, "name": "third"}
    ])

    assert len(db.all()) == 3

    # Call db.remove() with zero arguments and catch the RuntimeError
    with pytest.raises(RuntimeError):
        db.remove()

    # Verify via db.all() that exactly 3 records still exist
    assert len(db.all()) == 3

def test_truncate_removes_all_records_but_preserves_file(tmp_path):
    db_path = tmp_path / "db.json"
    db = TinyDB(db_path)

    # Pre-populate the database with 5 distinct records
    db.insert_multiple([{"record_id": i} for i in range(5)])

    # Verify len(db.all()) == 5
    assert len(db.all()) == 5

    # Execute db.truncate()
    db.truncate()

    # Verify len(db.all()) == 0
    assert len(db.all()) == 0

    # Verify os.path.exists(db_path) evaluates to True
    assert os.path.exists(db_path) is True

def test_search_with_mathematical_and_existence_conditions_returns_matching_records(tmp_path):
    db = TinyDB(tmp_path / "db.json")

    # Insert the records
    db.insert_multiple([
        {"name": "A", "score": 10},
        {"name": "B", "score": -50, "bonus": True},
        {"name": "C", "score": 0}
    ])

    q = Query()

    # Execute db.search(Query().bonus.exists()); must return exactly [{"name": "B", "score": -50, "bonus": True}]
    result_exists = db.search(q.bonus.exists())
    assert result_exists == [{"name": "B", "score": -50, "bonus": True}]

    # Execute db.search(Query().name == "C"); must return exactly [{"name": "C", "score": 0}]
    result_eq = db.search(q.name == "C")
    assert result_eq == [{"name": "C", "score": 0}]

    # Execute db.search(Query().score > 0); must return exactly [{"name": "A", "score": 10}]
    result_gt = db.search(q.score > 0)
    assert result_gt == [{"name": "A", "score": 10}]

def test_search_with_regex_condition_returns_pattern_matching_records(tmp_path):
    db = TinyDB(tmp_path / "db.json")

    # Insert the records
    db.insert_multiple([
        {"code": "SYS-123"},
        {"code": "APP-456"},
        {"code": "sys-789"}
    ])

    q = Query()

    # Execute db.search(Query().code.matches(r'^SYS-\d{3}$')); must return exactly [{"code": "SYS-123"}]
    result_exact = db.search(q.code.matches(r'^SYS-\d{3}$'))
    assert result_exact == [{"code": "SYS-123"}]

    # Execute db.search(Query().code.matches(r'^sys-\d{3}$', flags=re.IGNORECASE)); must return exactly [{"code": "SYS-123"}, {"code": "sys-789"}]
    result_ignorecase = db.search(q.code.matches(r'^sys-\d{3}$', flags=re.IGNORECASE))
    assert result_ignorecase == [{"code": "SYS-123"}, {"code": "sys-789"}]

def test_search_with_custom_callable_returns_records_passing_user_logic(tmp_path):
    db = TinyDB(tmp_path / "db.json")

    # Insert the records
    db.insert_multiple([
        {"tags": ["urgent", "backend"]},
        {"tags": ["frontend"]},
        {"tags": []}
    ])

    # Define a custom callable
    def is_complex_urgent(val):
        return isinstance(val, list) and len(val) > 1 and "urgent" in val

    q = Query()

    # Execute db.search(Query().tags.test(is_complex_urgent))
    result = db.search(q.tags.test(is_complex_urgent))

    # Must return exactly one record: [{"tags": ["urgent", "backend"]}]
    assert result == [{"tags": ["urgent", "backend"]}]

def test_query_any_evaluates_lists_correctly(tmp_path):
    db = TinyDB(tmp_path / "db.json")

    # Must insert a heterogeneous dataset
    db.insert_multiple([
        {"id": 1, "roles": ["admin", "editor"]},
        {"id": 2, "roles": ["viewer"]},
        {"id": 3, "roles": []},
        {"id": 4, "roles": ["editor", "contributor"]}
    ])

    q = Query()

    # Must test a direct value match: Query().roles.any("editor") must return exactly records 1 and 4
    result_direct = db.search(q.roles.any("editor"))
    assert result_direct == [
        {"id": 1, "roles": ["admin", "editor"]},
        {"id": 4, "roles": ["editor", "contributor"]}
    ]

    # Must test a nested query condition (Refactored to use dicts so Query has a path)
    db.insert({"id": 5, "scores": [{"score": 85}, {"score": 92}, {"score": 88}]})

    # Query().scores.any(Query().score >= 90) must successfully return record 5
    result_nested = db.search(q.scores.any(Query().score >= 90))
    assert result_nested == [{"id": 5, "scores": [{"score": 85}, {"score": 92}, {"score": 88}]}]

def test_search_missing_key_evaluates_false_without_error(tmp_path):
    db_file = tmp_path / "db.json"
    db = TinyDB(str(db_file))

    db.insert_multiple([
        {"username": "alice", "department": "engineering"},
        {"username": "bob"},
        {"username": "charlie", "department": "sales"}
    ])

    query = Query()
    results = db.search(query.department == "engineering")

    assert len(results) == 1
    assert results[0] == {"username": "alice", "department": "engineering"}
