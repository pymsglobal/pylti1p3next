import typing as t
from flask import make_response, render_template  # type: ignore
from pylti1p3.oidc_login import OIDCLogin
from .cookie import FlaskCookieService
from .session import FlaskSessionService
from .redirect import FlaskRedirect


class FlaskOIDCLogin(OIDCLogin):
    cookie_check_template_name = "cookies_allowed_js_check.html"

    def __init__(
        self,
        request,
        tool_config,
        *,
        session_service: t.Optional[FlaskSessionService] = None,
        cookie_service: t.Optional[FlaskCookieService] = None,
        launch_data_storage=None,
    ):
        cookie_service = (
            cookie_service if cookie_service else FlaskCookieService(request)
        )
        session_service = (
            session_service if session_service else FlaskSessionService(request)
        )
        super().__init__(
            request=request,
            tool_config=tool_config,
            session_service=session_service,
            cookie_service=cookie_service,
            launch_data_storage=launch_data_storage,
        )

    def get_redirect(self, url):
        return FlaskRedirect(url, self._cookie_service)

    def get_response(self, html):
        return make_response(html)
