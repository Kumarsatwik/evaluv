import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.schemas.job import JobCreateRequest, JobUpdateRequest, JobResponse
from unittest.mock import AsyncMock
from uuid import uuid4


class TestJobRoutes:
    """Test cases for job routes"""

    def test_create_job_success(self, client_jobs, mock_job_controller):
        """Test successful job creation"""
        job_data = JobCreateRequest(
            title="Senior Software Engineer",
            description="Looking for an experienced software engineer",
            skills="Python, JavaScript, React",
            experience="3+ years",
            location="New York, NY",
            salary_range="$100k-$150k",
            job_type="full-time",
            status="active"
        )

        job_id = str(uuid4())
        expected_response = JobResponse(
            id=job_id,
            title="Senior Software Engineer",
            description="Looking for an experienced software engineer",
            skills="Python, JavaScript, React",
            experience="3+ years",
            location="New York, NY",
            salary_range="$100k-$150k",
            job_type="full-time",
            status="active",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            created_by=str(uuid4())
        )

        mock_job_controller.create_job.return_value = expected_response

        user_id = str(uuid4())
        response = client_jobs.post("/jobs/", json=job_data.model_dump(), headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Senior Software Engineer"
        assert data["skills"] == "Python, JavaScript, React"
        mock_job_controller.create_job.assert_called_once()
        call_args = mock_job_controller.create_job.call_args
        assert call_args[0][0] == job_data
        # The second argument is the request object

    def test_create_job_unauthenticated(self, client_jobs, mock_job_controller):
        """Test job creation when not authenticated"""
        job_data = JobCreateRequest(
            title="Test Job",
            description="Test description",
            skills="Python",
            experience="1 year"
        )

        mock_job_controller.create_job.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client_jobs.post("/jobs/", json=job_data.model_dump())

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_create_job_validation_error(self, client_jobs, mock_job_controller):
        """Test job creation with invalid data"""
        # Missing required title
        invalid_job_data = {
            "description": "Test description",
            "skills": "Python",
            "experience": "1 year"
        }

        user_id = str(uuid4())
        response = client_jobs.post("/jobs/", json=invalid_job_data, headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 422  # Validation error
        assert "title" in str(response.json())

    def test_get_job_by_id_success(self, client_jobs, mock_job_controller):
        """Test get job by ID success"""
        job_id = str(uuid4())
        expected_response = JobResponse(
            id=job_id,
            title="Test Job",
            description="Test description",
            skills="Python",
            experience="2 years",
            location=None,
            salary_range=None,
            job_type="full-time",
            status="active",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            created_by=str(uuid4())
        )

        mock_job_controller.get_job_by_id.return_value = expected_response

        response = client_jobs.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["title"] == "Test Job"

    def test_get_job_by_id_not_found(self, client_jobs, mock_job_controller):
        """Test get job by ID when job doesn't exist"""
        from app.utils.exceptions import NotFoundException

        job_id = str(uuid4())
        mock_job_controller.get_job_by_id.side_effect = NotFoundException("Job not found")

        response = client_jobs.get(f"/jobs/{job_id}")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_get_my_jobs_success(self, client_jobs, mock_job_controller):
        """Test get current user's jobs"""
        user_id = str(uuid4())
        jobs = [
            JobResponse(
                id=str(uuid4()),
                title="Job 1",
                description="Description 1",
                skills="Python",
                experience="2 years",
                location=None,
                salary_range="$50k",
                job_type="full-time",
                status="active",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                created_by=user_id
            ),
            JobResponse(
                id=str(uuid4()),
                title="Job 2",
                description="Description 2",
                skills="JavaScript",
                experience="3 years",
                location="Remote",
                salary_range="$60k",
                job_type="contract",
                status="active",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                created_by=user_id
            )
        ]

        mock_job_controller.get_my_jobs.return_value = jobs

        response = client_jobs.get("/jobs/my/", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(job["created_by"] == user_id for job in data)

    def test_get_my_jobs_unauthenticated(self, client_jobs, mock_job_controller):
        """Test get my jobs when not authenticated"""
        mock_job_controller.get_my_jobs.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client_jobs.get("/jobs/my/")

        assert response.status_code == 401

    def test_get_all_jobs_success(self, client_jobs, mock_job_controller):
        """Test get all jobs"""
        jobs = [
            JobResponse(
                id=str(uuid4()),
                title="Job 1",
                description="Description 1",
                skills="Python",
                experience="2 years",
                location=None,
                salary_range="$50k",
                job_type="full-time",
                status="active",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                created_by=str(uuid4())
            ),
            JobResponse(
                id=str(uuid4()),
                title="Job 2",
                description="Description 2",
                skills="Java",
                experience="1 year",
                location="New York",
                salary_range=None,
                job_type="part-time",
                status="closed",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00",
                created_by=str(uuid4())
            )
        ]

        mock_job_controller.get_all_jobs.return_value = jobs

        response = client_jobs.get("/jobs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Job 1"
        assert data[1]["status"] == "closed"

    def test_update_job_success(self, client_jobs, mock_job_controller):
        """Test successful job update"""
        job_id = str(uuid4())
        user_id = str(uuid4())
        update_data = JobUpdateRequest(
            title="Updated Job Title",
            status="closed"
        )

        expected_response = JobResponse(
            id=job_id,
            title="Updated Job Title",
            description="Original description",
            skills="Python",
            experience="2 years",
            location=None,
            salary_range="$50k",
            job_type="full-time",
            status="closed",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:01:00",
            created_by=user_id
        )

        mock_job_controller.update_job.return_value = expected_response

        response = client_jobs.put(f"/jobs/{job_id}", json=update_data.model_dump(), headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Job Title"
        assert data["status"] == "closed"

    def test_update_job_unauthenticated(self, client_jobs, mock_job_controller):
        """Test update job when not authenticated"""
        job_id = str(uuid4())
        update_data = JobUpdateRequest(title="Updated Title")

        mock_job_controller.update_job.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client_jobs.put(f"/jobs/{job_id}", json=update_data.model_dump())

        assert response.status_code == 401

    def test_update_job_not_owner(self, client_jobs, mock_job_controller):
        """Test update job by user who doesn't own it"""
        from app.utils.exceptions import NotFoundException

        job_id = str(uuid4())
        update_data = JobUpdateRequest(title="Updated Title")
        user_id = str(uuid4())  # Different user

        mock_job_controller.update_job.side_effect = NotFoundException("Job not found or access denied")

        response = client_jobs.put(f"/jobs/{job_id}", json=update_data.model_dump(), headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 404
        assert "access denied" in response.json()["detail"]

    def test_delete_job_success(self, client_jobs, mock_job_controller):
        """Test successful job deletion"""
        job_id = str(uuid4())
        user_id = str(uuid4())

        mock_job_controller.delete_job.return_value = {"message": "Job deleted successfully"}

        response = client_jobs.delete(f"/jobs/{job_id}", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_delete_job_unauthenticated(self, client_jobs, mock_job_controller):
        """Test delete job when not authenticated"""
        job_id = str(uuid4())

        mock_job_controller.delete_job.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client_jobs.delete(f"/jobs/{job_id}")

        assert response.status_code == 401

    def test_delete_job_not_owner(self, client_jobs, mock_job_controller):
        """Test delete job by user who doesn't own it"""
        from app.utils.exceptions import NotFoundException

        job_id = str(uuid4())
        user_id = str(uuid4())

        mock_job_controller.delete_job.side_effect = NotFoundException("Job not found or access denied")

        response = client_jobs.delete(f"/jobs/{job_id}", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 404

    def test_create_job_with_minimal_data(self, client_jobs, mock_job_controller):
        """Test job creation with only required fields"""
        job_data = JobCreateRequest(
            title="Minimal Job",
            description="Minimal description",
            skills="Basic skills",
            experience="Entry level"
        )

        job_id = str(uuid4())
        expected_response = JobResponse(
            id=job_id,
            title="Minimal Job",
            description="Minimal description",
            skills="Basic skills",
            experience="Entry level",
            location=None,
            salary_range=None,
            job_type="full-time",  # Default value
            status="active",  # Default value
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            created_by=str(uuid4())
        )

        mock_job_controller.create_job.return_value = expected_response

        user_id = str(uuid4())
        response = client_jobs.post("/jobs/", json=job_data.model_dump(), headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "full-time"
        assert data["status"] == "active"
