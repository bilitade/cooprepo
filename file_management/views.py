from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings
from django.http import JsonResponse
from .forms import FolderCreationForm, FileUploadForm
from django.http import HttpResponse
import os
import shutil

import tempfile
import zipfile
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()  # Convert email to lowercase
        password = request.POST.get('password')
        print(f"Email: {email}, Password: {password}")  # Debugging statement
        user = authenticate(request, email=email, password=password)  # Use lowercase email as the username
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard page after successful login
        else:
            error_message = 'Invalid email or password.'
            return render(request, 'file_management/login.html', {'error_message': error_message})
    return render(request, 'file_management/login.html')
def logout_view(request):
    logout(request)
    return redirect('login')



def generate_breadcrumbs(path):
    breadcrumbs = []
    path_parts = path.strip('/').split('/')
    for i in range(len(path_parts)):
        breadcrumb_path = '/' + '/'.join(path_parts[:i+1])
        breadcrumbs.append((path_parts[i], breadcrumb_path))
    return breadcrumbs


@login_required

# def dashboard(request):
#     media_path = request.GET.get('path', '')
#     full_path = os.path.join(settings.MEDIA_ROOT, media_path.lstrip('/'))
#     if not os.path.exists(full_path):
#         os.makedirs(full_path)

#     if request.method == 'POST':
#         if 'create_folder' in request.POST:
#             folder_form = FolderCreationForm(request.POST)
#             if folder_form.is_valid():
#                 folder_name = folder_form.cleaned_data['folder_name']
#                 os.makedirs(os.path.join(full_path, folder_name))
#         elif 'upload_file' in request.POST:
#             file_form = FileUploadForm(request.POST, request.FILES)
#             if file_form.is_valid():
#                 file = request.FILES['file']
#                 with open(os.path.join(full_path, file.name), 'wb+') as destination:
#                     for chunk in file.chunks():
#                         destination.write(chunk)

#     items = []
#     for item in os.listdir(full_path):
#         item_path = os.path.join(full_path, item)
#         items.append({
#             'name': item,
#             'type': 'Folder' if os.path.isdir(item_path) else 'File',
#             'modified': os.path.getmtime(item_path),
#             'size': os.path.getsize(item_path) if os.path.isfile(item_path) else '-'
#         })

#     return render(request, 'file_management/dashboard.html', {
#         'items': items,
#         'media_path': media_path,
#         'folder_form': FolderCreationForm(),
#         'file_form': FileUploadForm()
#     })

def dashboard(request):
    path = request.GET.get('path', '')
    media_path = os.path.join(settings.MEDIA_ROOT, path.strip('/'))
    if not os.path.exists(media_path):
        media_path = settings.MEDIA_ROOT

    items = []
    with os.scandir(media_path) as it:
        for entry in it:
            items.append({
                'name': entry.name,
                'type': 'Folder' if entry.is_dir() else 'File',
                'modified': entry.stat().st_mtime,
                'size': entry.stat().st_size if entry.is_file() else '-',
            })

    if request.method == 'POST':
        if 'create_folder' in request.POST:
            folder_form = FolderCreationForm(request.POST)
            if folder_form.is_valid():
                folder_name = folder_form.cleaned_data['folder_name']
                new_folder_path = os.path.join(media_path, folder_name)
                os.makedirs(new_folder_path, exist_ok=True)
                return redirect(request.path + f'?path={path}')
        else:
            folder_form = FolderCreationForm()

        if 'upload_file' in request.POST:
            file_form = FileUploadForm(request.POST, request.FILES)
            if file_form.is_valid():
                uploaded_file = file_form.cleaned_data['file']
                file_path = os.path.join(media_path, uploaded_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                return redirect(request.path + f'?path={path}')
        else:
            file_form = FileUploadForm()
    else:
        folder_form = FolderCreationForm()
        file_form = FileUploadForm()

    breadcrumbs = generate_breadcrumbs(path)
    context = {
        'items': items,
        'media_path': path,
        'breadcrumbs': breadcrumbs,
        'folder_form': folder_form,
        'file_form': file_form,
    }
    return render(request, 'file_management/dashboard.html', context)



def delete_folder(request):
    if request.method == 'GET':
        # Extract folder name from the request GET parameters
        folder_name = request.GET.get('name')
        # Extract folder path from the request GET parameters
        folder_path = request.GET.get('path')
        
        # Debugging print
        print("Folder name:", folder_name)
        print("Folder path:", folder_path)

        # Construct the full folder path using the base media root path and the folder path
        full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path.strip('/'), folder_name)
        # Check if the folder exists
        if os.path.exists(full_folder_path):
            # Delete the folder and all its contents recursively
            shutil.rmtree(full_folder_path)
        # Redirect back to the dashboard or any other appropriate page
        return redirect('dashboard')



# Download Folder
def download_folder(request):
    if request.method == 'GET':
        # Extract folder name from the request GET parameters
        folder_name = request.GET.get('name')
        # Extract folder path from the request GET parameters
        folder_path = request.GET.get('path')
        # Construct the full folder path using the base media root path and the folder name
        full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path.strip('/'), folder_name)

        print("Full folder path:", full_folder_path)

        # Create a temporary directory to store the zip file
        temp_dir = tempfile.mkdtemp()
        # Create a temporary zip file
        zip_file_path = os.path.join(temp_dir, f"{folder_name}.zip")

        # Create a zip file and add the contents of the folder and its subfolders to it
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_folder_path):
                print("Root:", root)
                print("Dirs:", dirs)
                print("Files:", files)
                # Add all files in the current directory
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, full_folder_path)
                    zipf.write(file_path, rel_path)
                # Add all subdirectories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    rel_path = os.path.relpath(dir_path, full_folder_path)
                    zipf.write(dir_path, rel_path)

        # Read the zip file as binary data
        with open(zip_file_path, 'rb') as f:
            zip_data = f.read()

        # Delete the temporary directory and zip file
        shutil.rmtree(temp_dir)

        # Prepare the response with the zip file as an attachment
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{folder_name}.zip"'
        return response
    

    
def delete_file(request):
    if request.method == 'GET':
        # Extract file name from the request GET parameters
        file_name = request.GET.get('name')
        # Extract folder path from the request GET parameters
        folder_path = request.GET.get('path')
        # Debugging statements
        print("File name:", file_name)
        print("Folder path:", folder_path)
        # Construct the full file path using the folder path and file name
        full_file_path = os.path.join(settings.MEDIA_ROOT, folder_path.lstrip('/'), file_name)
        # Debugging statement
        print("Full file path:", full_file_path)
        # Check if the file exists
        if os.path.exists(full_file_path):
            # Delete the file
            os.remove(full_file_path)
        # Redirect back to the dashboard or any other appropriate page
        return redirect('dashboard')

def view_file(request):
    pass

# Download File
def download_file(request):
   pass

# Open File
def open_file(request):
    pass