from Bcfg2.Reporting.Compat import patterns  # django compat imports
from django.urls import reverse, re_path, NoReverseMatch
from django.http import HttpResponsePermanentRedirect
from Bcfg2.Reporting.utils import filteredUrls, paginatedUrls, timeviewUrls
from Bcfg2.Reporting import views

handler500 = 'Bcfg2.Reporting.views.server_error'

def newRoot(request):
    try:
        grid_view = reverse('reports_grid_view')
    except NoReverseMatch:
        grid_view = '/grid'
    return HttpResponsePermanentRedirect(grid_view)

urlpatterns = patterns('',
    (r'^$', newRoot),

    re_path(r'^manage/?$', views.client_manage, name='reports_client_manage'),
    re_path(r'^client/(?P<hostname>[^/]+)/(?P<pk>\d+)/?$', views.client_detail, name='reports_client_detail_pk'),
    re_path(r'^client/(?P<hostname>[^/]+)/?$', views.client_detail, name='reports_client_detail'),
    re_path(r'^element/(?P<entry_type>\w+)/(?P<pk>\d+)/(?P<interaction>\d+)?/?$', views.config_item, name='reports_item'),
    re_path(r'^element/(?P<entry_type>\w+)/(?P<pk>\d+)/?$', views.config_item, name='reports_item'),
    re_path(r'^entry/(?P<entry_type>\w+)/(?P<pk>\w+)/?$', views.entry_status, name='reports_entry'),
)

urlpatterns += patterns('',
    *timeviewUrls(
        (r'^summary/?$', views.display_summary, None, 'reports_summary'),
        (r'^timing/?$', views.display_timing, None, 'reports_timing'),
        (r'^common/group/(?P<group>[^/]+)/(?P<threshold>\d+)/?$', views.common_problems, None, 'reports_common_problems'),
        (r'^common/group/(?P<group>[^/]+)+/?$', views.common_problems, None, 'reports_common_problems'),
        (r'^common/(?P<threshold>\d+)/?$', views.common_problems, None, 'reports_common_problems'),
        (r'^common/?$', views.common_problems, None, 'reports_common_problems'),
))

urlpatterns += patterns('',
    *filteredUrls(*timeviewUrls(
        (r'^grid/?$', views.client_index, None, 'reports_grid_view'),
        (r'^detailed/?$',
            views.client_detailed_list, None, 'reports_detailed_list'),
        (r'^elements/(?P<item_state>\w+)/?$', views.config_item_list, None, 'reports_item_list'),
)))

urlpatterns += patterns('',
    *paginatedUrls( *filteredUrls(
        (r'^history/?$',
            views.render_history_view, None, 'reports_history'),
        (r'^history/(?P<hostname>[^/|]+)/?$',
            views.render_history_view, None, 'reports_client_history'),
)))
