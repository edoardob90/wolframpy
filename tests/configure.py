"""Test configuration, read lazily from ``WOLFRAMCLIENT_PY_JSON_CONFIG``.

The JSON file (see ``local_config_sample.json``) may define a local ``kernel`` path,
``cloud_credentials``, a ``server`` and an ``ApiOwner``. Nothing is read until one of
the attributes below is first accessed, so importing this module has no side effects.

Module attributes (resolved on first access):
``json_config``, ``secured_authentication_key``, ``user_configuration``, ``server``,
``kernel_path``, ``api_owner``.
"""

import functools
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from wolframclient.utils.logger import setup_logging_to_file

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

CONFIG_ENV_VAR = "WOLFRAMCLIENT_PY_JSON_CONFIG"
LOG_FILE_ENV_VAR = "WOLFRAMCLIENT_PY_LOG_FILE"


def dir_test_data():
    """Return path to the data directory in tests"""
    return DATA_DIR


def path_to_file_in_data_dir(*args):
    return os.path.join(DATA_DIR, *args)


def create_dir_if_missing(path):
    """Create the parent directory of the file at `path` if it does not exist."""
    file_dir = os.path.dirname(path)
    if file_dir and not os.path.exists(file_dir):
        os.makedirs(file_dir)


@dataclass(frozen=True)
class Config:
    json_config: dict | None = None
    secured_authentication_key: Any = None
    user_configuration: Any = None
    server: Any = None
    kernel_path: str | None = None
    api_owner: str | None = None

    @property
    def has_kernel(self):
        return bool(self.kernel_path)

    @property
    def has_cloud(self):
        return self.secured_authentication_key is not None


def _parse_config(config):
    sak = None
    user_cred = None
    server = None
    try:
        cloud_config = config["cloud_credentials"]
        try:
            from wolframclient.evaluation import SecuredAuthenticationKey

            sak = SecuredAuthenticationKey(
                cloud_config["SAK"]["consumer_key"], cloud_config["SAK"]["consumer_secret"]
            )
        except KeyError as e:
            logger.warning("Failed to read SAK from json config: %s", e)
        from wolframclient.evaluation import UserIDPassword

        if "User" in cloud_config:
            user_cred = UserIDPassword(
                cloud_config["User"]["id"], cloud_config["User"]["password"]
            )
    except KeyError as e:
        logger.warning("Failed to parse cloud credentials from json config: %s", e)
    try:
        from wolframclient.evaluation import WolframServer

        server_json = config["server"]
        server = WolframServer(
            server_json["host"],
            server_json["request_token_endpoint"],
            server_json["access_token_endpoint"],
            xauth_consumer_key=server_json.get("xauth_consumer_key", None),
            xauth_consumer_secret=server_json.get("xauth_consumer_secret", None),
            certificate=server_json.get("certificate", None),
        )
    except KeyError as e:
        logger.warning("Failed to parse server from json config: %s", e)

    return Config(
        json_config=config,
        secured_authentication_key=sak,
        user_configuration=user_cred,
        server=server,
        kernel_path=config.get("kernel", None),
        api_owner=config.get("ApiOwner", None),
    )


@functools.cache
def get_config():
    """Load and cache the test configuration. Returns an empty `Config` if unset."""
    log_file = os.environ.get(LOG_FILE_ENV_VAR)
    if log_file is not None:
        create_dir_if_missing(log_file)
        setup_logging_to_file(log_file)

    config_path = os.environ.get(CONFIG_ENV_VAR)
    if not config_path:
        return Config()
    expanded_path = os.path.expanduser(os.path.expandvars(config_path))
    try:
        with open(expanded_path) as fp:
            json_config = json.load(fp)
    except OSError as e:
        raise ValueError(f"Failed to read json configuration file {config_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid json in configuration file {config_path}: {e}") from e
    return _parse_config(json_config)


_CONFIG_ATTRIBUTES = frozenset(
    (
        "json_config",
        "secured_authentication_key",
        "user_configuration",
        "server",
        "kernel_path",
        "api_owner",
    )
)


def __getattr__(name):
    if name in _CONFIG_ATTRIBUTES:
        return getattr(get_config(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
