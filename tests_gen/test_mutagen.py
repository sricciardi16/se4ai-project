# 1. Testing Framework & Mocking
import pytest
import shutil

# 2. The Subject Under Test
import audio_metadata as mutagen
import audio_metadata.flac
import audio_metadata.id3
import audio_metadata.mp3
from audio_metadata.easyid3 import EasyID3
from audio_metadata.id3 import APIC, COMM, Encoding, ID3, TALB, TIT2, TPE1


def create_mp3(path):
    """
    Creates a minimal valid MP3 file with exactly 15.45 seconds of audio at 256kbps.
    Mutagen calculates MP3 length as (file_size - id3_size) * 8 / bitrate.
    By writing exactly 494400 bytes of audio data with a 256kbps frame header,
    we guarantee the length is exactly 15.45s and bitrate is 256000, regardless of tag size.
    """
    # Frame header: FF FB D0 44 (MPEG-1, Layer III, 256kbps, 44100Hz, Joint Stereo)
    # Frame size is exactly 835 bytes.
    frame = b"\xFF\xFB\xD0\x44" + b"\x00" * 831
    # Write 10 frames to ensure mutagen can successfully sync
    data = frame * 10
    # Pad to exactly 494400 bytes
    data += b"\x00" * (494400 - len(data))
    path.write_bytes(data)


def create_flac(path):
    """
    Creates a minimal valid FLAC file with a valid STREAMINFO block.
    """
    data = bytearray(b"fLaC")
    data += b"\x80\x00\x00\x22"  # STREAMINFO, last metadata block flag, 34 bytes
    data += b"\x10\x00\x10\x00"  # min/max block size
    data += b"\x00\x00\x00\x00\x00\x00"  # min/max frame size
    data += b"\x0A\xC4\x42\xF0\x00\x0A\x65\x81"  # 44100Hz, 2ch, 16bps, 681345 samples
    data += b"\x00" * 16  # MD5 signature
    path.write_bytes(data)


def test_easyid3_roundtrip_core_string_list_tags(tmp_path):
    path = str(tmp_path / "test.mp3")
    (tmp_path / "test.mp3").touch()

    tag = EasyID3()
    tag["title"] = ["Test Title"]
    tag["artist"] = ["Test Artist"]
    tag["album"] = ["Test Album"]
    tag["tracknumber"] = ["1"]
    tag["date"] = ["2023"]
    tag.save(path)

    reloaded = EasyID3(path)
    assert reloaded["title"] == ["Test Title"]
    assert reloaded["artist"] == ["Test Artist"]
    assert reloaded["album"] == ["Test Album"]
    assert reloaded["tracknumber"] == ["1"]
    assert reloaded["date"] == ["2023"]

def test_easyid3_persist_dict_updates_and_deletions(tmp_path):
    path = str(tmp_path / "test.mp3")
    (tmp_path / "test.mp3").touch()

    tag = EasyID3()
    tag["title"] = ["Old Title"]
    tag["artist"] = ["Old Artist"]
    tag.save(path)

    loaded = EasyID3(path)
    loaded["title"] = ["New Title"]
    del loaded["artist"]
    loaded.save()

    reloaded = EasyID3(path)
    assert reloaded["title"] == ["New Title"]
    assert "artist" not in reloaded

def test_easyid3_unset_fields_are_absent_from_mapping(tmp_path):
    path = str(tmp_path / "test.mp3")
    (tmp_path / "test.mp3").touch()

    tag = EasyID3()
    tag["title"] = ["Only Title"]
    tag.save(path)

    reloaded = EasyID3(path)
    assert "title" in reloaded
    assert "artist" not in reloaded
    assert "album" not in reloaded

def test_easyid3_preserve_multiple_strings_in_list(tmp_path):
    path = str(tmp_path / "test.mp3")
    (tmp_path / "test.mp3").touch()

    tag = EasyID3()
    tag["artist"] = ["Artist One", "Artist Two"]
    tag.save(path)

    reloaded = EasyID3(path)
    assert reloaded["artist"] == ["Artist One", "Artist Two"]

def test_easyid3_save_without_modifications_preserves_tags(tmp_path):
    path = str(tmp_path / "test.mp3")
    (tmp_path / "test.mp3").touch()

    tag = EasyID3()
    tag["title"] = ["Test Title"]
    tag["artist"] = ["Test Artist"]
    tag.save(path)

    loaded = EasyID3(path)
    loaded.save()

    reloaded = EasyID3(path)
    assert reloaded["title"] == ["Test Title"]
    assert reloaded["artist"] == ["Test Artist"]

