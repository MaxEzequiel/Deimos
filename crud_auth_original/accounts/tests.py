from django.test import TestCase

# Create your tests here.
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .password_validators import UppercaseAndSpecialCharacterValidator


class PasswordPolicyTests(SimpleTestCase):
    def setUp(self):
        self.validator = UppercaseAndSpecialCharacterValidator()

    def test_rejects_password_without_uppercase_or_special_character(self):
        with self.assertRaises(ValidationError):
            self.validator.validate("password1")

    def test_accepts_password_with_required_complexity(self):
        self.validator.validate("Segura!2026")
