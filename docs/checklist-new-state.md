# New-State Bring-Up Checklist

## 1) Create config

- Copy a template and save as: `data-config/us/{state2lower}/{view}.yaml`
- Fill in:
  - build.version (YYYY-MM)
  - build.input_path (relative to `data-in/`)
  - fields_rename, fields_keep, add_fields
  - write_topojson, simplify_pct
  - required_columns (optional override)
  - unique_id_column (default: unit_id)

## 2) Stage inputs

- Put raw data under `data-in/...` per your config.
- Commit nothing in `data-in` (it is local-only).

## 3) Dry run

```
# single build
civic-gen build -v 2025-04

# validate
civic-gen validate -v 2025-04

# index (flat + state)
civic-gen index
```

Or batch:

```
# inputs.yaml controls runs
civic-gen run -f inputs.yaml
```

## 4) QA spot checks

- Open `data-out/us/{state_slug}/{view}/{version}/metadata.json`
- Confirm:
  - CRS EPSG:4326, geometry type Polygon/MultiPolygon
  - features count reasonable
  - bbox sane
  - id_field/name_field present and correct
  - `source_fields` maps from canonical to original columns

## 5) App smoke test

- Load `web.geojson` or `web.topojson` into your map (local Insights) and confirm labels and filters.

## 6) Prepare for publish (optional)

- Verify `data-out/us/{state_slug}/{view}/{version}/` contains:
  - full.geojson
  - web.geojson
  - web.topojson (if enabled)
  - metadata.json
- Ensure `data-out/us/{state_slug}/index.json` points `latest` to your version.

## 7) Publish (manual)

- Publishing must be idempotent and additive (no history deletion).
- For now, manually add upload or push to data repo.
