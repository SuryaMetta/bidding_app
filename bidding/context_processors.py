from django.contrib.auth.decorators import login_required

def wallet_context(request):
    if request.user.is_authenticated:
        wallet = getattr(request.user, 'wallet', None)  # Get user's wallet
        return {'wallet': wallet}
    return {'wallet': None}
