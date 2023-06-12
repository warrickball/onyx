from django import forms


class ChoiceField(forms.ChoiceField):
    default_error_messages = {
        "invalid_choice": [
            "Select a valid choice. That choice is not one of the available choices."
        ]
    }

    def clean(self, value):
        return super().clean(value.lower())
