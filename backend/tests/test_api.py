from app.extensions import db
from app.models import AgentApplication, Conversation, ConversationMessage, Favorite, Property, PropertyImage, User, UserRole
from app.seed import seed_database


def test_health(client):
    assert client.get("/api/health").json["status"] == "ok"


def test_demo_seed_is_repeatable_and_complete(app):
    with app.app_context():
        seed_database()
        seed_database()
        assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 12
        assert db.session.scalar(db.select(db.func.count()).select_from(Property)) == 28
        assert db.session.scalar(db.select(db.func.count()).select_from(Favorite)) == 22
        assert db.session.scalar(db.select(db.func.count()).select_from(Conversation)) == 9
        assert db.session.scalar(db.select(db.func.count()).select_from(ConversationMessage)) == 35
        assert db.session.scalar(db.select(db.func.count()).select_from(AgentApplication)) == 3
        assert db.session.scalar(db.select(db.func.count()).select_from(PropertyImage)) == 50
        assert db.session.scalar(db.select(db.func.count(db.func.distinct(PropertyImage.url)))) == 50
        galleries = (
            db.select(PropertyImage.property_id)
            .group_by(PropertyImage.property_id)
            .having(db.func.count(PropertyImage.id) > 1)
            .subquery()
        )
        assert db.session.scalar(db.select(db.func.count()).select_from(galleries)) == 9


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


def test_admin_can_create_property_for_active_agent(client):
    agent = authenticate(client, "assigned-agent@example.com", UserRole.AGENT)
    admin = authenticate(client, "property-admin@example.com", UserRole.ADMIN)
    with client.application.app_context():
        agent_id = db.session.scalar(db.select(User.id).where(User.email == "assigned-agent@example.com"))
    payload = {"title":"Admin-created listing", "description":"A complete listing created by an administrator for an agent.", "price":175000, "purpose":"sale", "propertyType":"house", "city":"Prishtina", "address":"Dardania", "areaSqm":130, "amenities":["Parking"], "images":[], "agentId":agent_id}
    response = client.post("/api/admin/properties", json=payload, headers=admin)
    assert response.status_code == 201
    assert response.json["property"]["agent"]["id"] == agent_id
    assert any(item["id"] == response.json["property"]["id"] for item in client.get("/api/agent/properties", headers=agent).json["items"])
    assert any(item["id"] == response.json["property"]["id"] for item in client.get("/api/admin/properties", headers=admin).json["items"])


def test_admin_property_creation_requires_valid_agent(client):
    admin = authenticate(client, "validation-admin@example.com", UserRole.ADMIN)
    user = authenticate(client, "not-an-agent@example.com", UserRole.USER)
    payload = {"title":"Invalid owner listing", "description":"A complete listing that must not be assigned to a normal user.", "price":100000, "purpose":"sale", "propertyType":"apartment", "city":"Peja", "address":"Centre", "areaSqm":80, "images":[]}
    with client.application.app_context():
        user_id = db.session.scalar(db.select(User.id).where(User.email == "not-an-agent@example.com"))
    assert client.post("/api/admin/properties", json=payload | {"agentId":user_id}, headers=admin).status_code == 400
    assert client.post("/api/admin/properties", json=payload, headers=user).status_code == 403


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


def test_agent_application_identity_comes_from_authenticated_user(client):
    headers = authenticate(client, "identity@example.com", UserRole.USER)
    response = client.post("/api/account/agent-application", headers=headers, json={"fullName":"Impersonated Person", "email":"someone-else@example.com", "phone":"123", "city":"Prishtina", "message":"My authenticated identity must be used for this application."})
    assert response.status_code == 201
    with client.application.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "identity@example.com"))
        application = db.session.get(AgentApplication, response.json["id"])
        assert application.user_id == user.id
        assert application.email == user.email
        assert application.full_name == user.full_name


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


def test_password_change_verifies_current_password(client):
    headers = authenticate(client, "password@example.com", UserRole.USER)
    wrong = client.post("/api/account/change-password", headers=headers, json={"currentPassword":"wrong", "newPassword":"NewPassword123!"})
    assert wrong.status_code == 400
    changed = client.post("/api/account/change-password", headers=headers, json={"currentPassword":"verysecure1", "newPassword":"NewPassword123!"})
    assert changed.status_code == 200
    assert client.post("/api/auth/login", json={"email":"password@example.com", "password":"NewPassword123!"}).status_code == 200


