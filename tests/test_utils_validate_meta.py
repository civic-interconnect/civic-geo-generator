import json
from pathlib import Path

import pytest

from civic_geo_generator.utils.validate_meta import validate_metadata_schema


def test_metadata_schema_validates(tmp_path):
    """Test that valid metadata passes validation."""
    # Metadata WITHOUT $schema field (schema should be separate)
    metadata = {
        "id": "mn-precincts",
        "title": "Minnesota Precincts",
        "unit_type": "precinct",
        "id_field": "precinct_id",
        "name_field": "precinct_name",
        "snapshot_version": "2025-04",
        "generated_at": "2025-04-01T00:00:00Z",
        "paths": {
            "full_geojson": "full.geojson",
            "web_geojson": "web.geojson",
        },
        "stats": {"features": 1000, "bbox": [-97.2396, 43.4994, -89.4913, 49.3844]},
        "spatial": {"crs": "EPSG:4326", "geometry_type": "Polygon"},
        "source_name": "Minnesota Secretary of State",
        "source_url": "https://example.mn.gov",
        "license": "Public Domain",
        "source_fields": {
            "precinct_id": ["precinct_id"],
            "precinct_name": ["precinct_name"],
            "county": ["county"],
        },
    }

    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata))

    # Find schema
    schema_paths = [
        Path("schemas/output/metadata/v0.1.0/schema.json"),
    ]

    schema_path = next((p for p in schema_paths if p.exists()), None)

    if not schema_path:
        pytest.skip("Schema file not found")

    assert validate_metadata_schema(metadata_path, schema_path)
