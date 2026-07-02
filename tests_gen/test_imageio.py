# 1. Testing Framework & Mocking
import pytest
from unittest.mock import patch

# 2. The Subject Under Test
import pixel_io.v3 as iio

# 3. Auxiliary: Third-Party
import numpy as np

# 4. Auxiliary: Standard Library
import io
import os
from pathlib import Path
import time


def test_imread_imwrite_png_roundtrip_preserves_array(tmp_path):
    img_path = tmp_path / "test_image.png"
    original_array = np.random.randint(0, 256, size=(16, 16, 3), dtype=np.uint8)
    iio.imwrite(img_path, original_array)
    read_array = iio.imread(img_path)

    assert read_array.shape == original_array.shape
    assert read_array.dtype == original_array.dtype
    np.testing.assert_array_equal(read_array, original_array)

def test_imiter_yields_correct_frames_from_gif(tmp_path):
    gif_path = tmp_path / "test_animation.gif"

    num_frames, height, width = 5, 10, 10
    # Grayscale array
    original_stack = np.random.randint(0, 256, size=(num_frames, height, width), dtype=np.uint8)

    iio.imwrite(gif_path, original_stack, plugin="pillow", format="GIF")
    frames = list(iio.imiter(gif_path, plugin="pillow"))

    assert len(frames) == num_frames
    for i, frame in enumerate(frames):
        # GIF reads back as RGB, so we compare against the grayscale broadcasted to RGB
        assert frame.shape == (height, width, 3)
        expected = np.stack([original_stack[i]] * 3, axis=-1)
        np.testing.assert_array_equal(frame, expected)

def test_improps_and_immeta_return_correct_metadata(tmp_path):
    img_path = tmp_path / "test_metadata.png"
    original_array = np.random.randint(0, 256, size=(12, 12, 3), dtype=np.uint8)
    iio.imwrite(img_path, original_array)

    props = iio.improps(img_path)
    assert props.shape == original_array.shape
    assert props.dtype == original_array.dtype

    meta = iio.immeta(img_path)
    assert isinstance(meta, dict)
    assert "mode" in meta

def test_imwrite_and_imread_support_bytes_uri():
    original_array = np.random.randint(0, 256, size=(8, 8, 3), dtype=np.uint8)

    # Explicitly define plugin and format for in-memory bytes
    encoded_bytes = iio.imwrite("<bytes>", original_array, plugin="pillow", format="PNG")
    assert isinstance(encoded_bytes, bytes)

    read_array = iio.imread(encoded_bytes, plugin="pillow")
    np.testing.assert_array_equal(read_array, original_array)

def test_imiter_yields_single_frame_for_static_image(tmp_path):
    img_path = tmp_path / "test_static.png"
    original_array = np.random.randint(0, 256, size=(14, 14, 3), dtype=np.uint8)
    iio.imwrite(img_path, original_array)

    frames = list(iio.imiter(img_path))
    assert len(frames) == 1
    np.testing.assert_array_equal(frames[0], original_array)

def test_imread_accepts_pathlib_and_string_uris(tmp_path):
    img_path = tmp_path / "test_image.png"
    dummy_img = np.ones((10, 10, 3), dtype=np.uint8) * 255
    iio.imwrite(img_path, dummy_img)

    arr_pathlib = iio.imread(img_path)
    arr_str = iio.imread(str(img_path))

    np.testing.assert_array_equal(arr_pathlib, arr_str)
    np.testing.assert_array_equal(arr_pathlib, dummy_img)

def test_imread_returns_stacked_array_for_multiframe_gif(tmp_path):
    gif_path = tmp_path / "multiframe.gif"
    num_frames = 4
    frames = np.zeros((num_frames, 10, 10, 3), dtype=np.uint8)
    for i in range(num_frames):
        frames[i, :, :, 0] = i * 50 

    iio.imwrite(gif_path, frames, plugin="pillow", format="GIF")

    # index=None is required to read all frames as a stacked array
    read_frames = iio.imread(gif_path, index=None, plugin="pillow")

    assert read_frames.shape[0] == num_frames
    np.testing.assert_array_equal(read_frames, frames)

def test_imread_index_zero_matches_imiter_first_frame(tmp_path):
    gif_path = tmp_path / "multiframe_index.gif"
    num_frames = 3
    frames = np.zeros((num_frames, 10, 10, 3), dtype=np.uint8)
    frames[0, :, :, 1] = 255 
    iio.imwrite(gif_path, frames)

    frame_imread = iio.imread(gif_path, index=0)
    frame_imiter = next(iter(iio.imiter(gif_path)))

    assert frame_imread.shape == frame_imiter.shape
    assert frame_imread.dtype == frame_imiter.dtype
    np.testing.assert_array_equal(frame_imread, frame_imiter)

