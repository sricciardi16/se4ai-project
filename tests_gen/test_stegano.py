# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from image_message_embedder import exifHeader, lsb
from image_message_embedder.lsb import generators

# 3. Auxiliary: Third-Party
from PIL import Image

# 4. Auxiliary: Standard Library
import os


@pytest.fixture
def base_image_path(tmp_path):
    """Creates a basic RGB image to be used as the carrier for hidden messages."""
    path = tmp_path / "base_image.png"
    # 100x100 provides 10,000 pixels (30,000 bits in RGB), plenty for our test strings
    img = Image.new('RGB', (100, 100), color='white')
    img.save(path)
    return str(path)

def test_lsb_hide_and_reveal_standard_string(base_image_path, tmp_path):
    secret_message = "hello world"
    output_path = str(tmp_path / "hidden_standard.png")

    # Hide the message
    secret_image = lsb.hide(base_image_path, secret_message)
    secret_image.save(output_path)

    # Reveal the message from the saved file path
    revealed_message = lsb.reveal(output_path)

    assert revealed_message == secret_message

def test_lsb_hide_and_reveal_with_generator(base_image_path, tmp_path):
    secret_message = "generator secret"
    output_path = str(tmp_path / "hidden_generator.png")

    # Hide using lsb and the eratosthenes generator
    secret_image = lsb.hide(base_image_path, secret_message, generators.eratosthenes())
    secret_image.save(output_path)

    # Reveal using lsb and a new instance of the exact same generator
    revealed_message = lsb.reveal(output_path, generators.eratosthenes())

    assert revealed_message == secret_message

def test_lsb_hide_and_reveal_preserves_long_string_with_punctuation(base_image_path, tmp_path):
    secret_message = "This is a longer secret message with punctuation: 12345, hello-world!"
    output_path = str(tmp_path / "hidden_long.png")

    # Hide the message
    secret_image = lsb.hide(base_image_path, secret_message)
    secret_image.save(output_path)

    # Reveal the message
    revealed_message = lsb.reveal(output_path)

    assert revealed_message == secret_message

def test_lsb_reveal_accepts_pil_image_object_directly(base_image_path):
    secret_message = "direct pil object test"

    # hide() returns a PIL.Image.Image object
    secret_image_obj = lsb.hide(base_image_path, secret_message)

    # Verify it is indeed a PIL Image
    assert isinstance(secret_image_obj, Image.Image)

    # Pass the PIL.Image.Image object directly to reveal()
    revealed_message = lsb.reveal(secret_image_obj)

    assert revealed_message == secret_message

def test_lsb_hide_and_reveal_standard_string_arbitrary_message(base_image_path, tmp_path):
    secret_message = "my secret"
    output_path = str(tmp_path / "my_hidden.png")

    # Hide the message
    secret_image = lsb.hide(base_image_path, secret_message)
    secret_image.save(output_path)

    # Reveal the message
    revealed_message = lsb.reveal(output_path)

    assert revealed_message == secret_message

@pytest.fixture
def dummy_png(tmp_path):
    """Fixture to provide a dummy PNG image for LSB steganography."""
    img_path = tmp_path / "dummy.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path, format="PNG")
    return str(img_path)

@pytest.fixture
def dummy_jpg(tmp_path):
    """Fixture to provide a dummy JPEG image for EXIF steganography."""
    img_path = tmp_path / "dummy.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(img_path, format="JPEG")
    return str(img_path)

def test_lsb_preserves_extended_latin_characters(dummy_png, tmp_path):
    out_path = str(tmp_path / "out_latin.png")
    secret = "Café au lait"

    # lsb.hide returns a PIL Image object
    secret_img = lsb.hide(dummy_png, secret)
    secret_img.save(out_path)

    revealed = lsb.reveal(out_path)
    assert revealed == secret

def test_exif_header_hide_and_reveal_byte_string(dummy_jpg, tmp_path):
    out_path = str(tmp_path / "out_exif.jpg")
    secret = b"exif secret bytes"

    exifHeader.hide(dummy_jpg, out_path, secret)

    revealed = exifHeader.reveal(out_path)
    assert revealed == secret

def test_exif_header_writes_independent_files_without_cross_contamination(dummy_jpg, tmp_path):
    out_path1 = str(tmp_path / "out1.jpg")
    out_path2 = str(tmp_path / "out2.jpg")

    payload1 = b"payload-one"
    payload2 = b"payload-two"

    exifHeader.hide(dummy_jpg, out_path1, payload1)
    exifHeader.hide(dummy_jpg, out_path2, payload2)

    assert exifHeader.reveal(out_path1) == payload1
    assert exifHeader.reveal(out_path2) == payload2

def test_lsb_hide_and_reveal_minimal_string(dummy_png, tmp_path):
    out_path = str(tmp_path / "out_min_adapted.png")
    secret = "ok"

    secret_img = lsb.hide(dummy_png, secret)
    secret_img.save(out_path)

    revealed = lsb.reveal(out_path)
    assert revealed == secret

def test_lsb_hide_and_reveal_long_string_with_spaces(tmp_path):
    img_path = tmp_path / "cover.png"
    Image.new("RGB", (200, 200), "white").save(img_path)

    message = "A long long long message: 1234567890 abcdefghijklmnopqrstuvwxyz"
    secret_img = lsb.hide(str(img_path), message)
    secret_path = tmp_path / "secret.png"
    secret_img.save(secret_path)

    revealed = lsb.reveal(str(secret_path))
    assert revealed == message

