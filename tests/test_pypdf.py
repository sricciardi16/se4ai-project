# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import PyPDF2
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyPDF2.errors import FileNotDecryptedError, PdfReadError

# 4. Auxiliary: Standard Library
import io
from io import BytesIO
import zlib


def _create_test_pdf(num_pages: int, width: float = 200, height: float = 200) -> io.BytesIO:
    """Helper function to generate a PDF in memory for testing."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=width, height=height)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def test_read_pdf_preserves_page_count():
    # Crucial Data: Must test with a multi-page PDF (specifically 3 pages).
    pdf_stream = _create_test_pdf(num_pages=3)

    reader = PdfReader(pdf_stream)

    # Behavioral Specification: pages attribute length exactly matches total pages
    assert len(reader.pages) == 3

def test_read_page_preserves_dimensions():
    # Crucial Data: Must test with a specific known dimension: 200x200.
    pdf_stream = _create_test_pdf(num_pages=1, width=200, height=200)

    reader = PdfReader(pdf_stream)
    page = reader.pages[0]

    # Behavioral Specification: physical dimensions accurately readable and match
    assert page.mediabox.width == 200
    assert page.mediabox.height == 200

def test_merge_pdfs_combines_page_counts():
    # Crucial Data: Merge a 1-page PDF and a 2-page PDF to verify exactly 3 pages.
    pdf_stream_1 = _create_test_pdf(num_pages=1)
    pdf_stream_2 = _create_test_pdf(num_pages=2)

    reader1 = PdfReader(pdf_stream_1)
    reader2 = PdfReader(pdf_stream_2)

    writer = PdfWriter()

    # Sequentially add pages from multiple different PdfReader instances
    for page in reader1.pages:
        writer.add_page(page)
    for page in reader2.pages:
        writer.add_page(page)

    merged_out = io.BytesIO()
    writer.write(merged_out)
    merged_out.seek(0)

    # Verify the resulting document has exactly 3 pages
    merged_reader = PdfReader(merged_out)
    assert len(merged_reader.pages) == 3

def test_write_pdf_preserves_page_count():
    # Crucial Data: Must test with a 4-page PDF.
    pdf_stream = _create_test_pdf(num_pages=4)

    reader = PdfReader(pdf_stream)
    writer = PdfWriter()

    # Add all pages from source PDF
    for page in reader.pages:
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)

    # Verify resulting document preserves the exact page count
    new_reader = PdfReader(out)
    assert len(new_reader.pages) == 4

def test_rotate_page_updates_rotation_angle():
    # Crucial Data: Must test with a 90-degree clockwise rotation.
    pdf_stream = _create_test_pdf(num_pages=1)

    reader = PdfReader(pdf_stream)
    page = reader.pages[0]

    # Rotate 90 degrees clockwise
    page.rotate(90)

    writer = PdfWriter()
    writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)

    # Read back and verify the page permanently reflects the new rotation angle
    new_reader = PdfReader(out)
    new_page = new_reader.pages[0]

    assert new_page.rotation == 90

def test_rotate_page_preserves_dimensions():
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=300)

    orig_width = page.mediabox.width
    orig_height = page.mediabox.height

    # Rotate the page by 180 degrees
    page.rotate(180)

    # The absolute dimensions of the mediabox should remain identical
    assert page.mediabox.width == orig_width
    assert page.mediabox.height == orig_height

def test_encrypt_and_decrypt_pdf_success():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)

    # Encrypt with the specified password
    writer.encrypt("secret-password")

    out_stream = io.BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)

    reader = PdfReader(out_stream)

    # Verify it is encrypted
    assert reader.is_encrypted is True

    # Decrypt and verify success (returns truthy value on success)
    decrypt_result = reader.decrypt("secret-password")
    assert decrypt_result

    # Verify we can access the pages after decryption
    assert len(reader.pages) == 1

def test_decrypt_pdf_allows_page_access():
    writer = PdfWriter()
    writer.add_blank_page(width=150, height=250)
    writer.encrypt("pw")

    out_stream = io.BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)

    reader = PdfReader(out_stream)
    reader.decrypt("pw")

    # Access the page and verify structural properties are retained
    page = reader.pages[0]
    assert page.mediabox.width == 150
    assert page.mediabox.height == 250

def test_write_and_read_metadata_preserves_values():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)

    # Add specific metadata
    metadata = {
        "/Title": "PyPDF Benchmark Document",
        "/Author": "RealAppCodeBench"
    }
    writer.add_metadata(metadata)

    out_stream = io.BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)

    reader = PdfReader(out_stream)

    # Verify the exact key-value pairs are retrievable
    assert reader.metadata is not None
    assert reader.metadata.get("/Title") == "PyPDF Benchmark Document"
    assert reader.metadata.get("/Author") == "RealAppCodeBench"

def test_write_and_read_multiple_metadata_fields():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)

    # Add multiple standard PDF info dictionary fields
    metadata = {
        "/Title": "Test Title",
        "/Author": "Test Author",
        "/Subject": "Test Subject",
        "/Producer": "Test Producer"
    }
    writer.add_metadata(metadata)

    out_stream = io.BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)

    reader = PdfReader(out_stream)

    # Verify all fields are preserved and readable
    assert reader.metadata is not None
    assert reader.metadata.get("/Title") == "Test Title"
    assert reader.metadata.get("/Author") == "Test Author"
    assert reader.metadata.get("/Subject") == "Test Subject"
    assert reader.metadata.get("/Producer") == "Test Producer"

def _create_pdf(num_pages: int) -> io.BytesIO:
    """Helper to generate a PDF in memory with a specific number of pages."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=100, height=100)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def test_writer_append_combines_page_counts():
    # PER RULE 1 & 2: The legacy `append_pages_from_reader` is deprecated in pypdf 3.0.
    # The idiomatic, standard approach in 3.0 is to use `PdfWriter.append()`.
    pdf2 = _create_pdf(2)
    pdf3 = _create_pdf(3)

    reader2 = PdfReader(pdf2)
    reader3 = PdfReader(pdf3)

    writer = PdfWriter()
    writer.append(reader2)
    writer.append(reader3)

    assert len(writer.pages) == 5