def test_conversation_reply_authorization_and_unread(client):
    agent = authenticate(client, "conversation-agent@example.com", UserRole.AGENT)
    prop = client.post("/api/agent/properties", headers=agent, json={"title":"Conversation home", "description":"A listing for conversation authorization coverage.", "price":100000, "purpose":"sale", "propertyType":"house", "city":"Peja", "address":"Centre", "areaSqm":100, "images":[]}).json["property"]
    user = authenticate(client, "conversation-user@example.com", UserRole.USER)
    conversation_id = client.post("/api/account/inquiries", headers=user, json={"propertyId":prop["id"], "message":"I would like more details about this listing."}).json["id"]
    assert client.get("/api/account/unread-count", headers=agent).json["count"] == 1
    detail = client.get(f"/api/account/conversations/{conversation_id}", headers=agent)
    assert detail.status_code == 200
    assert client.get("/api/account/unread-count", headers=agent).json["count"] == 0
    assert client.post(f"/api/account/conversations/{conversation_id}/messages", headers=agent, json={"message":"I would be happy to help."}).status_code == 201
    assert client.get("/api/account/unread-count", headers=user).json["count"] == 1


def test_admin_role_edit_updates_overview(client):
    user_headers = authenticate(client, "promote@example.com", UserRole.USER)
    assert user_headers
    admin = authenticate(client, "role-admin@example.com", UserRole.ADMIN)
    users = client.get("/api/admin/users", headers=admin).json["items"]
    target = next(item for item in users if item["email"] == "promote@example.com")
    before = client.get("/api/admin/overview", headers=admin).json["totalAgents"]
    assert client.patch(f"/api/admin/users/{target['id']}", headers=admin, json={"role":"agent"}).status_code == 200
    assert client.get("/api/admin/overview", headers=admin).json["totalAgents"] == before + 1


def test_agent_cannot_apply_again(client):
    headers = authenticate(client, "approved@example.com", UserRole.AGENT)
    response = client.post("/api/account/agent-application", headers=headers, json={"fullName":"Approved Agent", "email":"approved@example.com", "phone":"123", "city":"Peja", "message":"This application should be rejected by role validation."})
    assert response.status_code == 409


def test_admin_cannot_apply_as_agent(client):
    headers = authenticate(client, "application-admin@example.com", UserRole.ADMIN)
    response = client.post("/api/account/agent-application", headers=headers, json={"phone":"123", "city":"Peja", "message":"Administrators must not create agent applications."})
    assert response.status_code == 409
    assert "Administrator" in response.json["error"]["message"]


def test_admin_transfers_property_ownership_and_authorization(client):
    first = authenticate(client, "owner-a@example.com", UserRole.AGENT)
    second = authenticate(client, "owner-b@example.com", UserRole.AGENT)
    admin = authenticate(client, "transfer-admin@example.com", UserRole.ADMIN)
    payload = {"title":"Transferable listing", "description":"A complete listing used to verify secure ownership transfer.", "price":150000, "purpose":"sale", "propertyType":"house", "city":"Prishtina", "address":"Centre", "areaSqm":140, "images":[]}
    item = client.post("/api/agent/properties", headers=first, json=payload).json["property"]
    with client.application.app_context():
        new_owner = db.session.scalar(db.select(User).where(User.email == "owner-b@example.com"))
        new_owner_id = new_owner.id
    updated = client.patch(f"/api/agent/properties/{item['id']}", headers=admin, json=payload | {"agentId":new_owner_id, "status":"active"})
    assert updated.status_code == 200
    assert all(row["id"] != item["id"] for row in client.get("/api/agent/properties", headers=first).json["items"])
    assert any(row["id"] == item["id"] for row in client.get("/api/agent/properties", headers=second).json["items"])
    assert client.patch(f"/api/agent/properties/{item['id']}", headers=first, json=payload).status_code == 403
    assert client.patch(f"/api/agent/properties/{item['id']}", headers=second, json=payload).status_code == 200
