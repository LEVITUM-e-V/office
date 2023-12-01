from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from paho.mqtt.publish import single
from django.conf import settings


def index(request):
    if request.user.is_authenticated:
        return redirect(core)
    return redirect('login')


@login_required
def core(request):
    return render(request, 'core.html')


@login_required
def door_command(request):

    if request.method != 'POST':
        return HttpResponse(400)

    command = request.POST.get('command', '')

    if command not in ['home', 'open', 'close']:
        return JsonResponse({
            'status': 'error',
            'message': f'unknown command {command}'
            })

    single(
            'door/command',
            command,
            hostname=settings.MQTT_SERVER,
            port=settings.MQTT_PORT,
            auth={
                'username': settings.MQTT_USER,
                'password': settings.MQTT_PASSWORD
                }
            )

    return JsonResponse({
        'status': 'ok'
        })
