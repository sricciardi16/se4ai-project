Project: `audio_metadata`


## 1. High-Level Goal
Implement a Python library named `audio_metadata` that parses, modifies, and saves audio metadata (specifically ID3 tags for MP3s and FLAC metadata) and extracts read-only audio stream information. The library must provide both a low-level, frame-accurate ID3 API and a high-level, simplified dictionary-like API.

## 2. Module Structure
You must implement the following module hierarchy:
* `audio_metadata` (Root module)
* `audio_metadata.mp3`
* `audio_metadata.flac`
* `audio_metadata.id3`
* `audio_metadata.easyid3`

---

## 3. Core API & File Handling (`audio_metadata`)

### `audio_metadata.File(path, easy=False)`
Implement a factory function that inspects a given file path and returns the appropriate format-specific object.
* **Detection:** Detect the file type based on its contents/headers. 
* **Returns:** 
  * An instance of `audio_metadata.mp3.MP3` for valid MP3 files.
  * An instance of `audio_metadata.flac.FLAC` for valid FLAC files.
  * `None` if the file is not a supported audio format (e.g., text files, images).
* **`easy` flag:** If `easy=True` is provided, the `tags` attribute of the returned object must use the simplified `EasyID3` interface (where all values are normalized to lists of strings).
* **Exceptions:** If the file is identified as an MP3 (e.g., via extension) but is corrupted and lacks valid MPEG frames (cannot sync), raise `audio_metadata.mp3.HeaderNotFoundError`.

### `audio_metadata.FileType` (Base Class)
Implement a base class for audio files (`MP3` and `FLAC` must inherit from this).
* **Attributes:**
  * `info`: A read-only object containing audio stream properties (see Section 4).
  * `tags`: A dictionary-like mapping of the file's metadata. If the file contains no metadata upon loading, this must be `None`.
* **Methods:**
  * `add_tags()`: If `tags` is `None`, initialize it as an empty, format-appropriate dictionary-like metadata object.
  * `save(filename=None)`: Persist the current state of `tags` to disk. 
    * If `filename` is `None`, overwrite the original file.
    * If `filename` is provided, write the modifications to that destination path (assuming a copy of the file already exists there) and leave the original file completely untouched.
    * *Rule:* Modifications to `tags` must remain entirely in memory and must not alter the physical file until `save()` is explicitly called.
  * `delete()`: Strip all metadata from the physical file, leaving the audio stream perfectly intact. Set the `tags` attribute to `None` (or an empty mapping).

---

## 4. Audio Stream Information

The `info` attribute on any `FileType` instance must return an object with the following read-only properties:
* `length` (float): The duration of the audio in seconds.
* `sample_rate` (int): The sample rate in Hz (e.g., 44100).
* `bitrate` (int): The bitrate in bits per second (e.g., 256000).
* `channels` (int): The number of audio channels (e.g., 2).

**Strict Calculation Rule:** 
For MP3 files, the `length` must be calculated using the exact formula: 
`length = (file_size - id3_size) * 8 / bitrate`

---

## 5. Low-Level ID3 API (`audio_metadata.id3`)

Implement a dictionary-like class `ID3` to handle raw ID3v2 frames.

### `audio_metadata.id3.ID3(path=None)`
* **Methods:**
  * `add(frame)`: Appends a frame object to the tag.
  * `getall(frame_id: str) -> list`: Returns a list of all frame objects matching the given 4-character ID (e.g., `"COMM"`, `"APIC"`).
  * `delall(frame_id: str)`: Removes all frames matching the given ID.
  * `save(path=None, v2_version=4)`: Writes the tags to the file. Must accept a `v2_version` keyword argument.
  * `__getitem__(key: str)`: Retrieves a specific frame. The key format depends on the frame type:
    * Standard text frames: `"FRAMEID"` (e.g., `"TIT2"`).
    * Complex frames with descriptions: `"FRAMEID:desc"` (e.g., `"APIC:Front Cover"`).
    * Complex frames with descriptions and languages: `"FRAMEID:desc:lang"` (e.g., `"COMM:Test Comment:eng"`).
* **Rules:**
  * Modifying a retrieved frame's attribute in memory (e.g., `tag["TIT2"].text = ["New"]`) and calling `save()` must successfully persist the change.
  * The class must support and preserve multiple frames of the exact same type (e.g., multiple `COMM` frames with different descriptions).

### Frames & Enums
Implement an `Encoding` enum/namespace containing at least `UTF8 = 3`.
Implement the following frame classes. They must store their initialization arguments as public attributes:
* **Text Frames (`TIT2`, `TPE1`, `TALB`, `TCON`)**: 
  * Signature: `__init__(self, encoding: int, text: list[str])`
  * Attributes: `encoding`, `text`
* **Comment Frame (`COMM`)**:
  * Signature: `__init__(self, encoding: int, lang: str, desc: str, text: list[str])`
  * Attributes: `encoding`, `lang`, `desc`, `text`
* **Picture Frame (`APIC`)**:
  * Signature: `__init__(self, encoding: int, mime: str, type: int, desc: str, data: bytes)`
  * Attributes: `encoding`, `mime`, `type`, `desc`, `data`

---

## 6. High-Level Simplified API (`audio_metadata.easyid3`)

Implement `EasyID3`, a dictionary-like class that abstracts raw ID3 frames into simple string keys.

### `audio_metadata.easyid3.EasyID3(path=None)`
* **Core Behaviors:**
  * Maps human-readable keys to underlying ID3 frames (e.g., `"title"` -> `TIT2`, `"artist"` -> `TPE1`, `"album"` -> `TALB`).
  * **Strict Type Rule:** Values assigned to or retrieved from `EasyID3` must *always* be lists of strings (e.g., `tag["title"] = ["My Title"]`).
  * Must preserve multiple strings in a list if provided (e.g., `["Artist 1", "Artist 2"]`).
  * Unset fields must be completely absent from the mapping (e.g., raising `KeyError` on access, returning `False` for `"artist" in tag`).
  * Calling `save()` on an unmodified `EasyID3` instance must safely preserve all existing tags without corrupting them.
* **Extensibility:**
  * Implement a class attribute `valid_keys` which is a dictionary of currently supported string keys.
  * Implement a class method `RegisterKey(key: str, getter: callable, setter: callable)`.
    * `getter(id3_instance, key)` must return a list of strings.
    * `setter(id3_instance, key, value_list)` must update the underlying raw ID3 frames.
    * The test suite will dynamically register a `"comment"` key using this method; your class must utilize these registered callbacks when getting/setting items.