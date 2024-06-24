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


@login_required
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
  
    
    context = {
    'items': items,
    'media_path': path,
    'breadcrumbs': breadcrumbs,
    'folder_form': folder_form,
    'file_form': file_form,
    'user': request.user
    
   
}


    print(context.items)

    return render(request, 'file_management/dashboard.html', context)


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

#delete folder
@login_required
@permission_required("auth.can_trash")
def delete_folder(request):
    if request.method == 'GET':
        folder_name = request.GET.get('name')
        folder_path = request.GET.get('path')
        full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path.strip('/'), folder_name)
        trash_folder_path = os.path.join(settings.TRASH_DIR, folder_path.strip('/'), folder_name)

        if os.path.exists(full_folder_path):
            os.makedirs(os.path.dirname(trash_folder_path), exist_ok=True)
            shutil.move(full_folder_path, trash_folder_path)
            track_user_activity(username=request.user.username, action=f'Trashed Folder: "{folder_name}" to trash from path: {full_folder_path}')
        
        return redirect('dashboard')
       
#delete file
@login_required
@permission_required('auth.can_trash')
def delete_file(request):
    if request.method == 'GET':
        file_name = request.GET.get('name')
        folder_path = request.GET.get('path')
        full_file_path = os.path.join(settings.MEDIA_ROOT, folder_path.lstrip('/'), file_name)
        trash_file_path = os.path.join(settings.TRASH_DIR,file_name)

        if os.path.exists(full_file_path):
            os.makedirs(os.path.dirname(trash_file_path), exist_ok=True)
            shutil.move(full_file_path, trash_file_path)
            track_user_activity(username=request.user.username, action=f'Trashed File: "{file_name}" from path: {folder_path}')
        
        return redirect('dashboard')
    
@login_required    
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

@login_required
@permission_required("auth.can_download")
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


@login_required
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
@login_required
@permission_required("auth.can_download")
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
    
@login_required
@permission_required("auth.can_view_user")
@login_required
def load_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
         
    }
    return render(request, 'file_management/users.html', context)

@login_required
@permission_required("auth.can_view_logs")
def load_user_activities(request):
    logs_dir = os.path.join(settings.BASE_DIR, 'logs/')
    logs = [f for f in os.listdir(logs_dir) if f.startswith('user_activity_') and f.endswith('.log')]
    
    # Sort logs based on modification time (most recent first)
    logs.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
    
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
    

@login_required
@permission_required("auth.can_view_trash")
# Trash list view
def trash_list(request):
    def get_file_size(path):
        size = os.path.getsize(path)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024

    def get_trash_date(path):
        metadata_path = path + '.meta'
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as meta_file:
                return meta_file.read().strip()
        return 'Unknown'

    trash_folder = settings.TRASH_DIR
    items = []

    for item_name in os.listdir(trash_folder):
        item_path = os.path.join(trash_folder, item_name)
        if os.path.isdir(item_path):
            item_type = 'Folder'
        else:
            item_type = 'File'

        item_info = {
            'name': item_name,
            'type': item_type,
            'modified': get_trash_date(item_path),
            'size': get_file_size(item_path) if item_type == 'File' else '',
            'relative_path': item_name
        }
        items.append(item_info)

    context = {
        'items': items,
        'breadcrumbs': [],
        'can_delete': True,  # Update this based on your permission logic
    }
    return render(request, 'file_management/trash.html', context)

@login_required
@permission_required("auth.can_delete")
def permanently_delete_item(request):
    item_name = request.GET.get('name')
    item_path = os.path.join(settings.TRASH_DIR, item_name)

    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
        track_user_activity(username=request.user.username, action=f'Permanently Deleted Folder :- "{item_name}" from path: {item_path}')
    else:
        os.remove(item_path)
        track_user_activity(username=request.user.username, action=f'Permanently Deleted File :- "{item_name}" from path: {item_path}')

    metadata_path = item_path + '.meta'
    if os.path.exists(metadata_path):
        os.remove(metadata_path)

        

    return redirect('trash_list')
@login_required
@permission_required("auth.can_restore")
def restore_item(request):
    item_name = request.GET.get('name')
    item_path = os.path.join(settings.TRASH_DIR, item_name)
    target_path = os.path.join(settings.MEDIA_ROOT, item_name)

    if os.path.exists(target_path):
        # Handle case where item with the same name already exists
        # You may want to implement a different logic here, e.g., renaming the item
        pass
    else:
        os.rename(item_path, target_path)
        metadata_path = item_path + '.meta'
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        track_user_activity(username=request.user.username, action=f'Restored Folde/File :- "{item_name}" to path: {target_path}')
    return redirect('trash_list')

@login_required
@permission_required("auth.can_download")
def download_trashed_folder(request):
    if request.method == 'GET':
        # Extract folder name from the request GET parameters
        folder_name = request.GET.get('name')
        # Construct the full folder path using the trash directory
        full_folder_path = os.path.join(settings.TRASH_DIR, folder_name)

        # Create a temporary directory to store the zip file
        temp_dir = tempfile.mkdtemp()
        # Create a temporary zip file
        zip_file_path = os.path.join(temp_dir, f"{folder_name}.zip")

        # Create a zip file and add the contents of the trashed folder and its subfolders to it
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_folder_path):
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
    
@login_required
@permission_required("auth.can_download")
def download_trashed_file(request):
    if request.method == 'GET':
        # Extract file name from the request GET parameters
        file_name = request.GET.get('name')
        # Construct the full file path using the trash directory
        full_file_path = os.path.join(settings.TRASH_DIR, file_name)

        # Check if the file exists
        if os.path.exists(full_file_path):
            # Open the file as binary data
            with open(full_file_path, 'rb') as file:
                # Prepare the response with the file content as an attachment
                response = HttpResponse(file.read(), content_type='application/force-download')
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            # File not found, return a 404 response or handle accordingly
            return HttpResponse(status=404)