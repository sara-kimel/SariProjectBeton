"""
בדיקת בריאות בסיסית — מוודאת שהאפליקציה עולה ושתי נקודות ה-health עונות 200.
לא נדרש חיבור DB.
"""


def test_root_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
