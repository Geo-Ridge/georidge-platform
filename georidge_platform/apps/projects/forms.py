from django import forms
from .models import Project
from .validators import validate_qgz_or_zip


class ProjectUploadForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "file"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "file": forms.FileInput(attrs={"class": "form-control", "accept": ".qgz,.zip"}),
        }

    def clean_file(self):
        file = self.cleaned_data["file"]
        validate_qgz_or_zip(file)
        return file
