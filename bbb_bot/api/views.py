import json
import os
import signal
import subprocess

import rc_protocol
from django.core.handlers.wsgi import WSGIRequest
from django.views import View
from django.http import JsonResponse

from api.models import Bot
from bbb_bot import settings


class RCPSafeView(View):
    def post(self, request: WSGIRequest, *args, **kwargs):
        try:
            decoded = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Json could not be decoded"}, status=400)
        if "checksum" not in decoded:
            return JsonResponse({"success": False, "message": "No checksum given"}, status=401)
        checksum = decoded["checksum"]
        del decoded["checksum"]
        if not rc_protocol.validate_checksum(
            request=decoded,
            checksum=checksum,
            shared_secret=settings.SHARED_SECRET,
            salt=request.get_full_path().split("/")[-1],
            time_delta=settings.RCP_TIME_DELTA,
        ):
            return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)
        return self.safe_post(decoded, *args, **kwargs)

    def safe_post(self, decoded, *args, **kwargs):
        return NotImplemented


class StartBot(RCPSafeView):
    def safe_post(self, decoded, *args, **kwargs):
        required = ["sender", "meeting_id", "bbb_server_uri", "bbb_secret"]
        for x in required:
            if x not in decoded:
                return JsonResponse({"success": False, "message": f"Parameter {x} is missing"}, status=400)

        sender = decoded["sender"]
        if not isinstance(sender, bool):
            return JsonResponse({"success": False, "message": "Parameter sender must be a valid bool"}, status=400)

        bot = Bot.objects.create()
        bot.pid = subprocess.Popen([
            "python3", "bot_script.py",
            "--bbb-url", decoded["bbb_server_uri"],
            "--bbb-secret", decoded["bbb_secret"],
            "--meeting-id", decoded["meeting_id"],
            "--bot", str(bot.id),
            *(("--use-microphone",) if decoded["sender"] else ()),
        ]).pid
        bot.save()

        return JsonResponse({"success": True})


class StopAllBots(RCPSafeView):
    def safe_post(self, decoded, *args, **kwargs):
        for bot in Bot.objects.all():
            try:
                os.kill(bot.pid, signal.SIGTERM)
            except ProcessLookupError:  # Skip already stopped processes
                pass
        Bot.objects.all().delete()
        return JsonResponse({"success": True})
