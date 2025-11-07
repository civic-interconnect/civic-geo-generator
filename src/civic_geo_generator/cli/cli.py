# src/civic_geo_generator/cli/cli.py
"""CLI for civic-gen.

Commands:
  civic-gen build --version 2025-04 [--state MN --view precincts]
  civic-gen validate --version 2025-04
  civic-gen index
  civic-gen run [STATE [views...]] | [-c path/to/config.yaml] | [-f inputs.yaml]
"""

import os
import sys

from civic_lib_core import log_utils
import typer

from civic_geo_generator import index, validate
from civic_geo_generator.build.pipeline import build as build_fn
from civic_geo_generator.cli.run import run_main
from civic_geo_generator.utils.paths import get_state_lowercase_parts

logger = log_utils.logger
app = typer.Typer(add_completion=False, help="civic-gen CLI")

# Shared Typer params
STATE_ARG = typer.Argument(
    None, help="2-letter state code, name, or FIPS (e.g., MN, Minnesota, 27)"
)
VIEWS_ARG = typer.Argument(None, help="Optional views to run (e.g., precincts)")
CONFIG_OPT = typer.Option(None, "--config", "-c", help="Explicit config YAML; bypass inputs.yaml")
INPUTS_OPT = typer.Option(
    None, "--inputs", "-f", help="Path to inputs.yaml (default: ./inputs.yaml)"
)

DEFAULT_STATE = "MN"
DEFAULT_VIEW = "precincts"


def _resolve_state_view(state_opt: str | None, view_opt: str | None) -> tuple[str, str]:
    """Resolve state (uppercase 2-letter abbr) and view (lowercase).

    Uses the following resolution order:
    1) explicit options if provided,
    2) env vars CIVIC_STATE_CODE / CIVIC_STATE_NAME and CIVIC_VIEW,
    3) defaults (MN / precincts).
    """
    raw_state = (
        state_opt or os.getenv("CIVIC_STATE_CODE") or os.getenv("CIVIC_STATE_NAME") or DEFAULT_STATE
    )
    abbr_lc, _ = get_state_lowercase_parts(raw_state)
    state_uc = abbr_lc.upper()

    view = (view_opt or os.getenv("CIVIC_VIEW") or DEFAULT_VIEW).strip().lower()
    return state_uc, view


@app.command("build")
def cmd_build(
    version: str = typer.Option(..., "--version", "-v", help="Snapshot tag like 2025-04"),
    state: str | None = typer.Option(
        None, "--state", "-s", help="State code/name/FIPS (default from env or MN)"
    ),
    view: str | None = typer.Option(
        None, "--view", "-w", help="View (default from env or 'precincts')"
    ),
) -> None:
    """Build a layer for the given snapshot version.

    Examples:
      civic-gen build --version 2025-04
      civic-gen build --version 2025-04 --state MN --view precincts
    """
    state_uc, view_key = _resolve_state_view(state, view)
    code = build_fn(state_uc, view_key, version=version)
    raise typer.Exit(code)


@app.command("validate")
def cmd_validate(
    version: str = typer.Option(..., "--version", "-v", help="Snapshot tag like 2025-04"),
) -> None:
    """Validate generated outputs for the given snapshot version.

    Uses state/view from env (or defaults) consistent with validate module.
    """
    code = validate.main(version=version)
    raise typer.Exit(code)


@app.command("index")
def cmd_index() -> None:
    """Scan data-out and write flat index, manifest, and per-state indexes."""
    code = index.main()
    raise typer.Exit(code)


@app.command("run")
def cmd_run(
    state: str | None = STATE_ARG,
    views: list[str] | None = VIEWS_ARG,
    config: str | None = CONFIG_OPT,
    inputs: str | None = INPUTS_OPT,
) -> None:
    """Orchestrate builds via inputs.yaml, explicit state/views, or config file.

    Supports three modes:
      - inputs.yaml (-f),
      - explicit state and optional views,
      - or a single config file (-c).

    Examples:
      civic-gen run -f inputs.yaml
      civic-gen run MN precincts
      civic-gen run -c data-config/us/mn/precincts.yaml
    """
    code = run_main(
        inputs_path=inputs,
        state_arg=state,
        views_args=views,
        config_path=config,
    )
    raise typer.Exit(code)


def main() -> int:
    """Entrypoint for the Civic Gen CLI."""
    try:
        app()
        return 0
    except Exception as exc:
        logger.error(f"CLI error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