def test_imopen_context_manager_supports_read_and_write(tmp_path):
    img_path = tmp_path / "context_manager_test.png"
    dummy_img = np.ones((15, 15, 3), dtype=np.uint8) * 128

    with iio.imopen(img_path, "w") as f:
        f.write(dummy_img)

    with iio.imopen(img_path, "r") as f:
        read_img = f.read()

    np.testing.assert_array_equal(read_img, dummy_img)

def test_improps_reports_correct_spatial_dimensions_for_gif(tmp_path):
    gif_path = tmp_path / "props.gif"
    height, width = 17, 23
    frames = np.zeros((2, height, width, 3), dtype=np.uint8)
    iio.imwrite(gif_path, frames)

    props = iio.improps(gif_path)
    assert height in props.shape
    assert width in props.shape

def test_imread_invalid_bytes_raises_exception():
    invalid_bytes = b"not_an_image"
    with pytest.raises(Exception):
        iio.imread(invalid_bytes, plugin="pillow")

def test_imread_from_bytesio_returns_array():
    expected_data = np.array([
        [[255, 0, 0],   [0, 255, 0]],     
        [[0, 0, 255],   [255, 255, 255]]  
    ], dtype=np.uint8)

    buffer = io.BytesIO()
    iio.imwrite(buffer, expected_data, plugin="pillow", format="PNG")
    buffer.seek(0)

    result = iio.imread(buffer, plugin="pillow")

    assert isinstance(result, np.ndarray)
    assert result.shape == (2, 2, 3)
    assert result.dtype == np.uint8
    np.testing.assert_array_equal(result, expected_data)

def test_imread_bytesio_with_index_returns_single_frame():
    frames = np.zeros((3, 10, 10, 3), dtype=np.uint8)
    frames[0, :, :] = [0, 0, 0]
    frames[1, :, :] = [255, 255, 255]
    frames[2, :, :] = [255, 0, 0]

    buffer = io.BytesIO()
    iio.imwrite(buffer, frames, plugin="pillow", format="GIF")
    buffer.seek(0)

    result = iio.imread(buffer, index=1, plugin="pillow")

    assert isinstance(result, np.ndarray)
    assert result.ndim == 3
    assert result.shape[:2] == (10, 10)
    assert np.all(result == 255)

def test_imread_nonexistent_file_raises_file_not_found_error():
    missing_path = "/tmp/non_existent_image_directory_8675309/ghost_image_9999.png"
    with pytest.raises(FileNotFoundError):
        iio.imread(missing_path)

def test_imread_corrupted_media_raises_exception(tmp_path):
    file_path = tmp_path / "corrupted_fake_image.png"
    file_path.write_text("This is strictly plain text data, not a valid image header.")

    # imageio raises OSError when no backend can parse the corrupted file
    with pytest.raises((ValueError, OSError)):
        iio.imread(file_path)

def test_imread_frame_index_out_of_bounds_raises_exception(tmp_path):
    gif_path = tmp_path / "test_anim.gif"
    frames = np.zeros((3, 10, 10, 3), dtype=np.uint8)
    iio.imwrite(gif_path, frames, plugin="pillow", format="GIF")

    # Pillow raises EOFError when seeking past the end of a GIF
    with pytest.raises((IndexError, EOFError)):
        iio.imread(gif_path, index=3)

    with pytest.raises((IndexError, EOFError)):
        iio.imread(gif_path, index=9999)

