# tests/test_validate.py

import json

import yaml

from civic_geo_generator import validate
from civic_geo_generator.utils import paths


def test_validate_runs_successfully(tmp_path, monkeypatch):
    """
    Validate should succeed when a minimal, well-formed repo layout exists.
    Anchor config discovery to a temp fixtures root via CIGEO_CONFIG_ROOT.
    """
    # Work within tmp so all relative paths resolve here
    monkeypatch.chdir(tmp_path)

    # Point config discovery at a temp fixtures root
    fixtures = tmp_path / "fixtures"
    monkeypatch.setenv("CIGEO_CONFIG_ROOT", str(fixtures))

    # Ensure data-in / data-out helpers point into tmp (no real FS writes)
    monkeypatch.setattr(paths, "get_data_in_dir", lambda: tmp_path / "data-in")
    monkeypatch.setattr(paths, "get_data_out_dir", lambda: tmp_path / "data-out")

    # Minimal config: config/us/mn/precincts.yaml
    cfg_dir = fixtures / "config" / "us" / "mn"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "precincts.yaml").write_text(
        yaml.dump({"build": {"version": "2025-04"}}), encoding="utf-8"
    )

    # Create expected output structure
    out_dir = tmp_path / "data-out" / "us" / "mn" / "precincts" / "2025-04"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Valid minimal GeoJSON (GeoJSON implies WGS84; validator sets CRS if missing)
    test_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "precinct_id": 1,
                    "precinct_name": "Test Precinct",
                    "county": "Example County",
                },
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            }
        ],
    }
    (out_dir / "full.geojson").write_text(json.dumps(test_geojson), encoding="utf-8")
    (out_dir / "web.geojson").write_text(json.dumps(test_geojson), encoding="utf-8")

    # Minimal metadata.json
    (out_dir / "metadata.json").write_text(
        json.dumps(
            {
                "$schema": "https://example.org/metadata.schema.json",
                "state": "mn",
                "view": "precincts",
                "version": "2025-04",
                "artifacts": {
                    "full_path": str(out_dir / "full.geojson"),
                    "web_name": "web.geojson",
                    "topo_name": None,
                },
                "counts": {"features": 1},
                "bbox": [-0.0, -0.0, 0.0, 0.0],
            }
        ),
        encoding="utf-8",
    )

    # Run validate for this version; expect success (0)
    result = validate.main(version="2025-04")
    assert result == 0