def test_easyid3_roundtrip_genre_and_albumartist(tmp_path):
    filepath = str(tmp_path / "test_easyid3.mp3")
    open(filepath, "wb").close()

    tag = EasyID3()
    tag["genre"] = ["Rock"]
    tag["albumartist"] = ["The Artist"]
    tag.save(filepath)

    loaded = EasyID3(filepath)
    assert loaded["genre"] == ["Rock"]
    assert loaded["albumartist"] == ["The Artist"]

def test_easyid3_maps_low_level_id3_frames_to_strings(tmp_path):
    filepath = str(tmp_path / "test_mapping.mp3")
    open(filepath, "wb").close()

    tag = ID3()
    tag.add(TIT2(encoding=3, text=["My Title"]))
    tag.add(TPE1(encoding=3, text=["My Artist"]))
    tag.add(TALB(encoding=3, text=["My Album"]))
    tag.save(filepath)

    loaded = EasyID3(filepath)
    assert loaded["title"] == ["My Title"]
    assert loaded["artist"] == ["My Artist"]
    assert loaded["album"] == ["My Album"]

def test_id3_roundtrip_complex_comm_and_apic_frames(tmp_path):
    filepath = str(tmp_path / "test_complex.mp3")
    open(filepath, "wb").close()

    tag = ID3()

    comm_frame = COMM(
        encoding=3,
        lang="eng",
        desc="Test Comment",
        text=["This is a comment"]
    )
    apic_frame = APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,
        desc="Front Cover",
        data=b"\xff\xd8\xff\x00FAKEJPEGDATA"
    )

    tag.add(comm_frame)
    tag.add(apic_frame)
    tag.save(filepath)

    loaded = ID3(filepath)

    loaded_comm = loaded["COMM:Test Comment:eng"]
    assert loaded_comm.encoding == 3
    assert loaded_comm.lang == "eng"
    assert loaded_comm.desc == "Test Comment"
    assert loaded_comm.text == ["This is a comment"]

    loaded_apic = loaded["APIC:Front Cover"]
    assert loaded_apic.encoding == 3
    assert loaded_apic.mime == "image/jpeg"
    assert loaded_apic.type == 3
    assert loaded_apic.desc == "Front Cover"
    assert loaded_apic.data == b"\xff\xd8\xff\x00FAKEJPEGDATA"

def test_id3_persist_modified_frame_text_attribute(tmp_path):
    filepath = str(tmp_path / "test_modify.mp3")
    open(filepath, "wb").close()

    tag = ID3()
    tag.add(TIT2(encoding=3, text=["Old Title"]))
    tag.save(filepath)

    loaded = ID3(filepath)
    loaded["TIT2"].text = ["New Title"]
    loaded.save(filepath)

    reloaded = ID3(filepath)
    assert reloaded["TIT2"].text == ["New Title"]

def test_id3_preserve_multiple_frames_of_same_type(tmp_path):
    filepath = str(tmp_path / "test_multiple.mp3")
    open(filepath, "wb").close()

    tag = ID3()
    tag.add(COMM(encoding=3, lang="eng", desc="First", text=["Text 1"]))
    tag.add(COMM(encoding=3, lang="eng", desc="Second", text=["Text 2"]))
    tag.save(filepath)

    loaded = ID3(filepath)
    comms = loaded.getall("COMM")

    assert len(comms) == 2
    descriptions = {frame.desc for frame in comms}
    assert descriptions == {"First", "Second"}

    assert loaded["COMM:First:eng"].text == ["Text 1"]
    assert loaded["COMM:Second:eng"].text == ["Text 2"]

def test_id3_delall_removes_all_frames_of_type(tmp_path):
    file_path = tmp_path / "test.mp3"
    file_path.write_bytes(b'\xFF\xFB\x90\x44' + b'\x00' * 100)

    audio = mutagen.id3.ID3()
    audio.add(mutagen.id3.APIC(
        encoding=3,
        mime='image/jpeg',
        type=3,
        desc='Cover',
        data=b'fake_image_data'
    ))
    audio.save(file_path, v2_version=4)

    audio = mutagen.id3.ID3(file_path)
    assert len(audio.getall("APIC")) == 1

    audio.delall("APIC")
    audio.save(file_path, v2_version=4)

    audio = mutagen.id3.ID3(file_path)
    assert audio.getall("APIC") == []