def test_clone_pdf_preserves_page_count():
    pdf3 = _create_pdf(3)
    reader = PdfReader(pdf3)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    assert len(writer.pages) == 3

def test_write_and_read_blank_pdf_pages():
    writer = PdfWriter()

    # Crucial Data: width=72 * 8.5, height=72 * 11
    expected_width = 72 * 8.5
    expected_height = 72 * 11
    writer.add_blank_page(width=expected_width, height=expected_height)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)

    reader = PdfReader(out)
    assert len(reader.pages) == 1

    # Verify the dimensions were correctly applied and read
    page = reader.pages[0]
    assert float(page.mediabox.width) == expected_width
    assert float(page.mediabox.height) == expected_height

def test_extract_page_and_write_to_new_pdf():
    # Crucial Data: multi-page PDF (3 pages)
    pdf3 = _create_pdf(3)
    reader = PdfReader(pdf3)

    # Crucial Data: isolating just the first page
    page = reader.pages[0]

    writer = PdfWriter()
    writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)

    new_reader = PdfReader(out)
    assert len(new_reader.pages) == 1

def test_merge_multiple_pdf_streams():
    # Generate first PDF stream
    writer1 = PdfWriter()
    writer1.add_blank_page(width=100, height=100)
    stream1 = BytesIO()
    writer1.write(stream1)
    stream1.seek(0)

    # Generate second PDF stream
    writer2 = PdfWriter()
    writer2.add_blank_page(width=100, height=100)
    stream2 = BytesIO()
    writer2.write(stream2)
    stream2.seek(0)

    merger = PdfMerger()

    # Test direct BytesIO append with fallback to PdfReader
    try:
        merger.append(stream1)
    except Exception:
        stream1.seek(0)
        merger.append(PdfReader(stream1))

    # Test appending a PdfReader object directly
    reader2 = PdfReader(stream2)
    merger.append(reader2)

    out_stream = BytesIO()
    merger.write(out_stream)
    merger.close()

    # Verify the merged output
    out_stream.seek(0)
    result_reader = PdfReader(out_stream)
    assert len(result_reader.pages) == 2

def test_read_invalid_pdf_bytes_raises_exception():
    stream = BytesIO(b"This is not a PDF file")
    with pytest.raises(PdfReadError):
        PdfReader(stream)

def test_load_valid_document_exposes_pages_and_metadata():
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=100, height=100)

    writer.add_metadata({
        "/Title": "Test Document 影師嗎",
        "/Author": "Jane Doe"
    })

    stream = BytesIO()
    writer.write(stream)
    stream.seek(0)

    reader = PdfReader(stream)

    # Verify pages and metadata
    assert len(reader.pages) == 3
    assert reader.metadata is not None
    assert reader.metadata.get("/Title") == "Test Document 影師嗎"
    assert reader.metadata.get("/Author") == "Jane Doe"

