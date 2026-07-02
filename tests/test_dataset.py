# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import dataset

# 3. Auxiliary: Third-Party
from sqlalchemy.exc import ArgumentError, NoSuchModuleError
import sqlalchemy.exc

# 4. Auxiliary: Standard Library
import os


@pytest.fixture
def db():
    # Use an in-memory SQLite database for testing
    db = dataset.connect('sqlite:///:memory:')
    yield db

def test_insert_find_distinct_and_delete_rows(db):
    table = db['users']

    # Insert rows
    table.insert(dict(name='Alice', age=30, city='New York'))
    table.insert(dict(name='Bob', age=45, city='Los Angeles'))
    table.insert(dict(name='Charlie', age=50, city='New York'))

    # len()
    assert len(table) == 3

    # find_one
    alice = table.find_one(name='Alice')
    assert alice is not None
    assert alice['age'] == 30

    # find with advanced comparison operators passed as dictionaries
    older_users = list(table.find(age={">=": 40}))
    assert len(older_users) == 2
    assert set(u['name'] for u in older_users) == {'Bob', 'Charlie'}

    # distinct
    cities = list(table.distinct('city'))
    assert len(cities) == 2
    assert set(c['city'] for c in cities) == {'New York', 'Los Angeles'}

    # delete
    table.delete(city='New York')
    assert len(table) == 1

    # all
    remaining = list(table.all())
    assert len(remaining) == 1
    assert remaining[0]['name'] == 'Bob'

def test_update_upsert_and_create_index(db):
    table = db['accounts']

    # insert_many
    table.insert_many([
        dict(account_id='A1', balance=100, status='active'),
        dict(account_id='A2', balance=200, status='active')
    ])

    # update
    table.update(dict(account_id='A1', balance=150), keys=['account_id'])
    assert table.find_one(account_id='A1')['balance'] == 150

    # upsert - update existing
    table.upsert(dict(account_id='A2', balance=250, status='inactive'), keys=['account_id'])
    a2 = table.find_one(account_id='A2')
    assert a2['balance'] == 250
    assert a2['status'] == 'inactive'

    # upsert - insert new
    table.upsert(dict(account_id='A3', balance=300, status='active'), keys=['account_id'])
    assert len(table) == 3
    assert table.find_one(account_id='A3')['balance'] == 300

    # create_index and has_index
    table.create_index(['account_id'])
    assert table.has_index(['account_id'])

def test_database_transaction_commit_and_rollback(db):
    table = db['sales']

    # Initial data
    table.insert(dict(region='North', amount=100))
    table.insert(dict(region='South', amount=200))

    # Begin transaction and rollback
    db.begin()
    table.insert(dict(region='North', amount=300))
    table.insert(dict(region='East', amount=400))
    db.rollback()

    # Verify rollback with raw SQL query and GROUP BY
    result_rollback = list(db.query('SELECT region, SUM(amount) as total FROM sales GROUP BY region'))
    assert len(result_rollback) == 2
    totals_rollback = {row['region']: row['total'] for row in result_rollback}
    assert totals_rollback.get('North') == 100
    assert totals_rollback.get('South') == 200
    assert 'East' not in totals_rollback

    # Begin transaction and commit
    db.begin()
    table.insert(dict(region='North', amount=500))
    table.insert(dict(region='West', amount=600))
    db.commit()

    # Verify commit with raw SQL query and GROUP BY
    result_commit = list(db.query('SELECT region, SUM(amount) as total FROM sales GROUP BY region'))
    assert len(result_commit) == 3
    totals_commit = {row['region']: row['total'] for row in result_commit}
    assert totals_commit.get('North') == 600
    assert totals_commit.get('South') == 200
    assert totals_commit.get('West') == 600

def test_insert_many_bulk_inserts_rows(db):
    table = db['logs']

    initial_length = len(table)
    assert initial_length == 0

    rows_to_insert = [
        dict(event='login', user_id=1),
        dict(event='logout', user_id=1),
        dict(event='login', user_id=2),
        dict(event='click', user_id=2),
        dict(event='logout', user_id=2)
    ]

    table.insert_many(rows_to_insert)

    final_length = len(table)
    assert final_length == initial_length + len(rows_to_insert)
    assert final_length == 5

