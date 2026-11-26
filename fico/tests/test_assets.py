import pytest


@pytest.mark.parametrize(
    "url",
    [
        "/assets/common.js",
        "/assets/..%2F__init__.py",
        "/assets/%2E%2E%2Fmain.py",
        "/assets/..%5Cmain.py",
    ],
)
def test_only_versioned_assets_are_served(client, url):
    assert client.get(url).status_code == 404
