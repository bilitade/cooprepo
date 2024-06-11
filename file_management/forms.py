from django import forms

class FolderCreationForm(forms.Form):
    folder_name = forms.CharField(max_length=100)

class FileUploadForm(forms.Form):
    file = forms.FileField()