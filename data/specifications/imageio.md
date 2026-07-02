Project: `pixel_io`


## 1. High-Level Goal
Implement a Python library named `pixel_io` that provides a unified interface for reading, writing, and inspecting image and animation data (e.g., PNG, JPEG, GIF). The library must support various input/output targets including file paths, raw byte strings, and in-memory buffers. It must also support delegating encoding/decoding to specific backend plugins (such as Pillow).

## 2. Module Structure
*   **Root Package:** `pixel_io`
*   **Public API Module:** `pixel_io.v3`
    *   All public functions and classes defined below must be accessible via `import pixel_io.v3 as iio`.

## 3. Core Data Types & Concepts

### 3.1. URI (Uniform Resource Identifier) Support
All functions that accept a `uri` argument must seamlessly handle the following types:
*   `str`: Standard file system paths.
*   `pathlib.Path`: Object-oriented file system paths.
*   `bytes`: Raw encoded image data in memory.
*   `io.BytesIO`: In-memory byte buffers.
*   **Special String `"<bytes>"`**: When passed as the `uri` to write operations, it instructs the library to return the encoded image as a `bytes` object rather than writing to disk.

### 3.2. Image Properties Object
Implement a class or data class (e.g., `ImageProperties`) returned by the `improps` function. It must expose the following public attributes:
*   `shape` (`tuple`): The dimensions of the image/frame (e.g., `(height, width, channels)`). For animations, it must include spatial dimensions.
*   `dtype` (`numpy.dtype`): The NumPy data type of the image pixels (e.g., `np.uint8`).
*   `is_batch` (`bool`): A boolean indicating if the URI represents a batch/sequence of images (must be `False` for static images).

### 3.3. Context Manager Object
Implement a file-like object returned by `imopen`. 
*   When opened in read mode (`"r"`), it must expose a `read()` method that takes no arguments and returns a `numpy.ndarray`.
*   When opened in write mode (`"w"`), it must expose a `write(array)` method that takes a `numpy.ndarray` and writes it to the target.

---

## 4. Public API Functions

### `imread(uri, index=None, plugin=None, **kwargs)`
Read an image or animation from a URI into a NumPy array.
*   **Arguments:**
    *   `uri`: The source to read from (see Section 3.1).
    *   `index` (`int` or `None`): The specific frame to read. Default is `None`.
    *   `plugin` (`str`): The backend to use (e.g., `"pillow"`).
*   **Returns:** `numpy.ndarray`
*   **Behaviors & Rules:**
    *   If `index=None` and the URI is a multi-frame animation (like a GIF), return a single stacked array of all frames with the shape `(num_frames, height, width, channels)`.
    *   If `index` is an integer (e.g., `0` or `1`), return only that specific frame as an array with the shape `(height, width, channels)`.
    *   When reading a GIF, the returned array must always be decoded as RGB (3 channels), even if the original source was written as grayscale.
*   **Error Handling:**
    *   Raise `FileNotFoundError` if the URI is a string/path that does not exist.
    *   Raise `Exception` (or a subclass) if the URI is a `bytes` object containing invalid/non-image data.
    *   Raise `ValueError` or `OSError` if the file exists but contains corrupted media or an invalid header.
    *   Raise `IndexError` or `EOFError` if `index` is requested but is out of bounds for the provided media.

### `imwrite(uri, image, plugin=None, format=None, **kwargs)`
Write a NumPy array to a URI.
*   **Arguments:**
    *   `uri`: The destination to write to (see Section 3.1).
    *   `image` (`numpy.ndarray`): The pixel data to write.
    *   `plugin` (`str`): The backend to use (e.g., `"pillow"`).
    *   `format` (`str`): The image format (e.g., `"PNG"`, `"GIF"`, `"JPEG"`).
    *   `**kwargs`: Additional encoding parameters.
*   **Returns:** `bytes` if `uri` is `"<bytes>"`, otherwise `None`.
*   **Behaviors & Rules:**
    *   If `format` is not provided, infer the format automatically from the file extension in the `uri`.
    *   If `uri` is exactly the string `"<bytes>"`, do not write to disk. Instead, encode the image in memory and return the resulting `bytes` object.
    *   Pass any arbitrary `**kwargs` (e.g., `quality=10`) directly to the underlying encoder. These parameters must actively affect the output (e.g., lowering quality must result in a smaller file size).
    *   Support writing 3D arrays `(frames, height, width)` to multi-frame formats like GIF.
*   **Error Handling:**
    *   Raise `ValueError`, `IndexError`, `OSError`, or `KeyError` if the provided `image` array has an incompatible shape (e.g., a 1D array, or an array with 5 color channels).
    *   Raise `PermissionError` if the destination `uri` is read-only or lacks write permissions.

### `imiter(uri, plugin=None, **kwargs)`
Create an iterator that yields individual frames of an image or animation.
*   **Arguments:**
    *   `uri`: The source to read from.
    *   `plugin` (`str`): The backend to use.
*   **Returns:** A Python `Iterator` yielding `numpy.ndarray` objects.
*   **Behaviors & Rules:**
    *   For multi-frame media (e.g., GIFs), yield each frame sequentially as a separate array.
    *   For static images, yield exactly one array, and then raise `StopIteration` on subsequent calls to `next()`.
    *   The first frame yielded by `imiter` must be perfectly identical in shape, dtype, and values to the array returned by `imread(uri, index=0)`.
*   **Error Handling:**
    *   Raise `StopIteration`, `OSError`, or `EOFError` immediately on the first `next()` call if the media is empty or contains only a partial/invalid header.

### `improps(uri, index=None, plugin=None, **kwargs)`
Extract image properties and metadata without decoding the pixel data.
*   **Arguments:**
    *   `uri`: The source to inspect.
    *   `index` (`int` or `None`): The specific frame to inspect.
    *   `plugin` (`str`): The backend to use.
*   **Returns:** An `ImageProperties` object (see Section 3.2).
*   **Behaviors & Rules:**
    *   **Performance Constraint:** This function MUST NOT decode the actual pixel data. It must parse only the file headers. Execution time must be strictly less than 0.5 seconds even for massive images (e.g., 10,000 x 10,000 pixels).
*   **Error Handling:**
    *   Raise `ValueError` or `OSError` if the file header is unparseable or corrupt.
    *   Raise `ValueError`, `EOFError`, or `IndexError` if an `index` is requested (e.g., `index=1` or `index=-1`) on a format that does not support multiple frames (like BMP).

### `immeta(uri, plugin=None, **kwargs)`
Extract detailed metadata from the image.
*   **Arguments:**
    *   `uri`: The source to inspect.
    *   `plugin` (`str`): The backend to use.
*   **Returns:** `dict`
*   **Behaviors & Rules:**
    *   The returned dictionary must contain at least a `"mode"` key representing the color mode of the image.

### `imopen(uri, mode, plugin=None, **kwargs)`
A context manager for opening an image resource for reading or writing.
*   **Arguments:**
    *   `uri`: The source or destination.
    *   `mode` (`str`): `"r"` for reading, `"w"` for writing.
    *   `plugin` (`str`): The backend to use.
*   **Returns:** A Context Manager yielding the object described in Section 3.3.
*   **Behaviors & Rules:**
    *   Must support the `with` statement.
    *   Must properly close/release the underlying file or buffer when the context exits.