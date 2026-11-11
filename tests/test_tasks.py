"""Tests for task creation, listing/pagination/filtering, updates, and deletion."""


async def _create_project(client, headers, name="Project"):
    response = await client.post("/projects", json={"name": name}, headers=headers)
    return response.json()["id"]


async def test_create_task(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    project_id = await _create_project(client, headers)

    response = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Write README"}, headers=headers
    )
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Write README"
    assert data["status"] == "todo"
    assert data["project_id"] == project_id


async def test_non_member_cannot_create_a_task(client, register_and_login):
    alice_headers = await register_and_login("alice@example.com")
    bob_headers = await register_and_login("bob@example.com")
    project_id = await _create_project(client, alice_headers)

    response = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Sneaky task"}, headers=bob_headers
    )
    assert response.status_code == 403


async def test_update_task_partially_changes_only_given_fields(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    project_id = await _create_project(client, headers)
    created = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Write README", "description": "Initial draft"},
        headers=headers,
    )
    task_id = created.json()["id"]

    response = await client.patch(
        f"/projects/{project_id}/tasks/{task_id}", json={"status": "done"}, headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "done"
    assert data["title"] == "Write README"  # untouched
    assert data["description"] == "Initial draft"  # untouched


async def test_delete_task(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    project_id = await _create_project(client, headers)
    created = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Temporary"}, headers=headers
    )
    task_id = created.json()["id"]

    delete_response = await client.delete(
        f"/projects/{project_id}/tasks/{task_id}", headers=headers
    )
    assert delete_response.status_code == 204

    get_response = await client.get(f"/projects/{project_id}/tasks/{task_id}", headers=headers)
    assert get_response.status_code == 404


async def test_list_tasks_paginates(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    project_id = await _create_project(client, headers)
    for i in range(5):
        await client.post(
            f"/projects/{project_id}/tasks", json={"title": f"Task {i}"}, headers=headers
        )

    response = await client.get(
        f"/projects/{project_id}/tasks", params={"page": 1, "page_size": 2}, headers=headers
    )
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2

    second_page = await client.get(
        f"/projects/{project_id}/tasks", params={"page": 2, "page_size": 2}, headers=headers
    )
    assert len(second_page.json()["items"]) == 2

    third_page = await client.get(
        f"/projects/{project_id}/tasks", params={"page": 3, "page_size": 2}, headers=headers
    )
    assert len(third_page.json()["items"]) == 1


async def test_list_tasks_filters_by_status_and_assignee(client, register_and_login):
    headers = await register_and_login("alice@example.com")
    me_response = await client.get("/auth/me", headers=headers)
    my_id = me_response.json()["id"]
    project_id = await _create_project(client, headers)

    unassigned = await client.post(
        f"/projects/{project_id}/tasks", json={"title": "Unassigned"}, headers=headers
    )
    assigned = await client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Assigned to me", "assignee_id": my_id},
        headers=headers,
    )
    await client.patch(
        f"/projects/{project_id}/tasks/{assigned.json()['id']}",
        json={"status": "in_progress"},
        headers=headers,
    )

    by_assignee = await client.get(
        f"/projects/{project_id}/tasks", params={"assignee_id": my_id}, headers=headers
    )
    assert [task["id"] for task in by_assignee.json()["items"]] == [assigned.json()["id"]]

    by_status = await client.get(
        f"/projects/{project_id}/tasks", params={"status": "todo"}, headers=headers
    )
    assert [task["id"] for task in by_status.json()["items"]] == [unassigned.json()["id"]]
