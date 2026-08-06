from app.extensions import db
from app.models import User, UserRole


def test_health(client):
    assert client.get("/api/health").json["status"] == "ok"


def test_register_login_and_profile(client):
    payload = {"email":"new@example.com", "password":"verysecure1", "firstName":"New", "lastName":"User"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    token = response.json["accessToken"]
    assert client.get("/api/auth/me", headers={"Authorization":f"Bearer {token}"}).json["user"]["email"] == payload["email"]
    assert client.post("/api/auth/login", json={"email":payload["email"], "password":payload["password"]}).status_code == 200
    refreshed = client.post("/api/auth/refresh", headers={"Authorization":f"Bearer {response.json['refreshToken']}"})
    assert refreshed.status_code == 200
    assert refreshed.json["accessToken"]


def test_normal_user_cannot_access_agent_api(client, app):
    response = client.post("/api/auth/register", json={"email":"user@example.com", "password":"verysecure1", "firstName":"Normal", "lastName":"User"})
    result = client.get("/api/agent/overview", headers={"Authorization":f"Bearer {response.json['accessToken']}"})
    assert result.status_code == 403


def authenticate(client, email, role):
    with client.application.app_context():
        user = User(email=email, first_name=role.value.title(), last_name="Tester", role=role)
        user.set_password("verysecure1"); db.session.add(user); db.session.commit()
    response = client.post("/api/auth/login", json={"email":email, "password":"verysecure1"})
    return {"Authorization":f"Bearer {response.json['accessToken']}"}


def test_agent_can_create_property(client):
    headers = authenticate(client, "agent@example.com", UserRole.AGENT)
    payload = {"title":"A carefully designed home", "description":"A detailed and convincing property description.", "price":125000, "purpose":"sale", "propertyType":"apartment", "city":"Prishtina", "address":"Ulpiana", "areaSqm":95, "bedrooms":2, "bathrooms":1, "amenities":["Balcony", "Elevator"], "images":[]}
    response = client.post("/api/agent/properties", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json["property"]["title"] == payload["title"]
    assert response.json["property"]["amenities"] == payload["amenities"]


def test_agent_cannot_delete_another_agents_property(client):
    first = authenticate(client, "first@example.com", UserRole.AGENT)
    second = authenticate(client, "second@example.com", UserRole.AGENT)
    payload = {"title":"Protected listing", "description":"This listing belongs exclusively to the first agent.", "price":99000, "purpose":"sale", "propertyType":"house", "city":"Peja", "address":"Centre", "areaSqm":120, "images":[]}
    property_id = client.post("/api/agent/properties", json=payload, headers=first).json["property"]["id"]
    assert client.delete(f"/api/agent/properties/{property_id}", headers=second).status_code == 403


def test_admin_approves_agent_application(client):
    user_headers = authenticate(client, "applicant@example.com", UserRole.USER)
    application = client.post("/api/account/agent-application", headers=user_headers, json={"fullName":"Applicant Tester", "email":"applicant@example.com", "phone":"123", "city":"Prishtina", "message":"I have relevant experience and want to join the platform."})
    admin_headers = authenticate(client, "admin@example.com", UserRole.ADMIN)
    reviewed = client.patch(f"/api/admin/agent-applications/{application.json['id']}", headers=admin_headers, json={"status":"approved"})
    assert reviewed.status_code == 200
    with client.application.app_context():
        assert db.session.scalar(db.select(User).where(User.email == "applicant@example.com")).role == UserRole.AGENT


def test_user_can_save_property_and_send_linked_inquiry(client):
    agent = authenticate(client, "inquiry-agent@example.com", UserRole.AGENT)
    payload = {"title":"Inquiry ready home", "description":"A complete listing that can receive a user inquiry.", "price":750, "purpose":"rent", "propertyType":"apartment", "city":"Prizren", "address":"Centre", "areaSqm":70, "images":[]}
    property_id = client.post("/api/agent/properties", json=payload, headers=agent).json["property"]["id"]
    user = authenticate(client, "buyer@example.com", UserRole.USER)
    assert client.put(f"/api/account/favorites/{property_id}", headers=user).status_code == 200
    assert client.get("/api/account/favorites", headers=user).json["items"][0]["id"] == property_id
    inquiry = client.post("/api/account/inquiries", headers=user, json={"propertyId":property_id, "message":"Could I arrange a viewing for this property?"})
    assert inquiry.status_code == 201
    assert client.get("/api/agent/inquiries", headers=agent).json["items"][0]["property"]["id"] == property_id


def test_agent_cannot_apply_again(client):
    headers = authenticate(client, "approved@example.com", UserRole.AGENT)
    response = client.post("/api/account/agent-application", headers=headers, json={"fullName":"Approved Agent", "email":"approved@example.com", "phone":"123", "city":"Peja", "message":"This application should be rejected by role validation."})
    assert response.status_code == 409
