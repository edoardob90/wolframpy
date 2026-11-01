import pytest

from tests.configure import CONFIG_ENV_VAR, DATA_DIR, get_config


@pytest.fixture
def data_dir():
    """Path to ``tests/data``."""
    return DATA_DIR


def pytest_collection_modifyitems(config, items):
    test_config = get_config()
    skip_kernel = pytest.mark.skip(
        reason=f"no 'kernel' path configured (set {CONFIG_ENV_VAR})"
    )
    skip_cloud = pytest.mark.skip(
        reason=f"no cloud credentials configured (set {CONFIG_ENV_VAR})"
    )
    for item in items:
        if "kernel" in item.keywords and not test_config.has_kernel:
            item.add_marker(skip_kernel)
        if "cloud" in item.keywords and not test_config.has_cloud:
            item.add_marker(skip_cloud)
