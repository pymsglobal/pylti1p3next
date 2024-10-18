from django.http import HttpResponse  # type: ignore
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from pylti1p3.oidc_login import OIDCLogin
from pylti1p3.request import Request

from .cookie import DjangoCookieService
from .redirect import DjangoRedirect
from .request import DjangoRequest
from .session import DjangoSessionService


class DjangoOIDCLogin(OIDCLogin):
    def __init__(
        self,
        request,
        tool_config,
        session_service=None,
        cookie_service=None,
        launch_data_storage=None,
    ):
        django_request = (
            request if isinstance(request, Request) else DjangoRequest(request)
        )
        cookie_service = (
            cookie_service if cookie_service else DjangoCookieService(django_request)
        )
        session_service = (
            session_service if session_service else DjangoSessionService(request)
        )
        super().__init__(
            django_request,
            tool_config,
            session_service,
            cookie_service,
            launch_data_storage,
        )

    def get_redirect(self, url):
        return DjangoRedirect(url, self._cookie_service)

    def get_response(self, html):
        return HttpResponse(html)

    def get_cookies_allowed_js_check(self) -> str:
        protocol, params = self.get_cookies_allowed_js_check_params()

        try:
            return render(
                self._request._request, 
                'pylti1p3/cookies_allowed_js_check.html', 
                {
                    'protocol': protocol,
                    'params': params,
                    'main_text': self._cookies_unavailable_msg_main_text,
                    'click_text': self._cookies_unavailable_msg_click_text,
                    'loading_text': self._cookies_check_loading_text,
                }
            )
        except TemplateDoesNotExist:
            return super().get_cookies_allowed_js_check()
