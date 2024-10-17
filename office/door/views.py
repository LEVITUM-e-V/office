import logging
import socket
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from .models import DoorLog

logger = logging.getLogger(__name__)


@login_required
def index(request):

    context = {
            'output': [],
            'logs': DoorLog.objects.order_by("-time")[:20]
            }

    def format_log_line(log):
        formatted_time = timezone.localtime(log.time).strftime('%d-%m-%Y %H:%M')
        return f"{formatted_time}: {log.user.first_name} {log.user.last_name} -> {log.command} = {log.response}"

    if request.method == 'POST':

        def finish_post():
            context['logs'] = list(map(format_log_line, context['logs']))
            return JsonResponse(context)
        command = request.POST.get('command', '')

        if command not in ['home', 'open', 'close', 'status', 'reboot']:
            context['status'] = 'unknown command %s' % command
            return finish_post()

        door_log = DoorLog(user=request.user, command=command)
        door_log.save()
        context.update({'logs': DoorLog.objects.order_by("-time")[:20]})

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            try:
                s.connect((settings.DOOR_HOST, settings.DOOR_PORT))
            except (socket.timeout, ConnectionError):
                logger.exception("door connect timeout")
                context['status'] = 'could not connect to door'
                return finish_post()
            s.sendall(command.encode() + b"\n")
            s.settimeout(3)

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

        return finish_post()

    context['logs'] = list(map(format_log_line, context['logs']))
    return render(request, 'door.html', context)
