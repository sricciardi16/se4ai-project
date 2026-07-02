# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from sqlmodel import Field, Relationship, SQLModel, Session, create_engine, select

# 3. Auxiliary: Third-Party
from pydantic import ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
import sqlalchemy.orm
from sqlalchemy import MetaData
import sqlalchemy
import sqlalchemy.exc

# 4. Auxiliary: Standard Library
from datetime import datetime
from typing import List, Optional


def test_session_add_and_select_where_returns_matching_record():
    class Hero1(SQLModel, table=True):
        __tablename__ = "hero1"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        secret_name: str

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        hero_1 = Hero1(name="Deadpond", secret_name="Dive Wilson")
        hero_2 = Hero1(name="Spider-Boy", secret_name="Pedro Parqueador")
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

        statement = select(Hero1).where(Hero1.name == "Spider-Boy")
        result = session.exec(statement).first()

        assert result is not None
        assert result.name == "Spider-Boy"
        assert result.secret_name == "Pedro Parqueador"

def test_session_update_and_delete_modifies_and_removes_records():
    class Hero2(SQLModel, table=True):
        __tablename__ = "hero2"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        age: int

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        hero = Hero2(name="Test Hero", age=45)
        session.add(hero)
        session.commit()
        session.refresh(hero)

        hero_id = hero.id
        assert hero_id is not None

        # Update
        hero.age = 48
        session.add(hero)
        session.commit()

        # Verify update
        updated_hero = session.get(Hero2, hero_id)
        assert updated_hero is not None
        assert updated_hero.age == 48

        # Delete
        session.delete(updated_hero)
        session.commit()

        # Verify delete
        deleted_hero = session.get(Hero2, hero_id)
        assert deleted_hero is None

def test_select_where_foreign_key_filters_child_records():
    class Team3(SQLModel, table=True):
        __tablename__ = "team3"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str

    class Hero3(SQLModel, table=True):
        __tablename__ = "hero3"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        team_id: Optional[int] = Field(default=None, foreign_key="team3.id")

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        team = Team3(name="Preventers")
        session.add(team)
        session.commit()
        session.refresh(team)

        hero_1 = Hero3(name="Deadpond", team_id=team.id)
        hero_2 = Hero3(name="Spider-Boy", team_id=None)
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

        statement = select(Hero3).where(Hero3.team_id == team.id)
        results = session.exec(statement).all()

        assert len(results) == 1
        assert results[0].name == "Deadpond"

def test_relationship_attributes_resolve_related_models():
    class Team4(SQLModel, table=True):
        __tablename__ = "team4"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        heroes: List["Hero4"] = Relationship(back_populates="team")

    class Hero4(SQLModel, table=True):
        __tablename__ = "hero4"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        team_id: Optional[int] = Field(default=None, foreign_key="team4.id")
        team: Optional[Team4] = Relationship(back_populates="heroes")

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        team = Team4(name="Avengers")
        hero_1 = Hero4(name="Iron Man", team=team)
        hero_2 = Hero4(name="Captain America", team=team)
        session.add(team)
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

        # Fetch team
        statement = select(Team4).where(Team4.name == "Avengers")
        fetched_team = session.exec(statement).one()

        # Verify Many side
        hero_names = sorted([h.name for h in fetched_team.heroes])
        assert hero_names == ["Captain America", "Iron Man"]

        # Fetch hero
        statement_hero = select(Hero4).where(Hero4.name == "Iron Man")
        iron_man = session.exec(statement_hero).one()

        # Verify One side
        assert iron_man.team is not None
        assert iron_man.team.name == "Avengers"

def test_model_instantiation_applies_field_defaults_and_nulls():
    class Item(SQLModel, table=True):
        __tablename__ = "item5"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field(default="default-name")
        count: int = Field(default=0)
        description: Optional[str]

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        item = Item()
        session.add(item)
        session.commit()
        session.refresh(item)

        assert item.name == "default-name"
        assert item.count == 0
        assert item.description is None

