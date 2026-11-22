import logging
import uuid
from contextvars import ContextVar

import sentry_sdk

logger = logging.getLogger(__name__)

request_context: ContextVar[dict | None] = ContextVar("request_context", default=None)

FEED_ROUTES = {"hebcal:calendar_file", "hebcal:legacy_calendar_file"}


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        context = request_context.get() or {}
        record.request_id = context.get("request_id")
        record.user_id = context.get("user_id")
        return True


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Railway-Request-Id") or uuid.uuid4().hex
        # Reading request.user marks the session as accessed, which adds
        # "Vary: Cookie" to the response. Feed fetches carry no session cookie,
        # so checking the key first keeps their headers unchanged.
        user_id = request.user.pk if request.session.session_key else None
        token = request_context.set({"request_id": request_id, "user_id": user_id})
        sentry_sdk.set_tag("request_id", request_id)
        try:
            response = self.get_response(request)
            match = request.resolver_match
            route = match.view_name if match and match.url_name else request.path
            if user_id is not None or route in FEED_ROUTES:
                logger.info(
                    "%s %s %s",
                    request.method,
                    route,
                    response.status_code,
                    extra={"route": route, "status": response.status_code},
                )
            return response
        finally:
            request_context.reset(token)
