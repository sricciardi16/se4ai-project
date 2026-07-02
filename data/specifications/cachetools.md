Project: `policy_cache`


## 1. High-Level Goal
Develop a Python caching library named `policy_cache` that provides dictionary-like cache data structures with various eviction policies (FIFO, LFU, LRU, TTL) and function/method memoization decorators. 

## 2. Module Structure
You must create the following module structure:
* `policy_cache` (Main module exposing the public API)
* `policy_cache.keys` (Submodule for key-generation utilities)

## 3. Public API & Core Behaviors

### 3.1. Base Class: `Cache`
Implement a base class `Cache` that behaves like a dictionary but enforces a maximum size constraint.

* **Signature:** `__init__(self, maxsize, getsizeof=None)`
  * `maxsize`: The maximum allowed size of the cache. Can be negative (which effectively means a capacity of 0).
  * `getsizeof`: An optional callable that takes a cache value as an argument and returns its size (weight) as a number. If `None`, it must default to a function that always returns `1` for any item.
* **Properties:**
  * `currsize`: A property that returns the current total size of all items in the cache (the sum of `getsizeof(value)` for all stored values).
* **Methods & Behaviors:**
  * `__setitem__(self, key, value)`: Inserts or updates an item. 
    * **Rule:** Before storing, calculate the size of the new value using `getsizeof`. If this size is strictly greater than `maxsize`, you MUST raise a `ValueError`. (e.g., if `maxsize` is `-1` and default size is `1`, `1 > -1` triggers a `ValueError`).
    * **Rule:** If adding the new item exceeds `maxsize`, the cache must evict items according to its specific policy until `currsize <= maxsize`.
  * `__getitem__(self, key)`: Returns the value for the key. Raises `KeyError` if the key does not exist.
  * `__contains__(self, key)`: Returns `True` if the key exists, `False` otherwise.
  * `__len__(self)`: Returns the number of distinct keys currently in the cache.
  * `get(self, key, default=None)`: Returns the value for the key if it exists, otherwise returns `default`.
  * `clear(self)`: Removes all items from the cache and resets `currsize` to `0`.
  * `popitem(self)`: Removes and returns a single `(key, value)` tuple from the cache. 
    * **Rule:** If the cache is empty, this MUST raise a `KeyError`.

### 3.2. Eviction Policies (Inheriting from `Cache`)
Implement the following subclasses. They must inherit from `Cache` and implement specific eviction rules when `currsize` exceeds `maxsize`.

#### `FIFOCache`
* **Signature:** `__init__(self, maxsize, getsizeof=None)`
* **Eviction Rule:** When capacity is reached, evict the oldest inserted item (First-In, First-Out).

#### `LFUCache`
* **Signature:** `__init__(self, maxsize, getsizeof=None)`
* **Eviction Rule:** When capacity is reached, evict the item that has been accessed the least number of times (Least Frequently Used).

#### `LRUCache`
* **Signature:** `__init__(self, maxsize, getsizeof=None)`
* **Eviction Rule:** When capacity is reached, evict the Least Recently Used item (the item that has gone the longest without being accessed or updated).
* **State Rules:**
  * Accessing an item via `__getitem__` must update its status to Most Recently Used (MRU), preventing it from being evicted.
  * Updating an existing key via `__setitem__` must update its value, maintain the current cache length, and update its status to MRU.
  * `popitem()` must remove and return the Least Recently Used `(key, value)` pair.

#### `TTLCache`
* **Signature:** `__init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None)`
  * `maxsize`: Required positional argument.
  * `ttl`: Time-to-live in seconds (can be negative).
  * `timer`: A callable returning the current time as a float. Defaults to `time.monotonic`.
* **Behaviors & Rules:**
  * **Expiration Logic:** An item is considered expired if `timer() - insertion_time >= ttl`.
  * **Negative TTL:** If `ttl` is negative, items expire immediately upon insertion. `__setitem__` must not crash, but immediate subsequent access must treat the item as missing.
  * **Accessing Expired Items:** 
    * `__contains__` must return `False` for expired items.
    * `__getitem__` must raise a `KeyError` for expired items.
    * `get()` must return the `default` value for expired items.
  * **Overwriting:** Overwriting an existing key via `__setitem__` MUST refresh its insertion time to the current `timer()`, effectively resetting its TTL.
  * **Manual Expiration:** Implement an `expire(self)` method. When called, it must iterate through the cache, permanently delete all expired items, and accurately update `currsize`.

### 3.3. Decorators

#### `cached`
Implement a decorator named `cached` to memoize function results.
* **Signature:** `cached(cache, key=hashkey, lock=None)`
  * `cache`: A cache instance (e.g., `LRUCache`, a standard `dict`) or `None`.
  * `key`: A callable that takes the decorated function's arguments and returns a cache key. Defaults to `hashkey`.
  * `lock`: An optional threading lock (e.g., `threading.Lock()`).
* **Behaviors & Rules:**
  * **Memoization:** If the generated key exists in the cache, return the cached value without executing the underlying function. If it does not exist, execute the function, store the result in the cache, and return it.
  * **Bypass:** If `cache` is explicitly `None`, the decorator MUST bypass memoization entirely and execute the underlying function on every call.
  * **Recomputation:** If the underlying cache object is cleared or an item expires (raising `KeyError`), the decorator must catch this, re-execute the function, and cache the new result.
  * **Thread Safety:** If a `lock` is provided, the decorator must acquire the lock *only* when reading from or writing to the cache dictionary/object to prevent concurrent mutation corruption. 
    * *Crucial Distinction:* The lock MUST NOT wrap the execution of the underlying function itself (i.e., do not implement a dogpile lock). Multiple threads experiencing a cache miss simultaneously should be allowed to execute the underlying function concurrently.

#### `cachedmethod`
Implement a decorator named `cachedmethod` to memoize instance methods.
* **Signature:** `cachedmethod(cache, key=hashkey, lock=None)`
  * `cache`: A **callable** that takes the class instance (`self`) as its only argument and returns the cache object bound to that instance.
* **Behaviors & Rules:**
  * **Instance Binding:** The cache must be retrieved by calling the `cache` callable with the instance (e.g., `cache(self)`). This ensures that memoization is bound to the specific object instance, preventing cross-instance data leakage.
  * **Bypass:** If the callable returns `None` for the cache, memoization must be bypassed, and the method must execute normally on every call.

### 3.4. Key Generation (Submodule: `policy_cache.keys`)

#### `hashkey`
Implement a function `hashkey` that generates deterministic cache keys from function arguments.
* **Signature:** `hashkey(*args, **kwargs)`
* **Behaviors & Rules:**
  * **Deterministic Output:** It must return a composite `tuple` that deterministically represents the combination of `args` and `kwargs`. (e.g., structurally identical dictionaries passed as arguments must resolve to the same key if normalized).
  * **Lazy Hashing:** The function MUST NOT call Python's built-in `hash()` on the arguments during key generation. It must simply construct and return the tuple. 
  * **Unhashable Types:** If unhashable arguments (like `list`, `set`, or `dict`) are passed, `hashkey` must successfully return the tuple without crashing. A `TypeError` should ONLY be raised later if and when Python attempts to hash the resulting tuple (e.g., when the tuple is used as a dictionary key by the cache).