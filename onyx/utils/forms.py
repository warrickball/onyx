from django import forms


class ChoiceField(forms.ChoiceField):
    def clean(self, value):
        return super().clean(value.lower())
