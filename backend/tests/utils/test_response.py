"""Tests for response utility functions."""

import pytest

from app.utils.response import create_error_response, create_success_response


class TestCreateSuccessResponse:
    """Tests for create_success_response function."""

    def test_basic_success_response(self):
        """Test creating a basic success response with data only."""
        data = {"id": 1, "name": "Test"}
        response = create_success_response(data)

        assert response.status_code == 200
        # Decode the response body
        import json

        body = json.loads(response.body)
        assert body["success"] is True
        assert body["data"] == data
        assert "message" not in body

    def test_success_response_with_message(self):
        """Test success response with optional message."""
        data = {"id": 1}
        message = "Operation completed successfully"
        response = create_success_response(data, message=message)

        import json

        body = json.loads(response.body)
        assert body["success"] is True
        assert body["data"] == data
        assert body["message"] == message

    def test_success_response_custom_status_code(self):
        """Test success response with custom status code (201 Created)."""
        data = {"id": 1}
        response = create_success_response(data, status_code=201)

        assert response.status_code == 201

    def test_success_response_with_none_data(self):
        """Test success response with None as data."""
        response = create_success_response(None)

        import json

        body = json.loads(response.body)
        assert body["success"] is True
        assert body["data"] is None

    def test_success_response_with_list_data(self):
        """Test success response with list data."""
        data = [{"id": 1}, {"id": 2}]
        response = create_success_response(data)

        import json

        body = json.loads(response.body)
        assert body["data"] == data


class TestCreateErrorResponse:
    """Tests for create_error_response function."""

    def test_basic_error_response(self):
        """Test creating a basic error response."""
        error = "Something went wrong"
        response = create_error_response(error)

        assert response.status_code == 400
        import json

        body = json.loads(response.body)
        assert body["success"] is False
        assert body["error"] == error
        assert "details" not in body

    def test_error_response_with_details(self):
        """Test error response with optional details."""
        error = "Validation failed"
        details = "Field 'name' is required"
        response = create_error_response(error, details=details)

        import json

        body = json.loads(response.body)
        assert body["success"] is False
        assert body["error"] == error
        assert body["details"] == details

    def test_error_response_custom_status_code(self):
        """Test error response with custom status code (404)."""
        response = create_error_response("Not found", status_code=404)
        assert response.status_code == 404

    def test_error_response_500_status(self):
        """Test error response with 500 status code."""
        response = create_error_response("Internal server error", status_code=500)
        assert response.status_code == 500

    def test_error_response_without_details(self):
        """Test that details field is excluded when None."""
        response = create_error_response("Error", details=None)

        import json

        body = json.loads(response.body)
        assert "details" not in body
