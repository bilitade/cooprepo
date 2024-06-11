from django import forms

class FolderCreationForm(forms.Form):
    folder_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))