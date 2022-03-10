import json

import rc_protocol
from django.core.handlers.wsgi import WSGIRequest
from django.views import View
from django.http import JsonResponse

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
            shared_secret=settings.RCP_SECRET,
            salt=request.get_full_path().split("/")[-1],
            time_delta=settings.RCP_TIME_DELTA,
        ):
            return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)
        return self.safe_post(decoded, *args, **kwargs)

    def safe_post(self, decoded, *args, **kwargs):
        return NotImplemented


class StartBot(RCPSafeView):
    def safe_post(self, decoded, *args, **kwargs):
        return JsonResponse({"success": True})
