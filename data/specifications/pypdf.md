Project: `docstruct`


## 1. High-Level Goal
Implement a Python library named `docstruct` for parsing, manipulating, merging, and writing PDF documents. The library must operate entirely on in-memory byte streams (file-like objects) and provide a robust object-oriented API for interacting with PDF pages, metadata, encryption, and text/image extraction.

## 2. Module Structure
You must create a root module named `docstruct` and a submodule for exceptions named `docstruct.errors`.

### Required Imports
The following imports must be available at the top level of `docstruct`:
*   `PdfReader`
*   `PdfWriter`
*   `PdfMerger`

The following imports must be available in `docstruct.errors`:
*   `PdfReadError`
*   `FileNotDecryptedError`

---

## 3. Exceptions (`docstruct.errors`)

### `PdfReadError`
*   **Behavior:** Raise this exception during the initialization of a `PdfReader` if the provided byte stream does not contain a valid PDF file (e.g., it is a plain text file, corrupted bytes, or lacks the PDF magic number).

### `FileNotDecryptedError`
*   **Behavior:** Raise this exception if a user attempts to access the `pages` attribute (including checking its length) or access a specific page (e.g., `reader.pages[0]`) on a `PdfReader` instance that has loaded an encrypted document but has not yet been successfully decrypted.

---

## 4. Core Classes & Public API

### `PdfReader`
**Goal:** Parse and read existing PDF byte streams.

*   **`__init__(self, stream: io.BytesIO)`**
    *   Accept a file-like bytes stream containing PDF data.
    *   Must immediately parse the stream. Raise `PdfReadError` if the stream is invalid or corrupted.
*   **`pages` (Property)**
    *   Return a sequence (e.g., a list) of `PageObject` instances representing the pages in the document.
    *   The length of this sequence must exactly match the number of pages in the PDF.
    *   *Rule:* If the document is encrypted and has not been decrypted, accessing this property MUST raise `FileNotDecryptedError`.
*   **`is_encrypted` (Property)**
    *   Return `True` if the loaded PDF is encrypted, otherwise return `False`.
*   **`decrypt(self, password: str) -> bool`**
    *   Attempt to decrypt the PDF using the provided password string.
    *   Return a truthy value (e.g., `True`) upon successful decryption.
    *   *Rule:* Once successfully decrypted, the `pages` property must become fully accessible.
*   **`metadata` (Property)**
    *   Return a dictionary-like object containing the PDF's metadata (e.g., `{"/Title": "...", "/Author": "..."}`).
    *   Must return `None` or an empty dict if no metadata exists, but must accurately preserve and expose all standard PDF info dictionary fields present in the file.

### `PdfWriter`
**Goal:** Construct, modify, and output PDF byte streams.

*   **`__init__(self)`**
    *   Initialize an empty PDF writer with zero pages.
*   **`pages` (Property)**
    *   Return a sequence of `PageObject` instances currently held in the writer.
*   **`add_page(self, page: PageObject)`**
    *   Append an existing `PageObject` to the writer.
    *   *Rule:* Pages must be stored and eventually written in the exact chronological order they were added.
*   **`add_blank_page(self, width: float, height: float) -> PageObject`**
    *   Create a new blank page with the specified physical dimensions.
    *   Append it to the writer's internal page list.
    *   Return the newly created `PageObject`.
*   **`append(self, reader: PdfReader, pages: list[int] = None)`**
    *   Append pages from a `PdfReader` instance into this writer.
    *   *Rule:* If `pages` is `None`, append all pages from the reader.
    *   *Rule:* If `pages` is provided (a list of integers), append *only* the pages at those specific indices, and append them in the *exact order* specified by the list.
*   **`encrypt(self, user_password: str, owner_password: str = None)`**
    *   Mark the output PDF to be encrypted.
    *   Must accept either a single positional string (acting as the password) or explicit keyword arguments for `user_password` and `owner_password`.
*   **`add_metadata(self, metadata: dict)`**
    *   Accept a dictionary of metadata key-value pairs (e.g., `{"/Title": "Test"}`) and embed them into the output PDF's info dictionary.
*   **`write(self, stream: io.BytesIO)`**
    *   Write the constructed PDF document to the provided file-like bytes stream.
    *   *Rule:* The output byte stream MUST strictly begin with the PDF magic number signature (`b"%PDF-"`).
    *   *Rule:* The output must be a perfectly valid PDF that can be immediately parsed by `PdfReader` without raising a `PdfReadError`.

### `PdfMerger`
**Goal:** Concatenate multiple PDF documents together.

*   **`__init__(self)`**
    *   Initialize an empty merger object.
*   **`append(self, document)`**
    *   Append an entire PDF document to the merger.
    *   *Rule:* This method must accept *both* a file-like bytes stream (`io.BytesIO`) AND an instantiated `PdfReader` object.
*   **`write(self, stream: io.BytesIO)`**
    *   Write the combined PDF document to the provided file-like bytes stream.
*   **`close(self)`**
    *   Close the merger and release any associated resources.

### `PageObject`
**Goal:** Represent a single page within a PDF document. (Note: This class is typically not instantiated directly by the user, but returned by `reader.pages` or `writer.add_blank_page`).

*   **`mediabox` (Property)**
    *   Return an object representing the physical dimensions of the page.
    *   This object must have `width` and `height` attributes accessible as floats.
*   **`rotation` (Property)**
    *   Return the current rotation angle of the page as an integer.
*   **`rotate(self, angle: int) -> 'PageObject'`**
    *   Apply a rotation to the page.
    *   *Rule:* Must return `self` (the page instance itself) to allow method chaining.
    *   *Rule:* Must update the `rotation` property.
    *   *Rule:* Must store negative angles *exactly* as provided (e.g., `-90` must be stored and returned as `-90`, do not normalize to `270`).
    *   *Rule:* Rotating a page MUST NOT alter the absolute `width` and `height` values of the page's `mediabox`.
*   **`get(self, key: str) -> Any`**
    *   Provide dictionary-like access to the underlying PDF dictionary properties.
    *   *Rule:* `page.get("/Rotate")` must return the exact integer angle applied via `rotate()`.
*   **`extract_text(self) -> str`**
    *   Extract and return all text content from the page as a continuous string.
    *   *Rule:* Must accurately include special characters and ASCII symbols.
    *   *Rule:* If the page is completely blank, return an empty string (`""`).
*   **`images` (Property)**
    *   Return an iterable (e.g., a list or tuple) of embedded image objects present on the page.
    *   *Rule:* The length of this iterable must exactly equal the number of embedded images on the page. If there are no images, it must return an empty iterable.
*   **`merge_page(self, source_page: 'PageObject')`**
    *   Overlay the content of the provided `source_page` onto this page.
    *   *Rule:* After execution, this page's text/content must reflect the combined state of both pages.
    *   *Rule:* The `source_page` object MUST remain completely unaffected and unmodified by this operation.