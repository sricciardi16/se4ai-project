Excellent. Since you have deep factual knowledge of this repository, I need you to define its "Core Essential Public API Contract" strictly from the perspective of an end-user consuming the library.

I do NOT want implementation details or hints on how it is built. I want a highly detailed reference of exactly how the core features are USED.

CRITICAL FILTER: 
- Focus ONLY on the primary, most commonly used features (the top 5-10 elements that define the library).
- Do NOT include legacy functions.
- Do NOT include obscure utilities or advanced extension/plugin classes.
- Do NOT include internal implementation details or private helpers (starting with `_`).

Please provide the output in the following structured format:

### 1. Primary Imports
(Exactly how does a user import the essential elements?)

### 2. Detailed Function Usage

For the essential module-level functions, provide:
* **Exact Call Signature:** (Include ALL arguments, keyword arguments, default values, and Python Type Hints)
* **Return Type:** (What exactly does the user get back? Include Type Hints)
* **Usage Behavior:** (How do the arguments change the output? What is the user trying to achieve by calling this?)
* **Edge Cases:** (How does it handle empty inputs, None, or invalid types?)

### 3. Detailed Class & Method Usage
For the essential public classes (only if the user MUST instantiate it for standard usage), provide:
* **Instantiation Signature:** (Exactly how does the user create the object? Include all arguments, defaults, and Type Hints)
* **Method Usage:** (For each essential method: exact signature with Type Hints, return type, and what it does for the user)
* **Public Attributes:** (Any variables the user is expected to read or modify directly)

### 4. Exceptions & Constants
* List any specific Exceptions the library raises that a user is expected to catch (`except`).
* List any essential public constants the user needs to pass as arguments.

### 5. Comprehensive Usage Example
(Provide a clear, multi-line Python script showing a user combining these elements to solve the primary problem the library was built for).