def test_parse_corrupted_document_raises_pdf_read_error():
    invalid_inputs = [
        b'\x00\xFF\xFE\x00\x11\x22',
        b'This is just a text file, not a PDF.'
    ]

    for invalid_bytes in invalid_inputs:
        stream = BytesIO(invalid_bytes)
        with pytest.raises(PdfReadError):
            PdfReader(stream)

def test_load_encrypted_document_flags_is_encrypted_true():
    # Create and test an unencrypted PDF
    writer_unenc = PdfWriter()
    writer_unenc.add_blank_page(width=100, height=100)
    stream_unenc = BytesIO()
    writer_unenc.write(stream_unenc)
    stream_unenc.seek(0)

    reader_unenc = PdfReader(stream_unenc)
    assert reader_unenc.is_encrypted is False

    # Create and test an encrypted PDF
    writer_enc = PdfWriter()
    writer_enc.add_blank_page(width=100, height=100)

    writer_enc.encrypt("password")
    stream_enc = BytesIO()
    writer_enc.write(stream_enc)
    stream_enc.seek(0)

    reader_enc = PdfReader(stream_enc)
    assert reader_enc.is_encrypted is True



def test_access_encrypted_pages_without_decryption_raises_error():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt(user_password="user_pass_123", owner_password="Admin!@#456")

    pdf_bytes = io.BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    reader = PdfReader(pdf_bytes)

    with pytest.raises(FileNotDecryptedError):
        _ = len(reader.pages)

    with pytest.raises(FileNotDecryptedError):
        _ = reader.pages[0]


def test_extract_text_returns_continuous_string_including_special_characters():
    stream = _create_minimal_pdf_with_text("ASCII Cafe !@#")
    reader = PdfReader(stream)

    # Test page with complex text
    text_page = reader.pages[0]
    extracted = text_page.extract_text()
    assert extracted == "ASCII Cafe !@#"

    # Test completely blank page
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    blank_stream = io.BytesIO()
    writer.write(blank_stream)
    blank_stream.seek(0)
    
    blank_reader = PdfReader(blank_stream)
    blank_page = blank_reader.pages[0]
    assert blank_page.extract_text() == ""


def test_access_page_images_returns_iterable_of_embedded_image_files():
    # Dynamically build a PDF with exactly 3 embedded images of varying formats
    jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x00\xff\xd9"
    flate_data = zlib.compress(b"\x00\x00\x00")
    raw_data = b"\xff\x00\x00"

    img1 = f"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpeg_data)} >>\nstream\n".encode() + jpeg_data + b"\nendstream"
    img2 = f"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(flate_data)} >>\nstream\n".encode() + flate_data + b"\nendstream"
    img3 = f"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(raw_data)} >>\nstream\n".encode() + raw_data + b"\nendstream"

    objs = [
        b"",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /XObject << /Im1 5 0 R /Im2 6 0 R /Im3 7 0 R >> >> /Contents 8 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /Resources <<>> /Contents 9 0 R >>",
        img1,
        img2,
        img3,
        b"<< /Length 0 >>\nstream\nendstream",
        b"<< /Length 0 >>\nstream\nendstream",
    ]

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for i in range(1, len(objs)):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + objs[i] + b"\nendobj\n"

    xref_start = len(pdf)
    pdf += b"xref\n0 " + str(len(objs)).encode() + b"\n"
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode()

    pdf += b"trailer\n<< /Size " + str(len(objs)).encode() + b" /Root 1 0 R >>\n"
    pdf += b"startxref\n" + str(xref_start).encode() + b"\n%%EOF\n"

    reader = PdfReader(io.BytesIO(pdf))

    # Page with exactly 3 images
    page_with_images = reader.pages[0]
    images = page_with_images.images
    assert len(images) == 3

    # Text-only page with 0 images
    text_only_page = reader.pages[1]
    no_images = text_only_page.images
    assert hasattr(no_images, '__iter__')
    assert len(no_images) == 0


def test_rotate_page_stores_negative_angles_as_provided():
    writer = PdfWriter()

    # Test 90 degrees
    page = writer.add_blank_page(width=100, height=100)
    result = page.rotate(90)
    assert result is page
    assert page.get("/Rotate") == 90

    # Test 180 degrees
    page = writer.add_blank_page(width=100, height=100)
    result = page.rotate(180)
    assert result is page
    assert page.get("/Rotate") == 180

    # Test 270 degrees
    page = writer.add_blank_page(width=100, height=100)
    result = page.rotate(270)
    assert result is page
    assert page.get("/Rotate") == 270

    # pypdf does not normalize negative angles, it stores them exactly as provided
    page = writer.add_blank_page(width=100, height=100)
    result = page.rotate(-90)
    assert result is page
    assert page.get("/Rotate") == -90



