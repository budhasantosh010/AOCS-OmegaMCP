"""Tests for config loader."""

import json
import tempfile
import os
from aocs_mcp.config import Config


def test_config_loads_defaults():
    """Config should have host_cli and roles sections."""
    cfg = Config()
    assert cfg.host_cli_config() is not None
    assert "enabled" in cfg.host_cli_config()
    assert cfg.get("roles") is not None
    assert "classifier" in cfg.get("roles", {})


def test_config_role_lookup():
    cfg = Config()
    role = cfg.get_role("specialist")
    assert role is not None
    assert "mode" in role


def test_config_contains_every_runtime_model_role():
    cfg = Config()
    roles = cfg.get("roles", {})
    required = {
        "direct-answer",
        "classifier",
        "scoring-engine",
        "multi-framer",
        "root-problem",
        "deep-test",
        "type1-specialist",
        "specialist",
        "prover",
        "tmr",
        "tmr-judge",
        "red-team",
        "contrarian",
        "deception-detector",
        "judge",
        "observer",
        "shadow-orchestrator",
        "blindspot-hunter",
        "fractal-observer",
        "fractal-shadow",
        "chaos-reconsideration",
        "type3-lens",
        "type3-first-principles",
        "type3-hypothesis",
        "idea-mutator",
        "ruthless-pruner",
        "serendipity-injector",
        "thought-simulator",
        "paradigm-detector",
        "universal-goal-assembly",
        "inefficiency-hunter",
        "analogical-mining",
        "higher-dimension",
        "future-backcast",
        "break-framework",
        "swarm-worker",
        "swarm-peer-audit",
        "swarm-auditor",
        "swarm-synthesis",
    }

    assert required - set(roles) == set()


def test_config_merges_local():
    """Local config should override defaults."""
    with tempfile.TemporaryDirectory() as tmp:
        # Write default
        default = {"host_cli": {"enabled": True}, "roles": {"test-role": {"mode": "host-cli"}}}
        with open(os.path.join(tmp, "models.default.json"), "w") as f:
            json.dump(default, f)

        # Write local override
        local = {"roles": {"test-role": {"mode": "direct-api"}}}
        with open(os.path.join(tmp, "models.local.json"), "w") as f:
            json.dump(local, f)

        cfg = Config(config_dir=tmp)
        assert cfg.get_role("test-role")["mode"] == "direct-api"


def test_config_missing_file():
    """Config should handle missing files gracefully."""
    cfg = Config(config_dir="/nonexistent/path")
    assert cfg.get("host_cli") is None
    assert cfg.get_role("anything") == {}


if __name__ == "__main__":
    test_config_loads_defaults()
    test_config_role_lookup()
    test_config_merges_local()
    test_config_missing_file()
    print("All config tests passed!")
