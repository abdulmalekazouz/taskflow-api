"""Tests for project creation, listing, and membership management."""


async def test_create_project_makes_the_creator_the_owner(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    response = await client.post(
        "/projects", json={"name": "Launch", "description": "Q1 launch plan"}, headers=headers
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Launch"

    members_response = await client.get(f"/projects/{data['id']}/members", headers=headers)
    members = members_response.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"


async def test_create_project_requires_authentication(client):
    response = await client.post("/projects", json={"name": "No auth"})
    assert response.status_code == 401


async def test_list_projects_only_shows_projects_i_am_a_member_of(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    bob_headers = await register_and_login("bob@example.com")

    await client.post("/projects", json={"name": "Alice's project"}, headers=alice_headers)
    await client.post("/projects", json={"name": "Bob's project"}, headers=bob_headers)

    response = await client.get("/projects", headers=alice_headers)
    names = {project["name"] for project in response.json()}
    assert names == {"Alice's project"}


async def test_non_member_cannot_view_a_project(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    bob_headers = await register_and_login("bob@example.com")

    created = await client.post("/projects", json={"name": "Private"}, headers=alice_headers)
    project_id = created.json()["id"]

    response = await client.get(f"/projects/{project_id}", headers=bob_headers)
    assert response.status_code == 403


async def test_owner_can_add_a_member_by_email(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    await register_and_login("bob@example.com")

    created = await client.post("/projects", json={"name": "Shared"}, headers=alice_headers)
    project_id = created.json()["id"]

    response = await client.post(
        f"/projects/{project_id}/members", json={"email": "bob@example.com"}, headers=alice_headers
    )
    assert response.status_code == 201
    assert response.json()["role"] == "member"


async def test_non_owner_cannot_add_a_member(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    bob_headers = await register_and_login("bob@example.com")
    await register_and_login("carol@example.com")

    created = await client.post("/projects", json={"name": "Shared"}, headers=alice_headers)
    project_id = created.json()["id"]
    await client.post(
        f"/projects/{project_id}/members", json={"email": "bob@example.com"}, headers=alice_headers
    )

    response = await client.post(
        f"/projects/{project_id}/members",
        json={"email": "carol@example.com"},
        headers=bob_headers,
    )
    assert response.status_code == 403


async def test_adding_an_unknown_email_returns_404(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    created = await client.post("/projects", json={"name": "Shared"}, headers=alice_headers)
    project_id = created.json()["id"]

    response = await client.post(
        f"/projects/{project_id}/members",
        json={"email": "nobody@example.com"},
        headers=alice_headers,
    )
    assert response.status_code == 404


async def test_adding_the_same_member_twice_is_rejected(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    await register_and_login("bob@example.com")
    created = await client.post("/projects", json={"name": "Shared"}, headers=alice_headers)
    project_id = created.json()["id"]

    await client.post(
        f"/projects/{project_id}/members", json={"email": "bob@example.com"}, headers=alice_headers
    )
    response = await client.post(
        f"/projects/{project_id}/members", json={"email": "bob@example.com"}, headers=alice_headers
    )
    assert response.status_code == 400
