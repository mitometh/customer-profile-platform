"""Unit tests for custom exception types."""

from uuid import uuid4

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    LLMUnavailableError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)


class TestAppError:
    def test_base_error_attributes(self):
        err = AppError(code="TEST", message="test msg", status_code=418, details={"k": "v"})
        assert err.code == "TEST"
        assert err.message == "test msg"
        assert err.status_code == 418
        assert err.details == {"k": "v"}

    def test_default_details_empty_dict(self):
        err = AppError(code="TEST", message="msg")
        assert err.details == {}


class TestNotFoundError:
    def test_not_found_404(self):
        uid = uuid4()
        err = NotFoundError("Customer", uid)
        assert err.status_code == 404
        assert err.code == "NOT_FOUND"
        assert str(uid) in err.message


class TestValidationError:
    def test_validation_400(self):
        err = ValidationError("Invalid input")
        assert err.status_code == 400
        assert err.code == "VALIDATION_ERROR"


class TestUnauthorizedError:
    def test_unauthorized_401(self):
        err = UnauthorizedError()
        assert err.status_code == 401
        assert err.code == "UNAUTHORIZED"

    def test_custom_message(self):
        err = UnauthorizedError("Bad token")
        assert err.message == "Bad token"


class TestForbiddenError:
    def test_forbidden_403(self):
        err = ForbiddenError("customers.read")
        assert err.status_code == 403
        assert "customers.read" in err.message


class TestConflictError:
    def test_conflict_409(self):
        err = ConflictError("Duplicate email")
        assert err.status_code == 409


class TestRateLimitedError:
    def test_rate_limited_429(self):
        err = RateLimitedError()
        assert err.status_code == 429


class TestLLMUnavailableError:
    def test_llm_unavailable_503(self):
        err = LLMUnavailableError()
        assert err.status_code == 503
