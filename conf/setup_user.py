def setup_project_user(user):
    """
    All users used the Django admin, so we need to set the "staff" user flag.
    Called from django_ynh.sso_auth
    """
    user.is_staff = True
    user.save()
    return user
