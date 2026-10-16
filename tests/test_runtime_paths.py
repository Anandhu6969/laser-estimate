import sys

from app.runtime_paths import application_data_dir, database_path, project_root, resource_path


def test_source_paths_use_project_files_without_changing_development_database():
    assert database_path() == project_root() / "data" / "laser_estimate.db"
    assert resource_path("assets", "universallogo.png").is_file()
    assert resource_path("app", "ui", "assets", "calendar.svg").is_file()


def test_packaged_paths_use_local_app_data_and_bundle_resources(monkeypatch, tmp_path):
    bundle_dir = tmp_path / "bundle"
    (bundle_dir / "assets").mkdir(parents=True)
    (bundle_dir / "assets" / "universallogo.png").write_bytes(b"test asset")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    expected_data = tmp_path / "LocalAppData" / "LaserEstimate"
    assert application_data_dir() == expected_data
    assert database_path() == expected_data / "laser_estimate.db"
    assert resource_path("assets", "universallogo.png").read_bytes() == b"test asset"
    assert not database_path().exists()
