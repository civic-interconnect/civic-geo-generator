# civic-geo-generator

[![PyPI](https://img.shields.io/pypi/v/civic-geo-generator.svg)](https://pypi.org/project/civic-geo-generator/)
[![Python versions](https://img.shields.io/pypi/pyversions/civic-geo-generator.svg)](https://pypi.org/project/civic-geo-generator/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/civic-interconnect/civic-geo-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/civic-interconnect/civic-geo-generator/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://civic-interconnect.github.io/civic-geo-generator/)

Lightweight CLI and library to build web-optimized GeoJSON for election precincts (and similar layers).  
Outputs three artifacts per run:

- full GeoJSON (QA and reproducibility)
- web GeoJSON (served to apps)
- TopoJSON (optional, for smaller delivery)

It also writes per-version `metadata.json`, and a state `index.json` that points to the latest layer.

## Installation

```shell
pip install civic-geo-generator
```

## Quick start

```bash
# install deps
uv sync --extra dev --extra docs --upgrade

# orchestrated runs based on yaml file
uv run civic-gen run -f inputs.yaml

# or provide a specific state and view
uv run civic-gen run MN precincts
```

## Conventions

- Batch inputs live in `inputs.yaml`.
- Config files live under `data-config/` (e.g., `us/mn/precincts.yaml`).
- Data input files should be placed in the **`data-in`** folder, organized by state and layer as described in YAML configs (e.g., `data-config/us/mn/precincts.yaml`).
- Outputs are written under `data-out/us/<state-name>/<view>/<version>/`.

## Links

- Source: https://github.com/civic-interconnect/civic-geo-generator
- Issues: https://github.com/civic-interconnect/civic-geo-generator/issues

---

## Pipeline

Place statewide GeoJSON input in correct location, e.g.

- data-in/us/mn/precincts_2025-04.json

Configure inputs.yaml, e.g.

```
# inputs.yaml  (batch mode)
runs:
  - state: MN
    views: [precincts]
    version_overrides:
      precincts: "2025-04"
```

```shell
# 1) Build (copy/normalize/add snapshot metadata)
civic-gen build --version 2025-04

# 2) Validate (CRS, required columns, geometry, basic uniqueness)
civic-gen validate --version 2025-04

# 3) Index (flat index, manifest, state layer pointers)
civic-gen index

```

---

## Development

See [DEVELOPER.md](./DEVELOPER.md)

## Available: Minnesota Precincts

- [State of Minnesota - Election Administration & Campaigns - Data & Maps - GeoJSON files](https://www.sos.mn.gov/election-administration-campaigns/data-maps/geojson-files/)

They include voting precinct boundaries as well as the name, county, and election districts (US Congress, MN Senate and House, County Commissioner) for each precinct.

Geojson files are intended to provide basic information regarding the location of election districts within the state. For the most accurate information on precincts and districts, as well as polling place information, please use the [Polling Place Finder](https://www.sos.mn.gov/elections-voting/election-day-voting/where-do-i-vote/).

Minnesota precincts - April 2025 (6225 KB json)

| Congressional District                         | as of April 2025      |
| ---------------------------------------------- | --------------------- |
| District 1 (southern Minnesota)                | C.D. 1 (1062 KB json) |
| District 2 (south Metro)                       | C.D. 2 (383 KB json)  |
| District 3 (greater Hennepin County)           | C.D. 3 (341 KB json)  |
| District 4 (Ramsey County and suburbs)         | C.D. 4 (217 KB json)  |
| District 5 (Minneapolis and suburbs)           | C.D. 5 (171 KB json)  |
| District 6 (northwestern Metro, St Cloud area) | C.D. 6 (578 KB json)  |
| District 7 (western Minnesota)                 | C.D. 7 (1760 KB json) |
| District 8 (northeastern Minnesota)            | C.D. 8 (1720 KB json) |
