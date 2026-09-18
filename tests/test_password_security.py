import pytest

from validators import assess_password_strength, validate_password_strength


@pytest.mark.parametrize("password", ["123456", "admin123", "password", "Abc123!", "aaaaaaa!!!!"])
def test_rejects_easy_or_predictable_passwords(password):
    report = assess_password_strength(password)

    assert report["score"] < 4
    with pytest.raises(ValueError, match="Contraseña"):
        validate_password_strength(password)


def test_accepts_special_characters_and_reports_strong_password():
    password = "Niebla!Cobre_47#Luna"

    report = validate_password_strength(password)

    assert report == {"score": 5, "max_score": 5, "level": "Muy fuerte", "feedback": []}


def test_never_includes_password_in_validation_feedback():
    password = "admin123"

    with pytest.raises(ValueError) as error:
        validate_password_strength(password)

    assert password not in str(error.value)