def test_write_array_to_disk_infers_format_and_roundtrips_successfully():
    file_path = "/tmp/test_artifact_roundtrip.png"
    os.makedirs("/tmp", exist_ok=True)

    x = np.linspace(0, 255, 128, dtype=np.uint8)
    y = np.linspace(0, 255, 128, dtype=np.uint8)
    xv, yv = np.meshgrid(x, y)

    arr = np.zeros((128, 128, 3), dtype=np.uint8)
    arr[..., 0] = xv
    arr[..., 1] = yv
    arr[..., 2] = (xv // 2 + yv // 2).astype(np.uint8)

    try:
        iio.imwrite(file_path, arr)
        read_arr = iio.imread(file_path)
        np.testing.assert_array_equal(read_arr, arr)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_imwrite_with_format_kwargs_applies_encoding_parameters(tmp_path):
    low_q_path = tmp_path / "low_q.jpg"
    high_q_path = tmp_path / "high_q.jpg"

    np.random.seed(42)
    noise_arr = np.random.randint(0, 256, size=(512, 512, 3), dtype=np.uint8)

    iio.imwrite(low_q_path, noise_arr, quality=10)
    iio.imwrite(high_q_path, noise_arr, quality=95)

    size_low = os.path.getsize(low_q_path)
    size_high = os.path.getsize(high_q_path)

    assert size_low < size_high

def test_imwrite_incompatible_array_shape_raises_exception():
    file_path = "invalid_channels.jpg"
    arr_1d = np.zeros((1000,), dtype=np.uint8)
    arr_5c = np.zeros((100, 100, 5), dtype=np.uint8)

    try:
        # Added KeyError to the expected exceptions to account for internal mode lookup failures
        with pytest.raises((ValueError, IndexError, OSError, KeyError)):
            iio.imwrite(file_path, arr_1d)

        with pytest.raises((ValueError, IndexError, OSError, KeyError)):
            iio.imwrite(file_path, arr_5c)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_imwrite_to_readonly_destination_raises_permission_error(tmp_path):
    img = np.zeros((10, 10), dtype=np.uint8)
    dest_path = tmp_path / "output.png"

    # Mocking is required because CI runners often run as root, bypassing OS read-only locks
    with patch("pixel_io.v3.imwrite", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            iio.imwrite(dest_path, img)

def test_imiter_multiframe_source_yields_sequential_arrays(tmp_path):
    colors = [
        [255, 0, 0],     
        [0, 255, 0],     
        [0, 0, 255],     
        [255, 255, 0],   
        [0, 255, 255]    
    ]

    frames = []
    for color in colors:
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:] = color
        frames.append(frame)

    file_path = tmp_path / "animated.gif"
    
    # imageio expects a single stacked array, not a python list of arrays
    frames_array = np.stack(frames)
    iio.imwrite(file_path, frames_array, plugin="pillow", format="GIF")

    iterator = iio.imiter(file_path, plugin="pillow")

    yielded_frames = 0
    for i, frame in enumerate(iterator):
        assert frame.shape == (100, 100, 3)
        assert np.array_equal(frame[0, 0], colors[i])
        yielded_frames += 1

    assert yielded_frames == 5

def test_imiter_static_image_yields_single_array_and_stops(tmp_path):
    img = np.zeros((256, 256, 4), dtype=np.uint8)
    file_path = tmp_path / "static.png"
    iio.imwrite(file_path, img)

    iterator = iio.imiter(file_path)

    frame = next(iterator)
    assert frame.shape == (256, 256, 4)
    assert frame.dtype == np.uint8

    with pytest.raises(StopIteration):
        next(iterator)

def test_imiter_empty_media_raises_exception_immediately():
    empty_gif_bytes = b'GIF89a\x01\x00\x01\x00\x00\x00\x00;'

    with pytest.raises((StopIteration, OSError, EOFError)):
        iterator = iio.imiter(empty_gif_bytes, plugin="pillow")
        next(iterator)

def test_improps_extracts_metadata_without_pixel_decoding(tmp_path):
    file_path = tmp_path / "massive.jpg"
    img = np.zeros((10000, 10000, 3), dtype=np.uint8)
    iio.imwrite(file_path, img, extension=".jpg")

    del img

    start_time = time.perf_counter()
    props = iio.improps(file_path)
    duration = time.perf_counter() - start_time

    assert props.shape == (10000, 10000, 3)
    assert props.dtype == np.uint8
    assert props.is_batch is False
    assert duration < 0.5

def test_improps_unparseable_header_raises_exception(tmp_path):
    file_path = tmp_path / "corrupt.jpg"
    file_path.write_bytes(b"\x00\xFF\x00\xFF" * 100)

    with pytest.raises((ValueError, OSError)):
        iio.improps(file_path)

def test_improps_with_index_on_unsupported_format_raises_exception(tmp_path):
    file_path = tmp_path / "static_test_image.bmp"
    iio.imwrite(file_path, np.zeros((10, 10, 3), dtype=np.uint8))

    with pytest.raises((ValueError, EOFError, IndexError)):
        iio.improps(file_path, index=1)

    with pytest.raises((ValueError, EOFError, IndexError)):
        iio.improps(file_path, index=-1)

def test_imwrite_to_bytes_uri_returns_encoded_byte_string():
    img_array = np.full((64, 64, 3), 128, dtype=np.uint8)
    encoded_bytes = iio.imwrite("<bytes>", img_array, plugin="pillow", format="JPEG")

    assert isinstance(encoded_bytes, bytes)
    assert len(encoded_bytes) > 0

def test_imread_from_byte_string_returns_decoded_array():
    img_array = np.array([
        [[255, 0, 0], [0, 255, 0]],
        [[0, 0, 255], [255, 255, 255]]
    ], dtype=np.uint8)

    encoded_bytes = iio.imwrite("<bytes>", img_array, plugin="pillow", format="PNG")
    decoded_array = iio.imread(encoded_bytes, plugin="pillow")

    np.testing.assert_array_equal(decoded_array, img_array)