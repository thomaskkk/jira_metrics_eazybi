import json
from main import app

def test_index_route():
    response = app.test_client().get('/')

    res = json.loads(response.data.decode('utf-8')).get("message")
    assert response.status_code == 200
    assert res == "All ok!"