def test_id3_roundtrip_talb_and_tcon_text_frames(tmp_path):
    file_path = tmp_path / "test_text.mp3"
    file_path.write_bytes(b'\xFF\xFB\x90\x44' + b'\x00' * 100)

    audio = mutagen.id3.ID3()
    audio.add(mutagen.id3.TALB(encoding=3, text=["My Album"]))
    audio.add(mutagen.id3.TCON(encoding=3, text=["Jazz"]))
    audio.save(file_path, v2_version=4)

    audio = mutagen.id3.ID3(file_path)
    assert audio.getall("TALB")[0].text == ["My Album"]
    assert audio.getall("TCON")[0].text == ["Jazz"]

def test_load_valid_audio_file_returns_format_specific_instance(tmp_path):
    mp3_path = tmp_path / "test_audio.mp3"
    flac_path = tmp_path / "test_audio.flac"

    # Minimal valid MP3 (MPEG-1 Layer 3, 128kbps, 44.1kHz)
    # Mutagen requires multiple frames to successfully sync
    mp3_path.write_bytes((b'\xFF\xFB\x90\x44' + b'\x00' * 413) * 3)

    # Minimal valid FLAC
    create_flac(flac_path)

    mp3_file = mutagen.File(mp3_path)
    flac_file = mutagen.File(flac_path)

    assert mp3_file is not None
    assert isinstance(mp3_file, mutagen.FileType)
    assert type(mp3_file).__name__ == "MP3"

    assert flac_file is not None
    assert isinstance(flac_file, mutagen.FileType)
    assert type(flac_file).__name__ == "FLAC"

def test_load_unsupported_file_returns_none(tmp_path):
    txt_path = tmp_path / "fake_audio.txt"
    txt_path.write_text("This is not an audio file", encoding="utf-8")

    img_path = tmp_path / "image.png"
    img_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 20)

    assert mutagen.File(txt_path) is None
    assert mutagen.File(img_path) is None

def test_load_corrupted_mp3_raises_header_not_found_error(tmp_path):
    corrupt_path = tmp_path / "corrupt.mp3"
    garbage = b'\x00\xFF\xFE\x01' * 25
    corrupt_path.write_bytes(garbage)

    # Mutagen specifically raises HeaderNotFoundError when it fails to sync to an MPEG frame.
    # Because the file has an .mp3 extension, mutagen.File attempts to parse it as an MP3 
    # and propagates the HeaderNotFoundError.
    with pytest.raises(mutagen.mp3.HeaderNotFoundError):
        mutagen.File(corrupt_path)

    # Directly invoking the MP3 class also yields the same exception
    with pytest.raises(mutagen.mp3.HeaderNotFoundError):
        mutagen.mp3.MP3(corrupt_path)

def test_load_with_easy_flag_normalizes_tags_to_string_lists(tmp_path):
    path = tmp_path / "test_easy.mp3"

    # Create a minimal valid MP3 frame (MPEG-1 Layer III, 128kbps, 44100Hz, Stereo)
    # Mutagen requires multiple frames to successfully sync
    frame = b"\xff\xfb\x90\x00" + b"\x00" * 413
    path.write_bytes(frame * 3)

    tags = ID3()
    tags.add(TIT2(encoding=Encoding.UTF8, text=["Test Title"]))
    tags.save(path)

    audio = mutagen.File(path, easy=True)

    assert "title" in audio.tags
    assert audio.tags["title"] == ["Test Title"]
    assert isinstance(audio.tags["title"], list)
    assert isinstance(audio.tags["title"][0], str)


def test_load_audio_file_populates_readonly_streaminfo(tmp_path):
    path = tmp_path / "test_streaminfo.mp3"

    frame = b"\xff\xfb\x90\x00" + b"\x00" * 413
    path.write_bytes(frame * 77)

    audio = mutagen.File(path)
    assert audio is not None

    info = audio.info

    assert abs(info.length - 2.0) < 0.1  # Approx 2.0 seconds
    assert info.sample_rate == 44100
    assert info.bitrate == 128000
    assert info.channels == 2


