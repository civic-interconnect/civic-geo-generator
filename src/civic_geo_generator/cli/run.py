# src/civic_geo_generator/cli/run.py
"""Command-line interface for running geo generator operations.

This module provides the main CLI entry point for orchestrating geo generation
workflows including building, validation, and indexing operations. It supports
both single-run and batch processing modes using configuration files.

Functions:
    run_main: Main orchestration function that coordinates build/validate/index operations
    _discover_views_for_state: Auto-discover available views for a given state
    _config_path_for: Generate config file path for state/view combination
    _read_build_version_from_yaml: Extract build version from YAML config
    _load_inputs_yaml: Load and validate inputs.yaml configuration
    _iter_runs: Parse run specifications from configuration
"""

from pathlib import Path

from civic_lib_core import log_utils
import yaml

from civic_geo_generator.build import build
from civic_geo_generator.index import main as index_main
from civic_geo_generator.utils.paths import resolve_config_path
from civic_geo_generator.validate import main as check_main


def _config_path_for(state: str, view: str) -> Path:
    """Resolve config path for state/view using new->legacy search."""
    try:
        return resolve_config_path(state, view, config_root=None)
    except FileNotFoundError:
        return Path("data-config") / f"us_{state.lower()}_{view}.yaml"


def _discover_views_for_state(state: str) -> list[str]:
    """Discover views by scanning new and legacy config layouts."""
    sl = state.lower()
    views: list[str] = []

    # layout: data-config/us/{state}/{view}.yaml
    base_new = Path("data-config") / "us" / sl
    if base_new.exists():
        for p in sorted(base_new.glob("*.yaml")):
            views.append(p.stem)  # filename == view

    # de-dup, preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for v in views:
        if v not in seen:
            uniq.append(v)
            seen.add(v)
    return uniq


def _err(msg: str) -> None:
    log_utils.logger.error(msg)


def _iter_runs(spec: dict) -> list[dict]:
    """Supports run configuration parsing.

    1) batch mode:
       runs:
         - state: MN
           views: [precincts]
           version_overrides:
             precincts: "2025-04"
    2) simple mode (no 'runs' key):
       state: MN
       views: [precincts]
       version_overrides: {...}
    """
    if "runs" in spec and isinstance(spec["runs"], list) and spec["runs"]:
        return spec["runs"]
    # simple mode fallback
    simple = {}
    for k in ("state", "views", "version_overrides"):
        if k in spec:
            simple[k] = spec[k]
    if not simple:
        raise ValueError("inputs.yaml must contain either 'runs' or a top-level 'state'")
    return [simple]


def _load_inputs_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError("inputs.yaml not found at repo root")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("inputs.yaml must parse to a mapping")
    return data


def _norm_state(s: str) -> str:
    s = (s or "").strip().upper()
    if len(s) != 2:
        raise ValueError("state must be a 2-letter code, e.g., MN")
    return s


def _read_build_version_from_yaml(cfg_path: Path) -> str | None:
    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        build = data.get("build") or {}
        ver = build.get("version")
        if ver:
            return str(ver)
    except Exception as e:
        _err(f"[warn] failed to read version from {cfg_path}: {e}")
    return None


def _run_with_config(config_path: str) -> int:
    cfg = Path(config_path)
    if not cfg.exists():
        _err(f"[error] config not found: {cfg}")
        return 2

    # Extract state and view from config filename
    stem = cfg.stem
    parts = stem.split("_", 2)

    if len(parts) != 3 or parts[0] != "us":
        _err(f"[error] config filename must be us_{{state}}_{{view}}.yaml format: {cfg.name}")
        return 2

    state = parts[1].upper()
    view = parts[2]
    version = _read_build_version_from_yaml(cfg)

    _err(f"[run] state={state} view={view} version={version or '(default)'} cfg={cfg}")

    code = 0
    code |= build(state, view, version=version)
    if version:
        code |= check_main(version=version)
    code |= index_main()
    return code


def _run_with_inputs(inputs_path: str | None) -> int:
    inputs_file = Path(inputs_path) if inputs_path else Path("inputs.yaml")
    log_utils.logger.debug(f"Loading inputs from {inputs_file}")

    spec = _load_inputs_yaml(inputs_file)
    runs = _iter_runs(spec)

    overall = 0
    base_root = inputs_file.parent
    for run in runs:
        try:
            state = _norm_state(str(run.get("state", "")).strip())
        except Exception as e:
            _err(f"[error] {e}")
            overall |= 2
            continue

        views = run.get("views") or _discover_views_for_state(state)
        if not views:
            _err(f"[skip] no configs found for state {state}")
            overall |= 1
            continue

        version_overrides: dict = run.get("version_overrides") or {}
        last_cfg: Path | None = None
        for view in views:
            try:
                cfg: Path = resolve_config_path(state, view, config_root=base_root)
            except FileNotFoundError:
                _err(f"[skip] missing config for {state} {view}: {_config_path_for(state, view)}")
                overall |= 1
                continue

            version = version_overrides.get(view) or _read_build_version_from_yaml(cfg)
            overall |= build(state, view, version=version)
            if version:
                overall |= check_main(version=version)
            last_cfg = cfg

        if last_cfg:
            overall |= index_main()

    return overall


def _run_with_state(state_arg: str, views_args: list[str] | None) -> int:
    try:
        state = _norm_state(state_arg)
    except Exception as e:
        _err(f"[error] {e}")
        return 2

    views = views_args or _discover_views_for_state(state)
    if not views:
        _err(f"[skip] no configs found for state {state}")
        return 1

    overall = 0
    last_cfg: Path | None = None
    for view in views:
        try:
            cfg = resolve_config_path(state, view, config_root=None)
        except FileNotFoundError:
            _err(f"[skip] missing config for {state} {view}: {_config_path_for(state, view)}")
            overall |= 1
            continue
        version = _read_build_version_from_yaml(cfg)
        _err(f"[run] state={state} view={view} version={version or '(default)'} cfg={cfg}")
        overall |= build(state, view, version=version)
        if version:
            overall |= check_main(version=version)
        last_cfg = cfg

    if last_cfg:
        overall |= index_main()
    return overall


def run_main(
    inputs_path: str | None = None,
    state_arg: str | None = None,
    views_args: list[str] | None = None,
    config_path: str | None = None,
) -> int:
    """Orchestrates existing build/validate/index using inputs.yaml or args.

    Priority:
      1) explicit config_path (runs build/check/index once)
      2) state_arg (+ optional views_args)
      3) inputs.yaml at repo root
    """
    if config_path:
        return _run_with_config(config_path)
    if state_arg:
        return _run_with_state(state_arg, views_args)
    return _run_with_inputs(inputs_path)
