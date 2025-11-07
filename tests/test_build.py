from pathlib import Path
from unittest.mock import Mock, patch

from civic_geo_generator.build import build


def test_build_writes_expected_names(tmp_path, monkeypatch):
    """Test that build creates files with expected names."""

    # Create mock GeoDataFrame
    import geopandas as gpd
    from shapely.geometry import Point

    mock_gdf = gpd.GeoDataFrame({"id": [1], "name": ["test"]}, geometry=[Point(0, 0)])

    # Mock all the dependencies
    with (
        patch("civic_geo_generator.build.pipeline.GeoGeneratorConfig") as mock_config_class,
        patch("civic_geo_generator.build.pipeline.gpd.read_file") as mock_read,
        patch("civic_geo_generator.build.pipeline.geojson_utils.save_geojson") as mock_save,
        patch("civic_geo_generator.build.pipeline.shutil.copy2") as mock_copy,
        patch("civic_geo_generator.build.pipeline.MetadataWriter") as mock_metadata_class,
    ):
        # Setup mocks
        out_dir = tmp_path / "output"
        mock_config = Mock()
        mock_config.get_build_config.return_value = {
            "version": "2025-04",
            "fields_lowercase": True,
            "fields_trim": True,
            "repair_geometries": False,  # optional: keep fast and deterministic
        }
        mock_config.get_input_path.return_value = Path("dummy.json")
        mock_config.get_output_dir.return_value = out_dir
        mock_config.state_abbr = "MN"
        mock_config.view = "precincts"
        mock_config_class.return_value = mock_config

        # Mocks create files so downstream checks pass
        def _save_side_effect(gdf, path):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")  # minimal placeholder content

        def _copy_side_effect(src, dst):
            dst = Path(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            # simulate a copy by ensuring the destination file exists
            dst.write_text("{}")

        mock_read.return_value = mock_gdf
        mock_save.side_effect = _save_side_effect
        mock_copy.side_effect = _copy_side_effect

        mock_metadata_writer = Mock()
        mock_metadata_class.return_value = mock_metadata_writer

        # Run
        result = build("MN", "precincts", "2025-04")
        assert result == 0

        # Verify interactions
        assert mock_config_class.called
        assert mock_read.called
        assert mock_save.called
        assert mock_copy.called
        assert mock_metadata_writer.write.called

        # Expected filenames should exist
        assert (out_dir / "full.geojson").exists()
        assert (out_dir / "web.geojson").exists()
