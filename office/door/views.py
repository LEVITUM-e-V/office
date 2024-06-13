import logging
import socket
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from .models import DoorLog

logger = logging.getLogger(__name__)


@login_required
def index(request):

    context = {
            'output': [],
            'logs': DoorLog.objects.order_by("-time")[:20]
            }

    if request.method == 'POST':
        command = request.POST.get('command', '')

        if command not in ['home', 'open', 'close', 'status', 'reboot']:
            messages.error(request, "unknown command %s" % command)
            return render(request, 'door.html', context)

        door_log = DoorLog(user=request.user, command=command)
        door_log.save()
        context.update({'logs': DoorLog.objects.order_by("-time")[:20]})

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            try:
                s.connect((settings.DOOR_HOST, settings.DOOR_PORT))
            except (socket.timeout, ConnectionError):
                logger.exception("door connect timeout")
                messages.error(request, "could not connect to door")
                return render(request, 'door.html', context)
            s.sendall(command.encode() + b"\n")
            s.settimeout(.5)

            try:
                message = bytes()
                while True:
                    c = s.recv(1)
                    if c == b'\n':
                        context['output'].append(message.decode())
                        message = bytes()
                        continue
                    message += c
            except socket.timeout:
                pass

        door_log.response = ','.join(context['output'])
        door_log.save()

    return render(request, 'door.html', context)
