# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from policy_cache import Cache, FIFOCache, LFUCache, LRUCache, TTLCache, cached, cachedmethod
from policy_cache.keys import hashkey

# 4. Auxiliary: Standard Library
import operator
import threading
import time


def test_lru_cache_evicts_least_recently_used_at_maxsize():
    cache = LRUCache(maxsize=2)

    # Insert items
    cache['a'] = 1
    cache['b'] = 2

    # Access an older item to update its MRU status
    _ = cache['a']

    # Insert a new item to trigger eviction
    cache['c'] = 3

    # Verify the correct un-accessed item ('b') was dropped
    assert 'b' not in cache
    assert 'a' in cache
    assert 'c' in cache
    assert cache['a'] == 1
    assert cache['c'] == 3

def test_ttl_cache_expires_items_after_ttl():
    cache = TTLCache(maxsize=10, ttl=0.2)

    cache['test_key'] = 'test_value'

    # Sleep for slightly longer than the TTL to guarantee expiration
    time.sleep(0.5)

    # Attempting to access an expired key using `in` should return False
    assert 'test_key' not in cache

    # Accessing it via cache[key] should raise a KeyError
    with pytest.raises(KeyError):
        _ = cache['test_key']

def test_cached_decorator_returns_memoized_result_on_subsequent_calls():
    tracker = {"executions": 0}

    @cached(cache={})
    def expensive_function(x):
        tracker["executions"] += 1
        return x * 10

    # First call - should execute
    result1 = expensive_function(5)
    assert result1 == 50
    assert tracker["executions"] == 1

    # Second call - should return cached result, execution count remains 1
    result2 = expensive_function(5)
    assert result2 == 50
    assert tracker["executions"] == 1

def test_cached_decorator_with_ttl_cache_recomputes_after_expiration():
    tracker = {"executions": 0}
    ttl_value = 0.2

    @cached(cache=TTLCache(maxsize=10, ttl=ttl_value))
    def time_sensitive_function(x):
        tracker["executions"] += 1
        return x + 5

    # Phase 1: Initial call (executes)
    result1 = time_sensitive_function(10)
    assert result1 == 15
    assert tracker["executions"] == 1

    # Phase 2: Immediate second call (cached)
    result2 = time_sensitive_function(10)
    assert result2 == 15
    assert tracker["executions"] == 1

    # Phase 3: Delayed third call after time.sleep(ttl + buffer) (executes again)
    time.sleep(ttl_value + 0.3)
    result3 = time_sensitive_function(10)
    assert result3 == 15
    assert tracker["executions"] == 2

def test_cached_decorator_accepts_custom_key_for_unhashable_arguments():
    tracker = {"executions": 0}

    def dict_normalizing_key(d):
        # Normalize dictionary by sorting its items so structurally identical
        # dicts resolve to the same cache key
        return hashkey(tuple(sorted(d.items())))

    @cached(cache={}, key=dict_normalizing_key)
    def process_payload(d):
        tracker["executions"] += 1
        return len(d)

    # Two dictionaries with the exact same key-value pairs but inserted in a different order
    dict_a = {"first": 1, "second": 2, "third": 3}
    dict_b = {"third": 3, "first": 1, "second": 2}

    # First call with dict_a
    res1 = process_payload(dict_a)
    assert res1 == 3
    assert tracker["executions"] == 1

    # Second call with dict_b - should hit the cache due to custom key normalization
    res2 = process_payload(dict_b)
    assert res2 == 3
    assert tracker["executions"] == 1

def test_lru_cache_maintains_length_on_existing_key_update():
    cache = LRUCache(maxsize=5)
    cache['key1'] = 'value1'
    cache['key2'] = 'value2'

    # Assert length before update
    assert len(cache) == 2

    # Update existing key
    cache['key1'] = 'new_value1'

    # Assert length after update remains unchanged
    assert len(cache) == 2
    assert cache['key1'] == 'new_value1'

def test_lru_cache_clear_removes_all_items():
    cache = LRUCache(maxsize=5)

    # Populate with multiple items
    cache['a'] = 1
    cache['b'] = 2
    cache['c'] = 3
    assert len(cache) == 3

    # Call clear
    cache.clear()

    # Verify length is 0 and keys are not present
    assert len(cache) == 0
    assert 'a' not in cache
    assert 'b' not in cache
    assert 'c' not in cache

