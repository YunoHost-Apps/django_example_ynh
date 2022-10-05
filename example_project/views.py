import logging

from django.conf import settings
from django.http import HttpRequest
from django.views.generic import TemplateView

from example_project import __version__


logger = logging.getLogger(__name__)


class DebugView(TemplateView):
    template_name = 'example_project/debug_view.html'

    def get(self, request, *args, **kwargs):
        logger.info('DebugView request from user: %s', request.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **context):
        request: HttpRequest = self.request
        user = request.user
        context.update(
            dict(
                version=__version__,
                user=user,
                env_type=settings.ENV_TYPE,
            )
        )
        if user.is_authenticated:
            context['meta'] = request.META
        return super().get_context_data(**context)