def test_find_one_returns_none_for_missing_record(db):
    table = db['employees']

    table.insert(dict(name='John', role='Developer'))
    table.insert(dict(name='Jane', role='Manager'))

    # Querying for a specifically non-existent value
    result = table.find_one(name="absent")

    assert result is None

@pytest.fixture
def db():
    """Provide an in-memory SQLite database for testing."""
    # dataset automatically handles connection pooling and setup
    database = dataset.connect('sqlite:///:memory:')
    yield database

@pytest.fixture
def table(db):
    """Provide a populated table for testing."""
    tbl = db['test_table']
    tbl.insert_many([
        {'name': 'a', 'value': 1},
        {'name': 'b', 'value': 2},
        {'name': 'c', 'value': 3},
        {'name': 'd', 'value': 4},
        {'name': 'e', 'value': 5},
        {'name': 'f', 'value': 6},
        {'name': 'g', 'value': 7},
        {'name': 'h', 'value': 8},
    ])
    return tbl

def test_find_supports_order_by_limit_and_offset(table):
    # Using _limit=3 and _offset=4 simultaneously to verify pagination
    # order_by='value' sorts ascending: 1, 2, 3, 4, 5, 6, 7, 8
    # offset 4 skips the first 4 rows (1, 2, 3, 4)
    # limit 3 takes the next 3 rows (5, 6, 7)
    results = list(table.find(order_by='value', _limit=3, _offset=4))

    assert len(results) == 3
    assert results[0]['value'] == 5
    assert results[1]['value'] == 6
    assert results[2]['value'] == 7

def test_all_yields_rows_with_auto_generated_id(table):
    results = table.all()

    # Verify it returns an iterator
    assert hasattr(results, '__iter__')
    assert hasattr(results, '__next__')

    rows = list(results)
    assert len(rows) == 8

    for row in rows:
        assert isinstance(row, dict)
        # Explicitly assert that the auto-generated "id" key exists
        assert 'id' in row
        assert isinstance(row['id'], int)

def test_delete_without_args_empties_table_rows(table):
    # delete with keyword arguments removes only matching rows
    table.delete(name='a')
    assert table.count() == 7

    table.delete()

    # Verify the row count drops to exactly 0 after truncation
    assert table.count() == 0

def test_drop_removes_table_from_database_tables_list(db, table):
    table_name = table.name

    # Must check the Database.tables property before the drop operation
    assert table_name in db.tables

    # Drop the table completely from the database
    table.drop()

    # Must check the Database.tables property after the drop operation
    assert table_name not in db.tables

def test_query_executes_raw_sql_with_bound_parameters(db, table):
    # Must use SQLAlchemy-style named parameters in the SQL string (e.g., :min_v)
    sql = f"SELECT * FROM {table.name} WHERE value >= :min_v ORDER BY value ASC"

    # Pass the corresponding value as a keyword argument (e.g., min_v=2)
    results = list(db.query(sql, min_v=2))

    assert len(results) == 7
    assert results[0]['value'] == 2
    assert results[-1]['value'] == 8

def test_distinct_returns_unique_column_values():
    db = dataset.connect("sqlite:///:memory:")
    table = db["test_table"]

    # Insert intentionally duplicated data
    table.insert({"c": "red", "other_data": 1})
    table.insert({"c": "red", "other_data": 2})
    table.insert({"c": "blue", "other_data": 3})

    # distinct() returns an iterator, so we convert to a list to verify
    results = list(table.distinct("c"))

    assert len(results) == 2
    assert {"c": "red"} in results
    assert {"c": "blue"} in results

def test_dataset_exposes_connect_callable():
    assert hasattr(dataset, "connect")
    assert callable(dataset.connect)

