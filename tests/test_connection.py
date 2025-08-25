class TestConnection:

    def test_api_connection(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Api is working!"

    def test_db_connection(self, client):
        resp = client.get("/health-check")
        assert resp.status_code == 200
        assert "PostgreSQL" in resp.json()["detail"]
