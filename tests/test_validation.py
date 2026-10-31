import pytest
from pydantic import ValidationError

from validation import RequestResult


def test_payment_alias_is_normalized():
    result = RequestResult.model_validate({
        "action": "list_failed_builds",
        "service": "payment",
    })

    assert result.service == "payment-service"


def test_supported_user_service_is_accepted():
    result = RequestResult.model_validate({
        "action": "list_failed_builds",
        "service": "user-service",
    })

    assert result.service == "user-service"


def test_unknown_action_value_is_accepted():
    result = RequestResult.model_validate({
        "action": "unknown",
        "service": None,
    })

    assert result.action == "unknown"


def test_unsupported_action_is_rejected():
    with pytest.raises(ValidationError):
        RequestResult.model_validate({
            "action": "delete_all_builds",
            "service": "payment-service",
        })


def test_unsupported_service_is_rejected():
    with pytest.raises(ValidationError):
        RequestResult.model_validate({
            "action": "list_failed_builds",
            "service": "admin-service",
        })
