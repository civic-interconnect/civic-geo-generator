# tests/test_index.py
import json

import civic_geo_generator.index as index
import civic_geo_generator.utils.paths as paths


def test_index_builds_flat_and_state(monkeypatch, tmp_path):
    # Redirect data-out
    monkeypatch.setattr(paths, "get_data_out_dir", lambda: tmp_path)

    # Create structure:
    # data-out/us/mn/precincts/2025-04/{web.geojson, metadata.json}
    out_dir = tmp_path / "us" / "minnesota" / "precincts" / "2025-04"
    out_dir.mkdir(parents=True)
    (out_dir / "metadata.json").write_text("{}", encoding="utf-8")
    gj = out_dir / "web.geojson"
    gj.write_text("{}", encoding="utf-8")

    # Mock geopandas
    class GDF:
        def __len__(self):
            return 3

        @property
        def total_bounds(self):
            return (-1.0, -2.0, 3.0, 4.0)

    monkeypatch.setattr(index.gpd, "read_file", lambda p: GDF())

    rc = index.index_main()
    assert rc == 0

    flat = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert any("web.geojson" in x["path"] for x in flat)

    state_idx = json.loads(
        (tmp_path / "us" / "minnesota" / "index.json").read_text(encoding="utf-8")
    )
    assert "layers" in state_idx

    def posix(s: str) -> str:
        return s.replace("\\", "/")

    assert any(
        posix(i["latest"]).endswith("precincts/2025-04/metadata.json") for i in state_idx["layers"]
    )