def test_lru_cache_popitem_removes_and_returns_single_entry():
    cache = LRUCache(maxsize=5)
    cache['x'] = 100
    cache['y'] = 200

    initial_length = len(cache)

    # Call popitem
    key, value = cache.popitem()

    # Verify length reduced by 1
    assert len(cache) == initial_length - 1

    # Verify returned key is no longer in cache
    assert key not in cache

    # Verify returned value matches one of the originally inserted values
    assert value in (100, 200)

def test_ttl_cache_overwrite_refreshes_time_to_live():
    # Use a small TTL for fast testing
    cache = TTLCache(maxsize=5, ttl=0.2)

    # Insert a key
    cache['refresh_key'] = 'initial_data'

    # Wait for a fraction of the TTL
    time.sleep(0.15)

    # Overwrite the key (should refresh the TTL)
    cache['refresh_key'] = 'updated_data'

    # Wait again, pushing total time past the original 0.2s TTL
    time.sleep(0.15)

    # Verify it is still accessible because the timer was refreshed
    assert cache['refresh_key'] == 'updated_data'

def test_ttl_cache_raises_keyerror_on_expired_item_access():
    cache = TTLCache(maxsize=5, ttl=0.1)

    # Insert multiple items
    cache['item1'] = 'data1'
    cache['item2'] = 'data2'

    # Sleep past the TTL
    time.sleep(0.15)

    # Verify membership checks return False
    assert 'item1' not in cache
    assert 'item2' not in cache

    # Explicitly assert KeyError is raised on access
    with pytest.raises(KeyError):
        _ = cache['item1']

    with pytest.raises(KeyError):
        _ = cache['item2']

def test_cached_decorator_recomputes_if_underlying_cache_is_cleared():
    underlying_cache = Cache(maxsize=10)
    execution_counter = 0

    @cached(cache=underlying_cache)
    def expensive_function(x):
        nonlocal execution_counter
        execution_counter += 1
        return x * 2

    # First call: Cache miss, function executes
    result1 = expensive_function(5)
    assert result1 == 10
    assert execution_counter == 1

    # Second call: Cache hit, function does not execute
    result2 = expensive_function(5)
    assert result2 == 10
    assert execution_counter == 1

    # Clear the injected cache instance
    underlying_cache.clear()

    # Third call: Cache miss due to clear(), function executes again
    result3 = expensive_function(5)
    assert result3 == 10
    assert execution_counter == 2


def test_cache_negative_maxsize_raises_value_error_on_set():
    # Instantiation should not crash
    cache = Cache(maxsize=-1)

    # Setting an item should predictably fail because size (default 1) > maxsize (-1)
    with pytest.raises(ValueError):
        cache["test_key"] = "test_value"


def test_cache_rejects_item_larger_than_maxsize():
    # Cache with maxsize 100 and a getsizeof that always returns 200
    cache = Cache(maxsize=100, getsizeof=lambda x: 200)

    # Setting an item should raise ValueError because 200 > 100
    with pytest.raises(ValueError):
        cache["test_key"] = "test_value"


def test_popitem_empty_cache_raises_keyerror():
    empty_caches = [
        FIFOCache(maxsize=10),
        LFUCache(maxsize=10),
        LRUCache(maxsize=10)
    ]

    for cache in empty_caches:
        with pytest.raises(KeyError):
            cache.popitem()


def test_ttlcache_negative_maxsize_handled_safely():
    # Instantiation should not crash
    cache = TTLCache(maxsize=-1, ttl=10)

    # Setting an item should predictably fail because size (default 1) > maxsize (-1)
    with pytest.raises(ValueError):
        cache["test_key"] = "test_value"

def test_ttlcache_negative_ttl_handled_safely():
    cache = TTLCache(maxsize=100, ttl=-1)

    # Setting an item should not crash
    cache["test_key"] = "test_value"

    # Because TTL is negative, the item expires immediately and should raise KeyError on access
    with pytest.raises(KeyError):
        _ = cache["test_key"]

    # .get() should safely handle the missing/expired key and return None
    assert cache.get("test_key") is None

def test_cached_decorator_caches_function_results():
    cache = LRUCache(maxsize=10)

    @cached(cache)
    def f(x):
        return x

    assert f(42) == 42
    assert f("test_string") == "test_string"

