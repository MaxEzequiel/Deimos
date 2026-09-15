from django.core.exceptions import ValidationError


class UppercaseAndSpecialCharacterValidator:
    """Exige una mayúscula y un carácter no alfanumérico."""

    def validate(self, password, user=None):
        if not any(character.isupper() for character in password):
            raise ValidationError(
                "La contraseña debe contener al menos una letra mayúscula.",
                code="password_no_uppercase",
            )
        if not any(not character.isalnum() for character in password):
            raise ValidationError(
                "La contraseña debe contener al menos un carácter especial.",
                code="password_no_special",
            )

    def get_help_text(self):
        return "La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial."
