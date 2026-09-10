from app.core.storage import LocalStorage


def test_local_storage_save_and_url(tmp_path):
    store = LocalStorage(tmp_path, "/static")
    url = store.save("solar/before.png", b"\x89PNG")
    # URL carries an mtime cache-buster so a re-seeded asset is re-fetched.
    assert url.startswith("/static/solar/before.png?v=")
    assert (tmp_path / "solar" / "before.png").read_bytes() == b"\x89PNG"


def test_url_for_missing_file_has_no_version(tmp_path):
    store = LocalStorage(tmp_path, "/static")
    assert store.url_for("solar/missing.png") == "/static/solar/missing.png"
