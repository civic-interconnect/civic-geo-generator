# test utils/get_paths.py

from civic_geo_generator.utils import paths


def test_get_data_in_dir():
    path = paths.get_data_in_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_data_out_dir():
    path = paths.get_data_out_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_tiger_in_dir():
    path = paths.get_tiger_in_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_states_out_dir():
    path = paths.get_states_out_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_national_out_dir():
    path = paths.get_national_out_dir()
    assert path.exists()
    assert path.is_dir()


def test_get_repo_root():
    path = paths.get_repo_root()
    assert path.exists()
    assert path.is_dir()


def test_get_config_roots():
    roots = paths.get_config_roots()
    assert isinstance(roots, list)
    assert all(isinstance(r, paths.Path) for r in roots)
    assert all(r.exists() and r.is_dir() for r in roots)


def test_resolve_config_path():
    state = "mn"
    view = "precincts"
    path = paths.resolve_config_path(state, view)
    assert path.exists()
    assert path.is_file()
    assert path.suffix == ".yaml"