def test_connect_in_memory_sqlite_returns_database_with_tables():
    db = dataset.connect("sqlite:///:memory:")

    assert hasattr(db, "tables")
    # In dataset 1.6, db.tables is a property that returns a list of table names
    assert isinstance(db.tables, list)

def test_connect_invalid_scheme_raises_exception():
    # SQLAlchemy raises NoSuchModuleError when the dialect/scheme is unrecognized
    with pytest.raises(NoSuchModuleError):
        dataset.connect("not_a_valid_scheme://user:pass@host/db")

def test_connect_empty_string_raises_exception():
    # SQLAlchemy raises ArgumentError when the connection string is empty or unparseable
    with pytest.raises(ArgumentError):
        dataset.connect("")

def test_core_workflow_connect_insert_and_retrieve_all():
    db = dataset.connect("sqlite:///:memory:")
    table = db["items"]

    table.insert({"name": "x", "value": 1})

    results = list(table.all())
    assert len(results) == 1
    assert results[0]["name"] == "x"
    assert results[0]["value"] == 1


def test_connect_valid_url_reflects_existing_schema():
    db_url = "sqlite:///pre_populated_test.db"
    db_path = "pre_populated_test.db"

    # Ensure clean state before test
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        # Setup: Create the pre-existing database with complex table names
        setup_db = dataset.connect(db_url)
        setup_db["legacy_users_2023"].insert({"id": 1})
        setup_db["_internal_config_v2"].insert({"id": 1})
        setup_db.engine.dispose()

        # Test: Connect and reflect
        db = dataset.connect(db_url)
        tables = db.tables

        assert "legacy_users_2023" in tables
        assert "_internal_config_v2" in tables

        db.engine.dispose()
    finally:
        # Teardown: Clean up the file
        if os.path.exists(db_path):
            os.remove(db_path)


def test_connect_invalid_url_raises_exception():
    # Test malformed protocol
    with pytest.raises((sqlalchemy.exc.ArgumentError, sqlalchemy.exc.OperationalError)):
        dataset.connect("not_a_db_protocol://localhost/mydb")

    # Test unreachable host/port boundary
    with pytest.raises((sqlalchemy.exc.ArgumentError, sqlalchemy.exc.OperationalError, ModuleNotFoundError)):
        db = dataset.connect("postgresql://user:pass@256.256.256.256:99999/timeout_db")
        # SQLAlchemy lazy-loads connections; accessing .tables forces the engine to connect,
        # which will trigger the OperationalError (or ModuleNotFoundError if psycopg2 is missing).
        _ = db.tables


def test_access_nonexistent_table_stages_in_memory_without_database_creation():
    db = dataset.connect("sqlite:///:memory:")
    table_name = "phantom_staging_table_99_!@#"

    # Access via bracket notation
    table = db[table_name]

    # Assert it returns a valid Table object for staging
    assert isinstance(table, dataset.Table)
    assert table.name == table_name

    # Assert the table name does NOT appear in the database tables list yet
    assert table_name not in db.tables


def test_inspect_database_and_table_returns_current_schema_lists():
    db = dataset.connect("sqlite:///:memory:")

    # Explicitly initialize tables and columns
    db["users"].insert({
        "id": 1,
        "email_address": "test@example.com",
        "created_at_timestamp": "2023-01-01T12:00:00Z"
    })
    db["orders"].insert({"id": 1})

    # Inspect Database tables
    tables = db.tables
    assert "users" in tables
    assert "orders" in tables

    # Inspect Table columns
    users_columns = db["users"].columns
    assert "id" in users_columns
    assert "email_address" in users_columns
    assert "created_at_timestamp" in users_columns

@pytest.fixture
def db():
    """Provides a fresh in-memory SQLite database for each test."""
    return dataset.connect('sqlite:///:memory:')