def test_cachedmethod_decorator_caches_instance_methods():
    class MyClass:
        def __init__(self):
            self.cache = LRUCache(maxsize=10)

        @cachedmethod(lambda self: self.cache)
        def my_method(self, x):
            return x

    obj = MyClass()
    assert obj.my_method(99) == 99
    assert obj.my_method("instance_test") == "instance_test"

def test_cached_function_subsequent_calls_return_memoized_result_without_execution():
    counter = 0

    @cached(cache=LRUCache(maxsize=100))
    def process_data(s, n):
        nonlocal counter
        counter += 1
        return s, n

    # Invoke 3 times with the exact arguments
    res1 = process_data("complex_string_!@#", 42)
    res2 = process_data("complex_string_!@#", 42)
    res3 = process_data("complex_string_!@#", 42)

    assert res1 == ("complex_string_!@#", 42)
    assert res2 == ("complex_string_!@#", 42)
    assert res3 == ("complex_string_!@#", 42)

    # Counter must strictly equal 1, proving logic was bypassed on calls two and three
    assert counter == 1

def test_cached_with_none_cache_bypasses_memoization_and_executes_always():
    counter = 0

    @cached(cache=None)
    def bypass_func(s):
        nonlocal counter
        counter += 1
        return s

    # Called exactly 5 times with the argument ("bypass_test",)
    for _ in range(5):
        res = bypass_func("bypass_test")
        assert res == "bypass_test"

    # Counter must strictly equal 5, proving memoization was bypassed
    assert counter == 5

def test_cached_with_lock_guarantees_thread_safe_concurrent_access():
    cache = {}

    @cached(cache=cache, lock=threading.Lock())
    def expensive_operation(arg):
        time.sleep(0.01)
        return f"processed_{arg}"

    threads = []
    for _ in range(50):
        t = threading.Thread(target=expensive_operation, args=("concurrent_key",))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # The lock in cachetools protects the cache dictionary from concurrent mutation corruption.
    # It does NOT prevent concurrent function execution on cache misses (no dogpile lock).
    assert len(cache) == 1
    assert expensive_operation("concurrent_key") == "processed_concurrent_key"


def test_cachedmethod_binds_cache_to_instance_preventing_cross_instance_leakage():
    class Service:
        def __init__(self):
            self.cache = {}
            self.execution_counter = 0

        @cachedmethod(operator.attrgetter("cache"))
        def process(self, arg):
            self.execution_counter += 1
            return f"processed_{arg}"

    instance_a = Service()
    instance_b = Service()

    result_a = instance_a.process("shared_key")
    result_b = instance_b.process("shared_key")

    assert result_a == "processed_shared_key"
    assert result_b == "processed_shared_key"

    assert instance_a.execution_counter == 1
    assert instance_b.execution_counter == 1

    # State Mutation Pattern: clear instance_a's cache
    instance_a.cache.clear()

    assert len(instance_a.cache) == 0
    assert len(instance_b.cache) > 0  # instance_b's cache remains unaffected


def test_cachedmethod_with_none_instance_cache_bypasses_memoization():
    class NullCacheService:
        def __init__(self):
            self.cache = None
            self.execution_counter = 0

        @cachedmethod(operator.attrgetter("cache"))
        def process(self, arg):
            self.execution_counter += 1
            return f"processed_{arg}"

    instance = NullCacheService()

    for _ in range(4):
        instance.process("null_cache_test")

    assert instance.execution_counter == 4


def test_hashkey_with_mixed_arguments_generates_deterministic_composite_tuple():
    key1 = hashkey(1, "complex_string_影師嗎", (1, 2), is_active=True, metadata=None)
    key2 = hashkey(1, "complex_string_影師嗎", (1, 2), is_active=True, metadata=None)

    assert isinstance(key1, tuple)
    assert key1 == key2


def test_hashkey_with_unhashable_arguments_raises_type_error():
    # hashkey computes the hash lazily. The TypeError is raised when hash() is called.
    key1 = hashkey([1, 2, 3])
    with pytest.raises(TypeError):
        hash(key1)

    key2 = hashkey({"key": "value"})
    with pytest.raises(TypeError):
        hash(key2)

    key3 = hashkey({1, 2, 3})
    with pytest.raises(TypeError):
        hash(key3)

