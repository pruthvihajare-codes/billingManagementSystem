def user_full_name(request):
    if request.user.is_authenticated:
        full_name = getattr(request.user, 'full_name', 'User')
    else:
        full_name = 'Guest'
    return {'full_name': full_name}
