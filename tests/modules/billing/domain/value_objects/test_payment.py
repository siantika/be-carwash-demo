import pytest

from app.shared.domain.exceptions.exceptions import InvalidValueObject
from app.modules.billing.domain.value_objects.payment import Payment, PaymentMethodEnum


def test_payment_accepts_enum_method():
    payment = Payment(method=PaymentMethodEnum.CASH, metadata={})
    assert payment.method == PaymentMethodEnum.CASH


def test_payment_rejects_string_method():
    with pytest.raises(InvalidValueObject):
        Payment(method="CASH")


def test_validate_metadata_missing_required_key():
    with pytest.raises(InvalidValueObject):
        Payment(
            method=PaymentMethodEnum.QRIS,
            metadata={
                "provider": "GOPAY",  # rrn is missing
            },
        )


def test_validate_metadata_wrong_type():
    with pytest.raises(InvalidValueObject):
        Payment(
            method=PaymentMethodEnum.QRIS,
            metadata={
                "provider": "GOPAY",
                "reference_id": 123,  # it should be str
            },
        )


def test_cash_payment_should_not_have_metadata():
    with pytest.raises(InvalidValueObject):
        Payment(
            method=PaymentMethodEnum.CASH,
            metadata={"anything": "not allowed"},
        )


def test_validate_metadata():
    payment = Payment(
        method=PaymentMethodEnum.QRIS,
        metadata={
            "rrn": "123456789012",
            "provider": "GOPAY",
        },
    )

    assert payment.metadata["provider"] == "GOPAY"