def test_image_backends_return_savable_objects_writing_non_empty_files(tmp_path):
    """
    Testing lsb backend with and without generators to ensure multiple
    configurations return valid, savable PIL Image objects.
    """
    img_path = tmp_path / "cover.png"
    Image.new("RGB", (50, 50), "black").save(img_path)

    # lsb backend (standard)
    lsb_img = lsb.hide(str(img_path), "test")
    lsb_out = tmp_path / "lsb_out.png"
    lsb_img.save(lsb_out)
    assert lsb_out.exists()
    assert os.path.getsize(lsb_out) > 0

    # lsb backend (with generator)
    gen_img = lsb.hide(str(img_path), "test", generators.eratosthenes())
    gen_out = tmp_path / "gen_out.png"
    gen_img.save(gen_out)
    assert gen_out.exists()
    assert os.path.getsize(gen_out) > 0

def test_lsb_hide_reveal_roundtrip_success(tmp_path):
    img_path = tmp_path / "cover.png"
    Image.new("RGB", (32, 32), "white").save(img_path)

    message = "hello"
    secret_img = lsb.hide(str(img_path), message)
    secret_path = tmp_path / "secret.png"
    secret_img.save(secret_path)

    revealed = lsb.reveal(str(secret_path))
    assert revealed == message

def test_hide_sequential_payload_returns_valid_image_object(tmp_path):
    img_path = tmp_path / "cover.png"
    Image.new("RGB", (100, 100), "blue").save(img_path)

    original_mtime = os.path.getmtime(img_path)

    payload = "Standard ASCII payload."
    secret_img = lsb.hide(str(img_path), payload)

    assert isinstance(secret_img, Image.Image)
    # Ensure the original file on disk was left completely unmodified
    assert os.path.getmtime(img_path) == original_mtime

def test_hide_with_auto_convert_rgb_transforms_palette_image(tmp_path):
    img_path = tmp_path / "cover.png"
    # Create an 8-bit 'P' (Palette) mode image
    img = Image.new("P", (50, 50), color=0)
    img.putpalette([
        0, 0, 0,
        255, 255, 255,
    ] + [0] * 762)
    img.save(img_path)

    payload = "Palette conversion test."

    secret_img = lsb.hide(str(img_path), payload, auto_convert_rgb=True)

    assert isinstance(secret_img, Image.Image)
    assert secret_img.mode in ('RGB', 'RGBA')

def test_reveal_sequential_payload_reconstructs_exact_string():
    img = Image.new("RGB", (100, 100), color="white")
    
    # FIX: Removed multi-byte unicode characters. 
    # stegano.lsb natively supports 8-bit characters, so we test within those bounds.
    payload = "Secret message with symbols: !@#$%^&*()"

    encoded_img = lsb.hide(img, payload)
    revealed = lsb.reveal(encoded_img)

    assert revealed == payload

def test_hide_scattered_payload_returns_valid_image_object():
    img = Image.new("RGB", (100, 100), color="white")
    payload = "Scattered prime payload."
    gen = generators.eratosthenes()

    encoded_img = lsb.hide(img, payload, gen)

    assert isinstance(encoded_img, Image.Image)

def test_reveal_scattered_payload_with_correct_generator_reconstructs_string():
    img = Image.new("RGB", (100, 100), color="white")
    
    # FIX: Swapped the exponentially growing fibonacci generator for the eratosthenes generator.
    # The prime number sequence grows slowly enough to fit the payload inside a 10,000 pixel image.
    payload = "Scattered sequence test with prime numbers"

    encoded_img = lsb.hide(img, payload, generators.eratosthenes())
    revealed = lsb.reveal(encoded_img, generators.eratosthenes())

    assert revealed == payload

def test_hide_payload_exceeds_image_capacity_raises_error():
    img = Image.new("RGB", (1, 1), color="white")
    payload = "A"

    with pytest.raises(Exception):
        lsb.hide(img, payload)

def test_hide_generator_exhausted_raises_error():
    img = Image.new("RGB", (50, 50), color="white")
    payload = "This payload requires dozens of bits."
    gen = iter([1, 2, 3, 4, 5])

    with pytest.raises(Exception):
        lsb.hide(img, payload, gen)

def test_reveal_no_payload_raises_index_error():
    # Dynamically generated 10x10 pixel solid black RGB image
    img = Image.new("RGB", (10, 10), color=(0, 0, 0))

    # Attempting to reveal a message from a pristine image with no delimiter
    # will exhaust the pixel data and raise an IndexError.
    with pytest.raises(IndexError):
        lsb.reveal(img)

def test_reveal_wrong_generator_raises_index_error():
    # Create a base image large enough to hold the payload using the generator sequence
    base_img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    payload = "Mismatched Sequence Test"

    # Encode using the Eratosthenes (prime numbers) generator
    encoded_img = lsb.hide(base_img, payload, generators.eratosthenes())

    # Attempt to decode using the Fibonacci generator
    # The mismatched sequence will fail to locate the termination delimiter
    with pytest.raises(IndexError):
        lsb.reveal(encoded_img, generators.fibonacci())
