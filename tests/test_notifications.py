"""Tests for background assignment notifications and the notifications API."""


async def _create_project_with_two_members(client, register_and_login):
    owner_headers = await register_and_login("owner@example.com")
    member_headers = await register_and_login("member@example.com")

    created = await client.post("/projects", json={"name": "Shared"}, headers=owner_headers)
    project_id = created.json()["id"]
    await client.post(
        f"/projects/{project_id}/members",
        json={"email": "member@example.com"},
        headers=owner_headers,
    )

    member_id = (await client.get("/auth/me", headers=member_headers)).json()["id"]
    return project_id, owner_headers, member_headers, member_id


async def test_creating_a_task_with_an_assignee_notifies_them(client, register_and_login):
    project_id, owner_headers, member_headers, member_id = await _create_project_with_two_members(
        client, register_and_login
    )

    await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Review PR", "assignee_id": member_id},
        headers=owner_headers,
    )

    response = await client.get("/notifications", headers=member_headers)
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert "Review PR" in notifications[0]["message"]
    assert notifications[0]["read"] is False


async def test_creating_a_task_without_an_assignee_notifies_no_one(client, register_and_login):
    project_id, owner_headers, member_headers, _ = await _create_project_with_two_members(
        client, register_and_login
    )

    await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Unassigned task"}, headers=owner_headers
    )

    response = await client.get("/notifications", headers=member_headers)
    assert response.json() == []


async def test_assigning_an_existing_task_notifies_the_new_assignee(client, register_and_login):
    project_id, owner_headers, member_headers, member_id = await _create_project_with_two_members(
        client, register_and_login
    )

    created = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Fix bug"}, headers=owner_headers
    )
    task_id = created.json()["id"]

    await client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        json={"assignee_id": member_id},
        headers=owner_headers,
    )

    response = await client.get("/notifications", headers=member_headers)
    assert len(response.json()) == 1


async def test_mark_notification_read(client, register_and_login):
    project_id, owner_headers, member_headers, member_id = await _create_project_with_two_members(
        client, register_and_login
    )
    await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Review PR", "assignee_id": member_id},
        headers=owner_headers,
    )
    notification_id = (await client.get("/notifications", headers=member_headers)).json()[0]["id"]

    response = await client.post(
        f"/notifications/{notification_id}/read", headers=member_headers
    )
    assert response.status_code == 200
    assert response.json()["read"] is True


async def test_cannot_mark_someone_elses_notification_read(client, register_and_login):
    project_id, owner_headers, member_headers, member_id = await _create_project_with_two_members(
        client, register_and_login
    )
    await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Review PR", "assignee_id": member_id},
        headers=owner_headers,
    )
    notification_id = (await client.get("/notifications", headers=member_headers)).json()[0]["id"]

    response = await client.post(
        f"/notifications/{notification_id}/read", headers=owner_headers
    )
    assert response.status_code == 404
