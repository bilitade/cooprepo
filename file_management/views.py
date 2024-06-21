from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import permission_required,login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.models import User
from django.conf import settings
from .forms import FolderCreationForm, FileUploadForm
from datetime import datetime
import os
import shutil
import mimetypes
import tempfile
import zipfile
import webbrowser
from .user_activity_logger import track_user_activity 
from django.http import JsonResponse


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email').lower()  # Convert email to lowercase
        password = request.POST.get('password')
        print(f"Email: {email}, Password: {password}")  # Debugging statement
        user = authenticate(request, email=email, password=password)  # Use lowercase email as the username
        if user is not None:
            login(request, user)
            track_user_activity(username=user.username, action=f'with email "{user.email}" logged into The System')  # Log user login
            return redirect('dashboard')  # Redirect to dashboard page after successful login
        else:
            error_message = 'Invalid email or password.'
            return render(request, 'file_management/login.html', {'error_message': error_message})
    return render(request, 'file_management/login.html')


def logout_view(request):
    # Capture the username and email before logging out
    
    username = request.user.username
    track_user_activity(username=username, action=f' logged out of the system')

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
def dashboard(request):
    path = request.GET.get('path', '')
    media_path = os.path.join(settings.MEDIA_ROOT, path.strip('/'))
    if not os.path.exists(media_path):
        media_path = settings.MEDIA_ROOT

    def format_size(size):
        # Convert size from bytes to kilobytes
        return f"{size / 1024:.2f} KB" if size != '-' else size

    def format_date(timestamp):
        # Convert timestamp to a readable date format
        return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y')

    items = []
    with os.scandir(media_path) as it:
        for entry in it:
            size = entry.stat().st_size if entry.is_file() else '-'
            modified = format_date(entry.stat().st_mtime)
            formatted_size = format_size(size)
            items.append({
                'name': entry.name,
                'type': 'Folder' if entry.is_dir() else 'File',
                'modified': modified,
                'size': formatted_size,
            })

    if request.method == 'POST':
        if 'create_folder' in request.POST:
            folder_form = FolderCreationForm(request.POST)
            if folder_form.is_valid():
                folder_name = folder_form.cleaned_data['folder_name']
                new_folder_path = os.path.join(media_path, folder_name)
                os.makedirs(new_folder_path, exist_ok=True)
                track_user_activity(username=request.user.username, action=f' Created  Folder:"{folder_name}" to path:- {new_folder_path}')
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
                track_user_activity(username=request.user.username, action=f' Uploaded File :"{uploaded_file.name}" to path:- {file_path }')
                return redirect(request.path + f'?path={path}')
            
        else:
            file_form = FileUploadForm()
    else:
        folder_form = FolderCreationForm()
        file_form = FileUploadForm()

    breadcrumbs = generate_breadcrumbs(path)
    user_groups = request.user.groups.values_list('name', flat=True) if request.user.is_authenticated else []
    
    context = {
    'items': items,
    'media_path': path,
    'breadcrumbs': breadcrumbs,
    'folder_form': folder_form,
    'file_form': file_form,
    'user': request.user,
    'can_upload_file': request.user.has_perm('auth.can_upload_file'),
    'can_create_folder': request.user.has_perm('auth.can_create_folder'),
    'can_delete': request.user.has_perm('auth.can_delete'),
    'can_ban_user': request.user.has_perm('auth.can_ban_user'),
    'can_approve_user': request.user.has_perm('auth.can_approve_user'),
    'can_delete_user': request.user.has_perm('auth.can_delete_user'),
    'can_view': request.user.has_perm('auth.can_view'),
    'can_download': request.user.has_perm('auth.can_download'),
    'can_create_user': request.user.has_perm('auth.can_create_user'),
    'user_group':user_groups
}


    print(context.items)

    return render(request, 'file_management/dashboard.html', context)

