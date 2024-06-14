


def user_info(request):
    user = request.user
    return {
        'current_user': user,
        
    }