def test_lrucache_evicts_oldest_unaccessed_item_at_capacity():
    cache = LRUCache(maxsize=3)

    # Initial insertion sequence
    cache["A"] = 100
    cache["B"] = 200
    cache["C"] = 300

    # Trigger insertion
    cache["D"] = 400

    # Expected state
    assert "A" not in cache
    assert "B" in cache
    assert "C" in cache
    assert "D" in cache


def test_lrucache_item_access_updates_lru_status_preventing_eviction():
    cache = LRUCache(maxsize=3)

    # Initial insertion sequence
    cache["A"] = 100
    cache["B"] = 200
    cache["C"] = 300

    # Access trigger
    _ = cache["A"]

    # Capacity trigger insertion
    cache["D"] = 400

    # Expected state
    assert "B" not in cache
    assert "A" in cache
    assert "C" in cache
    assert "D" in cache


def test_lrucache_with_custom_getsizeof_calculates_capacity_by_weight():
    cache = LRUCache(maxsize=10, getsizeof=len)

    # First insertion
    cache["key1"] = "apple"
    assert cache.currsize == 5

    # Second insertion
    cache["key2"] = "banana"

    # Expected state: Total weight (11) exceeds 10, triggering immediate eviction of "key1"
    assert "key1" not in cache
    assert "key2" in cache
    assert cache.currsize == 6


def test_item_existence_after_ttl_duration_returns_false():
    # maxsize is a required positional argument in cachetools 5.0
    cache = TTLCache(maxsize=100, ttl=0.1)

    cache["ephemeral_session"] = {"user": "admin", "active": True}

    # Wait exactly 0.15 seconds
    time.sleep(0.15)

    assert ("ephemeral_session" in cache) is False
    assert cache.get("ephemeral_session", default="MISSING") == "MISSING"


def test_manual_expire_purges_only_expired_items_and_updates_size():
    class MockTimer:
        def __init__(self):
            self.current_time = 0.0

        def __call__(self):
            return self.current_time

    mock_timer = MockTimer()

    # maxsize is a required positional argument in cachetools 5.0
    cache = TTLCache(maxsize=100, ttl=10.0, timer=mock_timer)

    # At mock time t=0.0
    mock_timer.current_time = 0.0
    cache["item_A"] = "value_A"

    # At mock time t=5.0
    mock_timer.current_time = 5.0
    cache["item_B"] = "value_B"

    # Advance mock time to t=12.0
    mock_timer.current_time = 12.0

    # Invoke expire()
    cache.expire()

    # Expected state
    assert cache.currsize == 1
    assert "item_B" in cache
    assert "item_A" not in cache

def test_accessing_missing_or_expired_key_raises_keyerror():
    """
    Test that accessing a missing key or an expired key raises a KeyError.
    """
    # Missing key test
    lru_cache = LRUCache(maxsize=100)
    with pytest.raises(KeyError):
        _ = lru_cache["non_existent_key_9999"]

    # Expired key test
    ttl_cache = TTLCache(maxsize=100, ttl=0.01)
    ttl_cache["stale_data"] = "value"
    time.sleep(0.02)
    with pytest.raises(KeyError):
        _ = ttl_cache["stale_data"]

def test_negative_capacity_or_ttl_raises_errors_on_access_or_insertion():
    # Test LRUCache with maxsize=-1
    lru1 = LRUCache(maxsize=-1)
    with pytest.raises(ValueError):
        lru1["test_key"] = "test_value"

    # Test LRUCache with maxsize=-999.99
    lru2 = LRUCache(maxsize=-999.99)
    with pytest.raises(ValueError):
        lru2["test_key"] = "test_value"

    # Test TTLCache with valid maxsize=100 but ttl=-0.001
    ttl1 = TTLCache(maxsize=100, ttl=-0.001)
    ttl1["test_key"] = "test_value"
    with pytest.raises(KeyError):
        _ = ttl1["test_key"]

    # Test TTLCache with valid maxsize=100 but ttl=-50
    ttl2 = TTLCache(maxsize=100, ttl=-50)
    ttl2["test_key"] = "test_value"
    with pytest.raises(KeyError):
        _ = ttl2["test_key"]
