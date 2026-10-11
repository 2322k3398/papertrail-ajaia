import os
import tempfile
import pytest
import app as papertrail

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(papertrail, "DB_PATH", str(db_path))
    papertrail.init_db()
    papertrail.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with papertrail.app.test_client() as client:
        yield client

def login_as(client, email="vishnupriya200636@gmail.com"):
    return client.post("/login", data={"email": email}, follow_redirects=True)

def test_create_and_save_document_persists(client):
    login_as(client)
    response = client.post("/documents/new", data={"title": "Test notes"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test notes" in response.data
    with papertrail.connect_db() as db:
        doc = db.execute("SELECT * FROM documents WHERE title='Test notes'").fetchone()
    assert doc is not None
    saved = client.put(f"/api/documents/{doc['id']}", json={
        "title": "Renamed notes", "content": "<h1>Hello</h1>"
    })
    assert saved.status_code == 200
    with papertrail.connect_db() as db:
        updated = db.execute("SELECT * FROM documents WHERE id=?", (doc["id"],)).fetchone()
    assert updated["title"] == "Renamed notes"
    assert updated["content"] == "<h1>Hello</h1>"

def test_sharing_grants_access_to_another_seeded_user(client):
    login_as(client)
    client.post("/documents/new", data={"title": "Shared notes"}, follow_redirects=True)
    with papertrail.connect_db() as db:
        doc = db.execute("SELECT * FROM documents WHERE title='Shared notes'").fetchone()
    client.post(f"/documents/{doc['id']}/share",
                data={"email": "alex@example.com", "permission": "view"},
                follow_redirects=True)
    client.post("/logout", follow_redirects=True)
    login_as(client, "alex@example.com")
    response = client.get(f"/documents/{doc['id']}")
    assert response.status_code == 200
    assert b"VIEW ONLY" in response.data
    denied = client.put(f"/api/documents/{doc['id']}", json={"content": "No"})
    assert denied.status_code == 403