def test_insert_record_with_new_keys_dynamically_alters_schema(db):
    table = db['dynamic_schema_table']

    # Establish initial table state: Contains only ['id', 'name']
    table.insert({"name": "Initial Record"})
    assert set(table.columns) == {'id', 'name'}

    # Inserted dictionary containing mixed data types
    payload = {
        "name": "Alice",
        "metadata_json": '{"role": "admin"}',
        "is_active": True,
        "login_count": 42
    }
    table.insert(payload)

    # Verify that the schema was dynamically altered
    current_columns = set(table.columns)
    assert 'metadata_json' in current_columns
    assert 'is_active' in current_columns
    assert 'login_count' in current_columns
    assert current_columns == {'id', 'name', 'metadata_json', 'is_active', 'login_count'}

def test_insert_single_record_returns_primary_key(db):
    table = db['single_insert_table']

    payload = {
        "name": "O'Connor-Smith",
        "age": 0,
        "is_active": False,
        "balance": -9999.99,
        "notes": ""
    }

    # Insert must return the auto-generated primary key (integer)
    pk = table.insert(payload)
    assert isinstance(pk, int)

    # Querying the table for that specific primary key
    record = table.find_one(id=pk)
    assert record is not None

    # Values must exactly match the original inserted record
    assert record["name"] == payload["name"]
    assert record["age"] == payload["age"]
    assert bool(record["is_active"]) is payload["is_active"]
    assert record["balance"] == payload["balance"]
    assert record["notes"] == payload["notes"]

def test_insert_many_records_saves_all_in_bulk(db):
    table = db['bulk_insert_table']

    # A list containing exactly 1005 dictionaries
    records = [{"batch_id": "B-001", "sequence": i} for i in range(1005)]

    # Submit using insert_many()
    table.insert_many(records)

    # Retrieve all records and verify total length
    all_records = list(table.all())
    assert len(all_records) == 1005

def test_update_existing_record_modifies_data_and_returns_count(db):
    table = db['update_table']

    initial_payload = {"username": "admin_user", "status": "active", "login_count": 5}
    table.insert(initial_payload)

    update_payload = {"username": "admin_user", "login_count": 6}

    # Update using identifying keys, must return integer count of modified rows
    modified_count = table.update(update_payload, keys=["username"])
    assert isinstance(modified_count, int)
    assert modified_count == 1

    # Querying must reflect newly updated values while leaving unspecified columns unaffected
    record = table.find_one(username="admin_user")
    assert record["login_count"] == 6
    assert record["status"] == "active"

def test_upsert_record_inserts_if_missing_and_updates_if_exists(db):
    table = db['upsert_table']

    first_payload = {"email": "test.user+1@example.com", "role": "user", "score": 10}

    # Insert if missing: returns new primary key
    pk = table.upsert(first_payload, keys=["email"])
    assert isinstance(pk, int)

    initial_row_count = len(list(table.all()))
    assert initial_row_count == 1

    second_payload = {"email": "test.user+1@example.com", "role": "superuser", "score": 10}

    # Update if exists
    update_result = table.upsert(second_payload, keys=["email"])

    assert update_result is True

    # Total row count must remain unchanged
    final_row_count = len(list(table.all()))
    assert final_row_count == initial_row_count

    # Verify the data was actually updated
    record = table.find_one(email="test.user+1@example.com")
    assert record["role"] == "superuser"
    assert record["score"] == 10

def test_insert_duplicate_unique_key_raises_integrity_error():
    db = dataset.connect('sqlite:///:memory:')

    # Setup: explicit table creation with UNIQUE constraint via raw SQL
    db.query("CREATE TABLE tenants (id INTEGER PRIMARY KEY, tenant_id TEXT UNIQUE, name TEXT)")
    table = db['tenants']

    # Payload 1 (Success)
    table.insert({"tenant_id": "T-9999", "name": "Alpha"})

    # Payload 2 (Failure trigger)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        table.insert({"tenant_id": "T-9999", "name": "Beta"})