#delete folder
@login_required
@permission_required("auth.can_delete")
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
            track_user_activity(username=request.user.username, action=f' Delete Folder:"{folder_name}" and All files within  from path:- {full_folder_path}')

        # Redirect back to the dashboard or any other appropriate page
        return redirect('dashboard')


# Download Folder
@login_required
@permission_required("auth.can_download")
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
        track_user_activity(username=request.user.username, action=f'logged out of the system')
        return response
#delete file
@login_required
@permission_required('auth.can_delete')
    
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
            track_user_activity(username=request.user.username, action=f' Delete file :"{file_name}" from path:- {full_file_path}')

        # Redirect back to the dashboard or any other appropriate page
        return redirect('dashboard')
    
    
def view_file(request):
    if request.method == 'GET':
        # Extract file name from the request GET parameters
        file_name = request.GET.get('name')
        # Extract folder path from the request GET parameters
        folder_path = request.GET.get('path')
        # Construct the full file path using the folder path and file name
        full_file_path = os.path.join(settings.MEDIA_ROOT, folder_path.lstrip('/'), file_name)
        # Check if the file exists
        if os.path.exists(full_file_path):
            # Get the MIME type of the file
            mime_type, _ = mimetypes.guess_type(full_file_path)
            # Open the file with the default program
            if mime_type:
                webbrowser.open(full_file_path)
            else:
                # Serve the file for download
                with open(full_file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/force-download')
                    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            # File not found, return a 404 response
            return HttpResponse(status=404)

    # Placeholder response if the request method is not GET
    return HttpResponse('File View Initiated')

def download_file(request):
    if request.method == 'GET':
        # Extract file name from the request GET parameters
        file_name = request.GET.get('name')
        # Extract folder path from the request GET parameters
        folder_path = request.GET.get('path')
        # Construct the full file path using the folder path and file name
        full_file_path = os.path.join(settings.MEDIA_ROOT, folder_path.lstrip('/'), file_name)
        # Return the file as a downloadable attachment
        with open(full_file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/force-download')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name
            return response



def search_files(request):
    def format_size(size):
        return f"{size / 1024:.2f} KB" if size != '-' else size

    def format_date(timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y')

    query = request.GET.get('query', '').strip()
    media_path = settings.MEDIA_ROOT
    results = []

    if query:
        for root, dirs, files in os.walk(media_path):
            for name in dirs + files:
                if query.lower() in name.lower():
                    full_path = os.path.join(root, name)
                    relative_path = os.path.relpath(full_path, media_path)
                    is_file = os.path.isfile(full_path)
                    try:
                        size = os.path.getsize(full_path) if is_file else '-'
                        modified = format_date(os.path.getmtime(full_path))
                        formatted_size = format_size(size)
                        results.append({
                            'name': name,
                            'type': 'File' if is_file else 'Folder',
                            'modified': modified,
                            'size': formatted_size,
                            'relative_path': relative_path,
                        })
                    except OSError as e:
                        # Handle the error if the file does not exist or permission is denied
                        print(f"Error accessing file {full_path}: {e}")

    return render(request, 'file_management/search_list.html', {'items': results, 'query': query})

#download file  in search view

def download(request):
    path = request.GET.get('path', '')
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        raise Http404("File does not exist")
    
#load user to the interface 
def load_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
         
    }
    return render(request, 'file_management/users.html', context)
def load_user_activities(request):
    logs_dir = os.path.join(settings.BASE_DIR, 'logs/')
    logs = [f for f in os.listdir(logs_dir) if f.startswith('user_activity_') and f.endswith('.log')]
    context = {'logs': logs}
    
    return render(request, 'file_management/logs.html', context)

def get_log_content(request, log_name):
    logs_dir = os.path.join(settings.BASE_DIR, 'logs/')
    log_path = os.path.join(logs_dir, log_name)
    if os.path.exists(log_path) and log_name.startswith('user_activity_') and log_name.endswith('.log'):
        with open(log_path, 'r') as file:
            content = file.read()
        return JsonResponse({'content': content})
    else:
        raise Http404("Log file does not exist.")