import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mpd import MPDClient
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


@login_required
def index(request):
    context = {
         'playlistinfo': [],
        }
    try:
        mpc = MPDClient()
        mpc.timeout = 3
        mpc.connect(settings.MPD_HOST, settings.MPD_PORT)
        if request.method == 'POST':
            song_id = int(request.POST.get('song_id', '0'))
            if song_id == 0:
                mpc.stop()
            else:
                mpc.playid(song_id)
        context['playlistinfo'] = mpc.playlistinfo()
        context['status'] = mpc.status()
        context['currentsong'] = mpc.currentsong()
    except ConnectionError:
        messages.error(request, "could not connect to Music Player Daemon")
        logger.exception("could not connect to mpd")
    except TimeoutError:
        messages.error(request, "timed out connecting to Music Player Daemon")
        logger.exception("timeout mpd")

    if request.method == 'POST':
        return JsonResponse(context)
    return render(request, 'radio.html', context)