def _create_minimal_pdf_with_text(text: str) -> io.BytesIO:
    """
    Helper function to generate a valid, minimal PDF in-memory with specific text.
    This avoids relying on external PDF generation libraries while providing
    exact byte-level control for testing pypdf's extraction and merging.
    """
    content = f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode('ascii')
    content_len = len(content)

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {content_len} >>\nstream\n".encode('ascii') + content + b"\nendstream\nendobj\n"
    ]

    offsets = [0]
    current_offset = len(b"%PDF-1.4\n")
    for obj in objects:
        offsets.append(current_offset)
        current_offset += len(obj)

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        xref += f"{offset:010d} 00000 n \n".encode('ascii')

    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{current_offset}\n%%EOF\n".encode('ascii')

    return io.BytesIO(b"%PDF-1.4\n" + b"".join(objects) + xref + trailer)


def test_merge_page_overlays_source_content_onto_target_page():
    target_stream = _create_minimal_pdf_with_text("Base Document")
    source_stream = _create_minimal_pdf_with_text("CONFIDENTIAL WATERMARK")

    target_reader = PdfReader(target_stream)
    source_reader = PdfReader(source_stream)

    target_page = target_reader.pages[0]
    source_page = source_reader.pages[0]

    # Merge the source page onto the target page
    target_page.merge_page(source_page)

    # Verify the target page reflects the combined state
    combined_text = target_page.extract_text()
    assert "Base Document" in combined_text
    assert "CONFIDENTIAL WATERMARK" in combined_text

    # Verify the source page remains completely unaffected
    source_text = source_page.extract_text()
    assert "CONFIDENTIAL WATERMARK" in source_text
    assert "Base Document" not in source_text


def test_add_page_appends_pages_sequentially_maintaining_exact_order():
    # Create distinct PageObject instances
    temp_writer = PdfWriter()
    page_a = temp_writer.add_blank_page(width=100, height=100)
    page_b = temp_writer.add_blank_page(width=200, height=200)
    page_c = temp_writer.add_blank_page(width=300, height=300)

    writer = PdfWriter()

    # Invoke add_page in non-alphabetical order: B, C, A
    writer.add_page(page_b)
    writer.add_page(page_c)
    writer.add_page(page_a)

    # Assert exact chronological order is maintained by checking dimensions
    assert len(writer.pages) == 3
    assert writer.pages[0].mediabox.width == 200
    assert writer.pages[1].mediabox.width == 300
    assert writer.pages[2].mediabox.width == 100



def test_append_specific_page_range_adds_pages_sequentially():
    # Create source document with exactly 5 distinct pages (indices 0 through 4)
    source_writer = PdfWriter()
    for i in range(5):
        # Varying widths to uniquely identify pages later
        source_writer.add_blank_page(width=100 + i, height=100 + i)

    source_stream = io.BytesIO()
    source_writer.write(source_stream)
    source_stream.seek(0)

    source_reader = PdfReader(source_stream)

    # Create target writer with an existing page
    target_writer = PdfWriter()
    existing_page = target_writer.add_blank_page(width=50, height=50)

    initial_len = len(target_writer.pages)
    assert initial_len == 1

    # Append specific page range out of sequential order
    target_writer.append(source_reader, pages=[3, 1, 4])

    # Verification
    assert len(target_writer.pages) == initial_len + 3
    
    # Verify by dimension
    assert target_writer.pages[0].mediabox.width == 50  # existing_page

    # Verify the newly appended pages strictly match the content of source pages 3, 1, and 4
    assert target_writer.pages[1].mediabox.width == 103  # Source page 3
    assert target_writer.pages[2].mediabox.width == 101  # Source page 1
    assert target_writer.pages[3].mediabox.width == 104  # Source page 4


def test_writer_outputs_valid_pdf_magic_number():
    writer = PdfWriter()
    # Input state: A PdfWriter containing exactly 2 pages
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=200, height=200)

    # Target stream
    stream = io.BytesIO()
    writer.write(stream)

    # Byte-level verification: must strictly begin with the PDF magic number signature
    pdf_bytes = stream.getvalue()
    assert pdf_bytes.startswith(b"%PDF-")

    stream.seek(0)
    try:
        # Must successfully parse without raising a PdfReadError
        reader = PdfReader(stream)
        # Accurately reflect the exact number of pages originally added
        assert len(reader.pages) == 2
    except PdfReadError:
        pytest.fail("PdfReadError was raised unexpectedly on a valid byte stream.")
