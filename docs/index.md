# Civic Geo Generator

Lightweight CLI and library to build web-optimized GeoJSON for election precincts (and similar layers).  
Outputs three artifacts per run:

- full GeoJSON (QA and reproducibility)
- web GeoJSON (served to apps)
- TopoJSON (optional, for smaller delivery)

It also writes per-version `metadata.json`, and a state `index.json` that points to the latest layer.

## Quick start

```bash
# install deps
uv sync --extra dev --extra docs --upgrade

# build, validate, index for a version
uv run civic-gen build    --version 2025-04
uv run civic-gen validate --version 2025-04
uv run civic-gen index

# orchestrated runs based on yaml file
uv run civic-gen run -f inputs.yaml

# or for just MN precincts
uv run civic-gen run MN precincts
```

## Conventions

- Batch inputs live in `inputs.yaml`.
- Config files live under `data-config/` (e.g., `us/mn/precincts.yaml`).
- Data input files should be placed in the **`data-in`** folder, organized by state and layer as described in your YAML configs (e.g., `data-config/us/mn/precincts.yaml`).
- Outputs are written under `data-out/us/<state-name>/<view>/<version>/`.

## Links

- Source: https://github.com/civic-interconnect/civic-geo-generator
- Issues: https://github.com/civic-interconnect/civic-geo-generator/issues
