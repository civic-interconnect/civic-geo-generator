# Civic Geo Generator: Data Contract

## Scope

This contract defines the on-disk outputs written by _civic-geo-generator_ for any state/view (e.g., precincts, school_districts). It standardizes file names, metadata, geometry rules, and per-release versioning so downstream apps (e.g., Insights) can consume data without per-state code.

## Canonical attributes (properties on each feature)

- unit_id: canonical identifier as a string (stable across releases when possible).
- unit_name: display name.
- unit_type: enum describing feature class (e.g., "precinct", "ward", "school_district").
- state_code: 2-letter USPS (e.g., "MN").
- state_fips: 2-digit string (e.g., "27").
- unit_parent_id (optional): stable parent id (e.g., county FIPS or name).
- source\_\* (optional): original authority fields retained for traceability.

Rules:

- IDs are strings; trim whitespace; lowercase column names; preserve UTF-8 in values.
- Null policy: use explicit null (not empty strings) where data is missing.

## Geometry and spatial rules

- CRS: EPSG:4326 only.
- Validity: repair invalid geometries (make_valid then buffer(0)). Drop empties.
- Types: Polygon or MultiPolygon only.
- Precision: coordinates rounded to 6–7 decimals.
- Optional label_point: precomputed centroid for labeling (lon, lat).

## File naming and tiers

Within: `data-out/us/{state_slug}/{view}/{version}/`

- full.geojson (canonical, unsimplified)
- web.geojson (same geometry as full or lightly simplified)
- web.topojson (simplified TopoJSON for web maps)
- metadata.json (dataset-level info and app contract)

Example (MN precincts, Apr 2025):

```
data-out/us/mn/precincts/2025-04/
  full.geojson
  web.geojson
  web.topojson
  metadata.json
```

## Versioning

- Each build writes to a new `version` folder (e.g., YYYY-MM). No overwrites.
- “Latest” pointers live in a state index (see below).

## Metadata contract (metadata.json)

Required fields (see schema for full details):

- id: stable dataset id, e.g., "us/mn/precincts".
- title: human-friendly title.
- unit_type: canonical enum (e.g., "precinct").
- id_field: name of the canonical id column (usually "unit_id").
- name_field: name of the canonical display column (usually "unit_name").
- snapshot_version: build version string (e.g., "2025-04").
- generated_at: ISO 8601 UTC timestamp.
- spatial: { crs: "EPSG:4326", geometry_type: "Polygon" | "MultiPolygon" }.
- stats: { features, bbox } where bbox is [minx, miny, maxx, maxy].
- paths: { full_geojson, web_geojson, web_topojson? }.
- source_name, source_url, license (and optional license_url).
- source_fields: mapping from canonical fields to an array of original source fields.
- web: { topojson_simplify_pct? }.

Optional:

- label_point_field: name of field containing [lon, lat].
- checksums: { filename: sha256 } map.

## Indices

- Flat index: `data-out/index.json`
  - Array of files with path (relative), bbox, features, version, state_code, view.
- State index: `data-out/us/{state_slug}/index.json`
  - Pointers to the latest metadata per view, e.g.:
    ```json
    {
      "layers": [
        { "id": "us/mn/precincts", "latest": "precincts/2025-04/metadata.json" }
      ]
    }
    ```

## Validation gates

- Files exist per tier.
- GeoJSON readable; not empty; geometries valid; CRS is EPSG:4326.
- Required columns present (`unit_id`, `unit_name`, `unit_type`, `state_code`).
- Uniqueness check on `unit_id` (configurable).
- BBox sanity (optional) versus state bounds.

## Publishing (manually upload or push to civic-data-* GitHub repo)

- Build/validate/index locally first.
- Never delete history; new versions are additive.
