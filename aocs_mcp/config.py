"""Config loader — reads models.default.json + models.local.json."""

import json
import os

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")


class Config:
    """Merged config from default + local overrides."""

    def __init__(self, config_dir: str | None = None):
        self._config_dir = config_dir or _CONFIG_DIR
        self._data: dict = {}

        # Load defaults
        default_path = os.path.join(self._config_dir, "models.default.json")
        if os.path.isfile(default_path):
            with open(default_path) as f:
                self._data = json.load(f)

        # Merge local overrides
        local_path = os.path.join(self._config_dir, "models.local.json")
        if os.path.isfile(local_path):
            with open(local_path) as f:
                local = json.load(f)
            self._deep_merge(self._data, local)

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def get_role(self, role: str) -> dict:
        """Get config for a specific AOCS role."""
        roles = self._data.get("roles", {})
        return roles.get(role, {})

    def host_cli_config(self) -> dict:
        return self._data.get("host_cli", {})

    def direct_api_config(self) -> dict:
        return self._data.get("direct_api", {})

    def direct_api_key(self, provider: str) -> str | None:
        dc = self.direct_api_config()
        prov = dc.get(provider, {})
        return prov.get("api_key") or os.environ.get(f"{provider.upper()}_API_KEY")

    @property
    def data(self) -> dict:
        return self._data