def test_load_file_with_metadata_exposes_tags_mapping(tmp_path):
    path = tmp_path / "test_metadata.flac"
    create_flac(path)

    audio_setup = mutagen.File(path)
    audio_setup.add_tags()
    audio_setup.tags["artist"] = ["Björk"]
    audio_setup.tags["genre"] = ["Electronic", "Avant-garde"]
    audio_setup.save()

    audio = mutagen.File(path)

    assert audio.tags is not None
    assert audio.tags["artist"] == ["Björk"]
    assert audio.tags["genre"] == ["Electronic", "Avant-garde"]


def test_load_file_without_metadata_returns_none_tags(tmp_path):
    path = tmp_path / "test_no_metadata.flac"
    create_flac(path)

    audio = mutagen.File(path)

    assert audio is not None
    assert audio.tags is None


def test_add_tags_on_stripped_file_initializes_empty_mapping(tmp_path):
    path = tmp_path / "test_add_tags.flac"
    create_flac(path)

    audio = mutagen.File(path)

    assert audio.tags is None

    audio.add_tags()

    assert audio.tags is not None
    audio.tags["title"] = ["New Title"]
    assert audio.tags["title"] == ["New Title"]

# Register 'comment' for EasyID3 to support the required dict keys for MP3 files
def get_comment(id3, key):
    return [c.text[0] for c in id3.getall("COMM")]

def set_comment(id3, key, val):
    id3.delall("COMM")
    for v in val:
        id3.add(COMM(encoding=3, lang="eng", desc="", text=[v]))

if "comment" not in EasyID3.valid_keys.keys():
    EasyID3.RegisterKey("comment", get_comment, set_comment)


def test_modify_tags_does_not_alter_physical_file_until_saved(tmp_path):
    path = tmp_path / "test.mp3"
    create_mp3(path)

    f_setup = mutagen.File(str(path), easy=True)
    f_setup.add_tags()
    f_setup.tags["artist"] = ["Original"]
    f_setup.save()

    f_mem = mutagen.File(str(path), easy=True)
    f_mem.tags["artist"] = ["Modified 影師嗎"]

    f_disk = mutagen.File(str(path), easy=True)
    assert f_disk.tags["artist"] == ["Original"]


def test_save_without_arguments_persists_staged_metadata_to_original_file(tmp_path):
    path = tmp_path / "test.mp3"
    create_mp3(path)

    f_setup = mutagen.File(str(path), easy=True)
    f_setup.add_tags()
    f_setup.save()

    f = mutagen.File(str(path), easy=True)
    f.tags["album"] = ["A Night at the Opera"]
    f.tags["tracknumber"] = ["12/15"]
    f.save()

    f_verify = mutagen.File(str(path), easy=True)
    assert f_verify.tags["album"] == ["A Night at the Opera"]
    assert f_verify.tags["tracknumber"] == ["12/15"]


def test_save_with_destination_path_writes_new_file_and_preserves_original(tmp_path):
    source = tmp_path / "source_track.flac"
    dest = tmp_path / "destination_track_copy.flac"
    create_flac(source)

    f_setup = mutagen.File(str(source))
    f_setup.add_tags()
    f_setup.tags["title"] = ["Original Title"]
    f_setup.save()

    # Mutagen modifies files in place. To save to a new destination, 
    # the destination file must already exist.
    shutil.copy(str(source), str(dest))

    f = mutagen.File(str(source))
    f.tags["title"] = ["Modified Title 影師嗎"]
    f.save(str(dest))

    f_orig = mutagen.File(str(source))
    assert f_orig.tags["title"] == ["Original Title"]

    f_dest = mutagen.File(str(dest))
    assert f_dest.tags["title"] == ["Modified Title 影師嗎"]


def test_delete_removes_all_metadata_leaving_audio_intact(tmp_path):
    path = tmp_path / "test.mp3"
    create_mp3(path)

    f_setup = mutagen.File(str(path), easy=True)
    f_setup.add_tags()
    f_setup.tags["title"] = ["Test Title"]
    f_setup.tags["artist"] = ["Test Artist"]
    f_setup.tags["comment"] = ["A very long comment string to ensure block resizing works"]
    f_setup.save()

    f = mutagen.File(str(path), easy=True)

    assert round(f.info.length, 2) == 15.45
    assert f.info.bitrate == 256000
    assert f.info.sample_rate == 44100

    f.delete()

    f_after = mutagen.File(str(path), easy=True)

    assert f_after.tags is None or len(f_after.tags) == 0

    assert round(f_after.info.length, 2) == 15.45
    assert f_after.info.bitrate == 256000
    assert f_after.info.sample_rate == 44100