def test_find_with_multiple_equality_filters_yields_matching_records():
    db = dataset.connect('sqlite:///:memory:')
    table = db['users']

    # Pre-populate with overlapping data
    table.insert({'status': 'active', 'role': 'admin'})
    table.insert({'status': 'active', 'role': 'user'})
    table.insert({'status': 'inactive', 'role': 'admin'})
    table.insert({'status': None, 'role': 'guest'})

    # Query with multiple equality filters (AND logic)
    results = list(table.find(status='active', role='admin'))
    assert len(results) == 1
    assert results[0]['status'] == 'active'
    assert results[0]['role'] == 'admin'

    # Query with None value to ensure IS NULL translation
    results_none = list(table.find(status=None))
    assert len(results_none) == 1
    assert results_none[0]['role'] == 'guest'

def test_find_one_with_unmatched_filters_returns_none():
    db = dataset.connect('sqlite:///:memory:')
    table = db['accounts']

    # Insert records known to match multiple criteria
    table.insert({'email': 'test1@example.com', 'is_active': True})
    table.insert({'email': 'test2@example.com', 'is_active': True})

    # Query using highly specific, non-existent string
    result_none = table.find_one(email='nonexistent_ghost_record@example.com')
    assert result_none is None

    # Query criteria known to match multiple records
    result_dict = table.find_one(is_active=True)
    assert isinstance(result_dict, dict)

def test_all_yields_entire_collection_as_dictionaries():
    db = dataset.connect('sqlite:///:memory:')
    table = db['scores']

    # Collection must contain exactly 3 distinct records with mixed data types
    table.insert({'id': 1, 'name': 'Alice', 'score': 99.5})
    table.insert({'id': 2, 'name': 'Bob', 'score': 0.0})
    table.insert({'id': 3, 'name': 'Charlie', 'score': -15.2})

    results = list(table.all())
    assert len(results) == 3
    for record in results:
        assert isinstance(record, dict)

def test_delete_with_filters_removes_matching_records_and_returns_boolean():
    db = dataset.connect('sqlite:///:memory:')
    table = db['items']

    # Pre-populate with 5 records
    for _ in range(3):
        table.insert({'category': 'delete_me'})
    for _ in range(2):
        table.insert({'category': 'keep_me'})

    # Invoke delete
    result = table.delete(category='delete_me')
    
    assert result is True

    # Query find to assert exactly 2 records remain (state mutation isolation)
    remaining = list(table.find(category='keep_me'))
    assert len(remaining) == 2

    # Ensure the deleted ones are actually gone
    deleted = list(table.find(category='delete_me'))
    assert len(deleted) == 0

def test_transaction_context_manager_rolls_back_on_exception():
    # Initialize an in-memory SQLite database
    db = dataset.connect('sqlite:///:memory:')
    table = db['transactions']

    # Enter the context manager and simulate a failure
    with pytest.raises(ValueError, match="Simulated failure"):
        with db:
            table.insert({'transaction_id': 'TXN-FAIL-9999', 'amount': 5000})
            raise ValueError("Simulated failure")

    # Query the table to ensure the transaction was rolled back
    result = table.find_one(transaction_id='TXN-FAIL-9999')
    assert result is None


def test_query_with_malicious_parameters_prevents_injection_and_yields_mappings():
    # Initialize an in-memory SQLite database
    db = dataset.connect('sqlite:///:memory:')
    users = db['users']

    # Setup Data
    users.insert({'username': 'alice'})
    users.insert({'username': "admin' OR '1'='1"})

    # Query String & Malicious Parameter
    query_string = "SELECT * FROM users WHERE username = :username"
    malicious_param = "admin' OR '1'='1"

    # Execute query with the first malicious parameter
    results = list(db.query(query_string, username=malicious_param))

    # Validation: Must yield only the single record where the username literally matches
    assert len(results) == 1
    assert isinstance(results[0], dict)
    assert results[0]['username'] == malicious_param

    # Secondary Malicious Parameter
    secondary_malicious_param = "'; DROP TABLE users; --"

    # Execute query with the secondary malicious parameter
    secondary_results = list(db.query(query_string, username=secondary_malicious_param))

    # Secondary Validation: Must yield zero results
    assert len(secondary_results) == 0

    # Prove the DROP TABLE command was neutralized by successfully querying the table
    all_users = list(db['users'].all())
    assert len(all_users) == 2
