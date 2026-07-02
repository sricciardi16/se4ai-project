Project: `image_message_embedder`


## 1. High-Level Goal
Implement a Python steganography library named `image_message_embedder` that allows users to hide and reveal secret messages within image files. The library must support two distinct steganographic methods:
1. **LSB (Least Significant Bit) Encoding:** Hiding standard and extended 8-bit ASCII strings inside the pixel data of lossless images (like PNGs). It must support both sequential encoding and scattered encoding using mathematical generators.
2. **EXIF Metadata Encoding:** Hiding raw byte strings inside the EXIF headers of JPEG images.

## 2. Module Structure
You must create the following exact package and module structure:
* `image_message_embedder/` (Root package)
  * `lsb/` (Subpackage or module)
    * `generators.py` (Module containing sequence generators)
  * `exifHeader.py` (Module for EXIF manipulation)

*(Note: `__init__.py` files should expose the necessary functions so they can be imported exactly as defined in the signatures below).*

---

## 3. Component: `image_message_embedder.lsb`

This module handles hiding and revealing text inside the Least Significant Bits of image pixels. 

### 3.1. `hide(image, message, generator=None, auto_convert_rgb=False)`

**Signature & Types:**
* `image`: `str` (file path) OR `PIL.Image.Image` object.
* `message`: `str` (The secret message, supporting 8-bit characters including extended Latin and punctuation).
* `generator`: `Iterator[int]`, optional (default `None`).
* `auto_convert_rgb`: `bool`, optional (default `False`).
* **Returns:** A *new* `PIL.Image.Image` object.

**Strict Behaviors & Rules:**
1. **Input Handling:** If `image` is a string, load it using `PIL.Image.open`. If it is already a `PIL.Image.Image` object, use it directly.
2. **Non-Destructive:** You MUST NOT modify the original file on disk. The function must return a new, savable `PIL.Image.Image` instance in memory.
3. **Palette Conversion:** If `auto_convert_rgb` is `True` and the image is in a non-RGB mode (e.g., mode `'P'` for Palette), you must convert the image to `'RGB'` or `'RGBA'` before processing.
4. **Message Serialization & Delimiter:** Convert the `message` string into a sequence of bits. You **must** append a consistent termination delimiter (e.g., a null byte `00000000` or a specific custom bit-sequence) to the end of the message bits so the `reveal` function knows when to stop reading.
5. **Bit Injection:** Flatten the image's color channels (R, G, B) into a 1D sequence. Replace the Least Significant Bit (LSB) of these color channels with the bits of the secret message.
6. **Generator Routing:** 
   * If `generator` is `None`, modify the color channels sequentially (index 0, 1, 2, 3...).
   * If `generator` is provided, use the integers yielded by the generator as the exact indices of the flattened color channels to modify.
7. **Exception - Capacity Exceeded:** If the total number of bits in the payload (message + delimiter) exceeds the available pixels/channels in the image, raise a standard `Exception`.
8. **Exception - Generator Exhausted:** If the provided `generator` stops yielding values before the entire payload (message + delimiter) is hidden, raise a standard `Exception`.

### 3.2. `reveal(image, generator=None)`

**Signature & Types:**
* `image`: `str` (file path) OR `PIL.Image.Image` object.
* `generator`: `Iterator[int]`, optional (default `None`).
* **Returns:** `str` (The decoded secret message).

**Strict Behaviors & Rules:**
1. **Input Handling:** Accept either a file path string or a `PIL.Image.Image` object.
2. **Bit Extraction:** Read the LSBs of the image's color channels. If `generator` is `None`, read them sequentially. If a `generator` is provided, read the LSBs at the specific indices yielded by the generator.
3. **Deserialization:** Reconstruct the bits into 8-bit characters.
4. **Termination:** Continuously read and decode until the exact termination delimiter (appended during `hide`) is encountered. Once found, stop reading and return the reconstructed string.
5. **Exception - Missing Payload / Wrong Generator:** If the function exhausts all available pixel data without ever finding the termination delimiter, it **must** raise an `IndexError`. This specifically handles cases where a user attempts to reveal a message from a pristine/empty image, or attempts to decode an image using the *wrong* generator (which results in reading garbage data and missing the delimiter).

---

## 4. Component: `image_message_embedder.lsb.generators`

This module provides mathematical sequence generators used to scatter the bits of the hidden message across the image, rather than storing them sequentially.

### 4.1. `eratosthenes()`
* **Returns:** A generator/iterator yielding `int`.
* **Strict Behavior:** Implement a prime number generator (e.g., using the Sieve of Eratosthenes). It must yield prime numbers in ascending order indefinitely (2, 3, 5, 7, 11, 13...).

### 4.2. `fibonacci()`
* **Returns:** A generator/iterator yielding `int`.
* **Strict Behavior:** Implement a Fibonacci sequence generator. It must yield Fibonacci numbers in ascending order indefinitely (1, 2, 3, 5, 8, 13...).

---

## 5. Component: `image_message_embedder.exifHeader`

This module handles hiding and revealing raw byte strings inside the EXIF metadata of JPEG images.

### 5.1. `hide(input_image_path, output_image_path, secret_message_bytes)`

**Signature & Types:**
* `input_image_path`: `str` (Path to the source JPEG).
* `output_image_path`: `str` (Path where the modified JPEG will be saved).
* `secret_message_bytes`: `bytes` (The raw byte string to hide).
* **Returns:** `None`

**Strict Behaviors & Rules:**
1. **EXIF Injection:** Read the JPEG from `input_image_path`. Embed the `secret_message_bytes` directly into the image's EXIF metadata (e.g., by injecting it into a specific EXIF tag like `UserComment`, or appending it safely within the EXIF segment).
2. **File Writing:** Save the resulting image to `output_image_path`.
3. **Isolation:** Ensure that writing to one output path does not cross-contaminate or alter the state of other files or subsequent function calls.

### 5.2. `reveal(image_path)`

**Signature & Types:**
* `image_path`: `str` (Path to the JPEG containing the hidden EXIF message).
* **Returns:** `bytes`

**Strict Behaviors & Rules:**
1. **EXIF Extraction:** Read the JPEG from `image_path`.
2. **Retrieval:** Locate the specific EXIF tag or segment used by the `hide` function, extract the hidden byte string, and return it exactly as it was provided.