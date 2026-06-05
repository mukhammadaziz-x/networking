from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User, UserRole
from app.models.activity import Activity
from app.models.company import Company


def get_auth_client(email: str = "admin@clothcrm.local", password: str = "Admin123!"):
    """Helper to return an authenticated TestClient instance"""
    client = TestClient(app)
    client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True
    )
    return client


def test_task_crud_and_activity_logging():
    """Verify that an admin can create, read, edit, delete tasks and activities are logged"""
    client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Create a temporary company
        company = Company(name="Task Test Corp", status="active", owner_id=1)
        db.add(company)
        db.commit()
        db.refresh(company)
        
        # 1. Create task
        task_data = {
            "title": "Clean Warehouse",
            "description": "Sweep and organize racks",
            "due_date": (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "priority": "high",
            "status": "open",
            "assignee_id": 1,
            "related_company_id": company.id
        }
        create_response = client.post("/tasks/create", data=task_data, follow_redirects=False)
        assert create_response.status_code == 303
        
        # Verify DB created
        task = db.query(Task).filter(Task.title == "Clean Warehouse").first()
        assert task is not None
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.OPEN
        assert task.related_company_id == company.id
        
        # Verify Activity Logged
        activity = db.query(Activity).filter(
            Activity.entity_type == "Task",
            Activity.entity_id == task.id,
            Activity.action == "create"
        ).first()
        assert activity is not None
        assert "Clean Warehouse" in activity.description
        
        # 2. Edit task
        edit_data = {
            "title": "Clean Warehouse and Dock",
            "description": "Clean racks and load docks",
            "due_date": (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "priority": "medium",
            "status": "in_progress",
            "assignee_id": 1,
            "related_company_id": company.id
        }
        edit_response = client.post(f"/tasks/{task.id}/edit", data=edit_data, follow_redirects=False)
        assert edit_response.status_code == 303
        
        # Verify DB updated
        db.refresh(task)
        assert task.title == "Clean Warehouse and Dock"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.IN_PROGRESS
        
        # 3. List tasks
        list_response = client.get("/tasks")
        assert list_response.status_code == 200
        assert "Clean Warehouse and Dock" in list_response.text
        
        # 4. Delete task
        delete_response = client.post(f"/tasks/{task.id}/delete", follow_redirects=False)
        assert delete_response.status_code == 303
        
        # Verify deleted
        task_deleted = db.query(Task).filter(Task.id == task.id).first()
        assert task_deleted is None
        
        # Clean up
        db.delete(company)
        db.commit()
        
    finally:
        db.close()


def test_quick_mark_done_patch_api():
    """Verify that PATCHing a task status updates the DB and log and works correctly"""
    client = get_auth_client()
    db = SessionLocal()
    
    try:
        # Create a task
        task = Task(
            title="Temp API Task",
            status=TaskStatus.OPEN,
            priority=TaskPriority.LOW,
            assignee_id=1
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Patch to done
        patch_response = client.patch(
            f"/api/tasks/{task.id}/status",
            json={"status": "done"}
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["status"] == "done"
        
        # Verify DB updated
        db.refresh(task)
        assert task.status == TaskStatus.DONE
        
        # Verify Activity Logged
        activity = db.query(Activity).filter(
            Activity.entity_type == "Task",
            Activity.entity_id == task.id,
            Activity.action == "update"
        ).order_by(Activity.created_at.desc()).first()
        assert activity is not None
        assert "status: open -> done" in activity.description.lower()
        
        # Clean up
        db.delete(task)
        db.commit()
        
    finally:
        db.close()


def test_tasks_role_permissions_visibility():
    """Verify that Sales Reps cannot view 'All Tasks' scope and filters behave accordingly"""
    sales_client = get_auth_client("sales@clothcrm.local", "Sales123!")
    manager_client = get_auth_client("manager@clothcrm.local", "Manager123!")
    
    # 1. Sales rep tries to get All Tasks -> should be forced/re-routed to My Tasks context
    sales_resp = sales_client.get("/tasks?view=all")
    assert sales_resp.status_code == 200
    # Sales should not have the toggle button in HTML for My Tasks vs All Tasks
    assert "Task Scope Toggle" not in sales_resp.text
    
    # 2. Manager gets tasks -> has scope toggle
    mgr_resp = manager_client.get("/tasks?view=all")
    assert mgr_resp.status_code == 200
    assert "Task Scope Toggle" in mgr_resp.text


def test_global_activity_feed_page():
    """Verify that Activity log feed page displays log entries and filters successfully"""
    client = get_auth_client()
    
    # 1. Access page
    response = client.get("/activities")
    assert response.status_code == 200
    assert "CRM Audit Logs & Event Timeline" in response.text
    
    # 2. Filter by entity type
    filter_response = client.get("/activities?entity_filter=Company")
    assert filter_response.status_code == 200
    
    # 3. Filter by user
    filter_user_response = client.get("/activities?user_filter=1")
    assert filter_user_response.status_code == 200
