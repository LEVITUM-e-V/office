from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import socket


def index(request):
    if request.user.is_authenticated:
        return redirect(core)
    return redirect('oidc_authentication_init')


@login_required
def core(request):
    return render(request, 'core.html')


@login_required
def door_command(request):

    if request.method != 'POST':
        return HttpResponse(400)

    command = request.POST.get('command', '')

    if command not in ['home', 'open', 'close', 'status']:
        return JsonResponse({
            'status': 'error',
            'message': f'unknown command {command}'
            })

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((settings.DOOR_HOST, settings.DOOR_PORT))
        s.sendall(command.encode() + b"\n")
        s.settimeout(.5)

        messages = []
        try:
            message = bytes()
            while True:
                c = s.recv(1)
                if c == b'\n':
                    messages.append(message.decode())
                    message = bytes()
                    continue
                message += c
        except socket.timeout:
            pass

    return JsonResponse({
        'status': 'ok',
        'messages': messages
        })
