


def user_info(request):
    user = request.user
    return {
        'current_user': user,
        'can_approve_user': request.user.has_perm('auth.can_approve_user'),
        
    }