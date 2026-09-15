from django.core.exceptions import ValidationError


class UppercaseAndSpecialCharacterValidator:
    def validate(self, password, user=None):
        has_uppercase = False
        has_special_character = False
        for character in password:
            if character.isupper():
                has_uppercase = True
            if not character.isalpha():
                has_special_character = True

        errors = []
        if not has_uppercase:
            errors.append("la contraseña debe tener al menos una letra mayuscula")
        if not has_special_character:
            errors.append("la contraseña debe tener al menos un caracter especial o un numero")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "la contraseña debe tener al menos una letra mayuscula y un caracter especial o un numero"
