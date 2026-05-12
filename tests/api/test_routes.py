from app.main import app


def test_auth_and_account_routes_are_separated():
    paths = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/accounts" in paths
    assert "/api/v1/accounts/{account_id}" in paths
    assert "/api/v1/auth/accounts" not in paths
