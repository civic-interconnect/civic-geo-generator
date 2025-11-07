from civic_geo_generator.cli import run


def test_run_uses_inputs_yaml(tmp_path, monkeypatch):
    """Test that run command processes inputs.yaml correctly."""
    import yaml

    # inputs.yaml next to config
    inputs = {"state": "MN", "views": ["precincts"], "version_overrides": {"precincts": "2025-04"}}
    inputs_file = tmp_path / "inputs.yaml"
    inputs_file.write_text(yaml.dump(inputs))

    # make config/us/mn/precincts.yaml
    config_dir = tmp_path / "config" / "us" / "mn"
    config_dir.mkdir(parents=True)
    (config_dir / "precincts.yaml").write_text(yaml.dump({"build": {"version": "2025-04"}}))

    # record calls
    build_called = []

    def mock_build(state, view, version=None):
        build_called.append((state, view, version))
        return 0

    #  mock the name used inside run.py
    monkeypatch.setattr(run, "build", mock_build)

    # stub other side effects
    monkeypatch.setattr(run, "check_main", lambda version: 0)
    monkeypatch.setattr(run, "index_main", lambda: 0)

    # run relative to tmp
    monkeypatch.chdir(tmp_path)

    result = run.run_main(inputs_path=str(inputs_file))
    assert result == 0
    assert build_called == [("MN", "precincts", "2025-04")]
