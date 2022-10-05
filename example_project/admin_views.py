from bx_django_utils.admin_extra_views.base_view import AdminExtraViewMixin
from bx_django_utils.admin_extra_views.datatypes import AdminExtraMeta, PseudoApp
from bx_django_utils.admin_extra_views.registry import register_admin_view
from django.http import HttpResponseRedirect
from django.urls.base import reverse
from django.views.generic.base import View


pseudo_app = PseudoApp(meta=AdminExtraMeta(name='YunoHost Django Example Project'))


@register_admin_view(pseudo_app=pseudo_app)
class Redirect2DebugView(AdminExtraViewMixin, View):
    meta = AdminExtraMeta(name='Go to Example Project Debug View')

    def get(self, request):
        url = reverse('debug-view')  # example_project.views.DebugView()
        return HttpResponseRedirect(url)