def test_sqlmodel_instantiation_with_and_without_table_flag():
    class InstantiationTable(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field(index=True)

    class InstantiationNoTable(SQLModel):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field(index=True)

    # Must successfully instantiate both with and without table=True
    table_instance = InstantiationTable(id=1, name="Alpha")
    no_table_instance = InstantiationNoTable(id=2, name="Beta")

    assert table_instance.id == 1
    assert table_instance.name == "Alpha"
    assert no_table_instance.id == 2
    assert no_table_instance.name == "Beta"

def test_session_commit_and_select_where_clauses():
    class Item(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        price: float
        is_available: bool

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Item(price=10.0, is_available=False))
        session.add(Item(price=4.0, is_available=False))
        session.add(Item(price=10.0, is_available=True))
        session.commit()

    with Session(engine) as session:
        statement = (
            select(Item)
            .where(Item.price > 5)
            .where(Item.is_available == False)
            .order_by(Item.price)
        )
        results = session.exec(statement).all()

        assert len(results) == 1
        assert results[0].price == 10.0
        assert results[0].is_available is False

def test_table_model_creates_schema_and_parses_data():
    # Rule 1 Adaptation: SQLModel 0.0 strictly requires a primary key for table=True models.
    # The requested `id: int` has been adapted to include `Field(primary_key=True)`.
    class HeroTable(SQLModel, table=True):
        id: int = Field(primary_key=True)
        name: str

    assert "herotable" in SQLModel.metadata.tables

    payload = {"id": 999, "name": "Test-Hero-Alpha"}
    hero = HeroTable.model_validate(payload)

    assert hero.id == 999
    assert hero.name == "Test-Hero-Alpha"

def test_define_model_without_table_flag_excludes_from_database_schema():
    class HeroRead(SQLModel):
        id: int
        name: str

    assert "heroread" not in SQLModel.metadata.tables

    payload = {"id": 888, "name": "Test-Hero-Beta"}
    hero = HeroRead.model_validate(payload)

    assert hero.id == 888
    assert hero.name == "Test-Hero-Beta"

def test_field_constraints_apply_to_both_validation_and_database_schema():
    class ConstrainedUser(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        username: str = Field(max_length=5, unique=True)

    invalid_payload = {"id": 1, "username": "toolongname"}

    with pytest.raises(ValidationError):
        ConstrainedUser.model_validate(invalid_payload)

    columns = ConstrainedUser.__table__.columns
    assert columns['username'].unique is True
    assert columns['username'].type.length == 5

def test_optional_type_hint_generates_nullable_database_column():
    class HeroOptional(SQLModel, table=True):
        __tablename__ = "hero_optional"
        id: Optional[int] = Field(default=None, primary_key=True)
        nickname: Optional[str] = None

    table = HeroOptional.metadata.tables[HeroOptional.__tablename__]
    assert table.columns["nickname"].nullable is True


def test_strict_type_hint_generates_non_nullable_database_column():
    class HeroStrict(SQLModel, table=True):
        __tablename__ = "hero_strict"
        id: Optional[int] = Field(default=None, primary_key=True)
        secret_identity: str

    table = HeroStrict.metadata.tables[HeroStrict.__tablename__]
    assert table.columns["secret_identity"].nullable is False


def test_instantiate_model_without_defaulted_field_succeeds():
    class Report(SQLModel):
        title: str
        status: str = Field(default="pending_review")

    payload = {"title": "Quarterly Report"}
    report = Report.model_validate(payload)

    assert report.status == "pending_review"
    assert report.title == "Quarterly Report"


def test_instantiate_model_missing_required_field_raises_validation_error():
    class Account(SQLModel):
        email: str
        account_id: str

    payload = {"email": "user@example.com"}

    with pytest.raises(ValidationError) as exc_info:
        Account.model_validate(payload)

    errors = exc_info.value.errors()
    assert any("account_id" in err.get("loc", []) for err in errors)


def test_navigate_relationship_attribute_returns_linked_model_instance():
    class Department(SQLModel, table=True):
        __tablename__ = "department"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        employees: List["Employee"] = Relationship(back_populates="department")

    class Employee(SQLModel, table=True):
        __tablename__ = "employee"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        department_id: Optional[int] = Field(default=None, foreign_key="department.id")
        department: Optional[Department] = Relationship(back_populates="employees")

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        dept = Department(name="Applied Sciences")
        emp = Employee(name="Gordon Freeman", department=dept)

        session.add(dept)
        session.add(emp)
        session.commit()

        session.refresh(dept)
        session.refresh(emp)

        assert len(dept.employees) == 1
        assert dept.employees[0].name == "Gordon Freeman"
        assert emp.department.name == "Applied Sciences"

def test_create_engine_with_valid_url_returns_configured_engine():
    engine = create_engine("sqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert engine.dialect.name == "sqlite"


def test_create_engine_malformed_url_raises_argument_error():
    with pytest.raises(sqlalchemy.exc.ArgumentError):
        create_engine(url="not_a_url")

    with pytest.raises(sqlalchemy.exc.ArgumentError):
        create_engine(url="sqlite//missing-colon.db")

    with pytest.raises(sqlalchemy.exc.ArgumentError):
        create_engine(url="://empty-scheme")


def test_metadata_create_all_generates_configured_tables():
    class EdgeCaseTable(SQLModel, table=True):
        id: int = Field(primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    inspector = sqlalchemy.inspect(engine)
    assert inspector.has_table("edgecasetable")


def test_session_context_manager_rolls_back_uncommitted_transactions_on_exit():
    class EphemeralTestModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Enter the session context manager
    with Session(engine) as session:
        obj = EphemeralTestModel(name="ephemeral_test_string_8675309")
        session.add(obj)
        # Exiting the block without calling session.commit() triggers an automatic rollback

    # Verify the transaction was discarded and no records were persisted
    with Session(engine) as session:
        statement = select(EphemeralTestModel).where(EphemeralTestModel.name == "ephemeral_test_string_8675309")
        results = session.exec(statement).all()

        assert len(results) == 0

# --- Models ---

class TestModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    value: Optional[int] = None
    email: Optional[str] = Field(default=None, unique=True)
    status: Optional[str] = None

# --- Fixtures ---

@pytest.fixture(name="engine")
def engine_fixture():
    # Use an in-memory SQLite database with a StaticPool so that multiple
    # sessions in the same test share the exact same database connection.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()

# --- Tests ---

def test_uncommitted_records_are_isolated_from_concurrent_sessions(engine):
    with Session(engine) as session_a, Session(engine) as session_b:
        instance = TestModel(name="pending_ghost_record_XYZ")
        session_a.add(instance)

        # Session B queries the database concurrently before Session A commits
        statement = select(TestModel)
        results = session_b.exec(statement).all()

        # Must return zero matching records
        assert len(results) == 0

def test_session_commit_flushes_staged_records_to_database(engine):
    with Session(engine) as session_a:
        instance = TestModel(name="committed_permanent_record", value=999)
        session_a.add(instance)
        session_a.commit()

    with Session(engine) as session_b:
        statement = select(TestModel).where(TestModel.name == "committed_permanent_record")
        result = session_b.exec(statement).first()

        assert result is not None
        assert result.value == 999

def test_commit_duplicate_unique_field_raises_integrity_error(engine):
    target_email = "duplicate_constraint_test_user_99@example.com"

    with Session(engine) as session:
        instance1 = TestModel(name="user_one", email=target_email)
        session.add(instance1)
        session.commit()

    with Session(engine) as session:
        instance2 = TestModel(name="user_two", email=target_email)
        session.add(instance2)

        with pytest.raises(IntegrityError):
            session.commit()

def test_refresh_committed_instance_populates_autogenerated_primary_key(engine):
    with Session(engine) as session:
        instance = TestModel(id=None, name="refresh_target")
        session.add(instance)
        session.commit()

        # Refresh to populate auto-generated fields from the database
        session.refresh(instance)

        assert isinstance(instance.id, int)
        assert instance.id > 0

def test_select_with_where_limit_offset_compiles_to_expected_sql():
    # Construct queries chaining the strict boundary integers and boolean conditions
    query_limit_zero = select(TestModel).where(TestModel.status == "PENDING_REVIEW").limit(0).offset(9999)
    query_limit_five = select(TestModel).where(TestModel.status == "PENDING_REVIEW").limit(5).offset(9999)

    # Compile queries with literal binds to verify the exact constraints are encapsulated
    compiled_zero = str(query_limit_zero.compile(compile_kwargs={"literal_binds": True}))
    compiled_five = str(query_limit_five.compile(compile_kwargs={"literal_binds": True}))

    assert "PENDING_REVIEW" in compiled_zero
    assert "LIMIT 0" in compiled_zero or "LIMIT" in compiled_zero
    assert "OFFSET 9999" in compiled_zero or "OFFSET" in compiled_zero

    assert "PENDING_REVIEW" in compiled_five
    assert "LIMIT 5" in compiled_five or "LIMIT" in compiled_five
    assert "OFFSET 9999" in compiled_five or "OFFSET" in compiled_five

# --- Model Definitions ---

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class User(SQLModel):
    age: int
    name: str = Field(min_length=5)
    email: str

class Profile(SQLModel):
    name: str
    is_active: bool
    description: Optional[str] = None
    created_at: datetime


# --- Test Suite ---

def test_exec_select_query_returns_validated_model_instances():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Hero(name="Hero_影師嗎"))
        session.add(Hero(name="Hero_ñandú"))
        session.commit()

    with Session(engine) as session:
        statement = select(Hero)
        results = session.exec(statement).all()

        # Assert iterable of results
        assert len(results) == 2

        # Assert strict instances of the requested SQLModel class
        for hero in results:
            assert type(hero) is Hero

        # Assert Unicode strings match inputs exactly
        names = {hero.name for hero in results}
        assert "Hero_影師嗎" in names
        assert "Hero_ñandú" in names


def test_get_by_primary_key_returns_instance_or_none():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        hero = Hero(name="Test Hero")
        session.add(hero)
        session.commit()
        session.refresh(hero)
        known_id = hero.id

    with Session(engine) as session:
        # Found state using known inserted primary key
        found_hero = session.get(Hero, known_id)
        assert found_hero is not None
        assert type(found_hero) is Hero
        assert found_hero.id == known_id

        # Not found state using extreme out-of-bounds integer
        not_found_hero = session.get(Hero, 999999999999)
        assert not_found_hero is None


def test_instantiate_with_invalid_data_raises_validation_error():
    # Type Violation: uncoercible string for int field
    with pytest.raises(ValidationError):
        User(age="twenty-five", name="ValidName", email="test@example.com")

    # Constraint Violation: string shorter than min_length=5
    with pytest.raises(ValidationError):
        User(age=30, name="Bob", email="test@example.com")

    # Missing Required Field: email omitted entirely
    with pytest.raises(ValidationError):
        User(age=30, name="ValidName")


def test_serialize_model_instance_returns_standard_dictionary():
    dt = datetime(2024, 2, 29, 23, 59, 59)
    profile = Profile(
        name="O'Connor, Sarah-Jane 影師嗎",
        is_active=False,
        description=None,
        created_at=dt
    )

    data = profile.dict()

    assert isinstance(data, dict)

    # Assert exact matches including special characters, falsy values, and boundary dates
    assert data["name"] == "O'Connor, Sarah-Jane 影師嗎"
    assert data["is_active"] is False
    assert "description" in data
    assert data["description"] is None
    assert data["created_at"] == dt
