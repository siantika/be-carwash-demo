from app.main import app


def test_auth_and_account_routes_are_separated():
    paths = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/logout" in paths
    assert "/api/v1/accounts" in paths
    assert "/api/v1/accounts/{account_id}" in paths
    assert "/api/v1/service-types" in paths
    assert "/api/v1/service-types/{service_type_id}" in paths
    assert "/api/v1/service-types/{service_type_id}/activate" in paths
    assert "/api/v1/service-types/{service_type_id}/deactivate" in paths
    assert "/api/v1/tickets" in paths
    assert "/api/v1/tickets/{ticket_id}/void" in paths
    assert "/api/v1/transactions" in paths
    assert "/api/v1/auth/accounts" not in paths
