from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    if request.user.is_authenticated:
        return redirect(core)
    return redirect('login')


@login_required
def core(request):
    return render(request, 'core.html')
