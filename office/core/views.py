import logging
from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)


def index(request):
    if request.user.is_authenticated:
        return render(request, 'index.html')
    return redirect('oidc_authentication_init')
