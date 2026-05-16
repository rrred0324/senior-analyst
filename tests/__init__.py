"""pytest tests for senior_analyst sources and CLI.

Run from project root:
    ./venv/bin/python -m pytest tests/ -v
    ./venv/bin/python -m pytest tests/ -v -m "not network"  # skip network tests

Tests are split into:
  - unit (no network, fast)
  - network (real HTTP calls, slow, may flake)

Configure with markers in pytest.ini.
"""
