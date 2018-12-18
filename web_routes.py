import json

from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor

from yombo.lib.webinterface.auth import require_auth
from yombo.core.log import get_logger

logger = get_logger("modules.wemo.web_routes")

def module_wemo_routes(webapp):
    """
    Adds routes to the webinterface module.

    :param webapp: A pointer to the webapp, it's used to setup routes.
    :return:
    """
    with webapp.subroute("/module_settings") as webapp:

        def root_breadcrumb(webinterface, request):
            webinterface.add_breadcrumb(request, "/?", "Home")
            webinterface.add_breadcrumb(request, "/modules/index", "Modules")
            webinterface.add_breadcrumb(request, "/module_settings/wemo/index", "Wemo")

        @webapp.route("/wemo", methods=['GET'])
        @require_auth()
        def page_module_wemo_get(webinterface, request, session):
            return webinterface.redirect(request, '/module_settings/wemo/index')

        @webapp.route("/wemo/index", methods=['GET'])
        @require_auth()
        def page_tools_module_wemo_index_get(webinterface, request, session):
            page = webinterface.webapp.templates.get_template('modules/wemo/web/index.html')
            root_breadcrumb(webinterface, request)
            return page.render(alerts=webinterface.get_alerts(),
                               )

        @webapp.route("/wemo/discover", methods=['GET'])
        @require_auth()
        def page_tools_module_wemo_heal_get(webinterface, request, session):
            wemo = webinterface._Modules['Wemo']
            reactor.callLater(0.5, wemo.discover_devices)
            page = webinterface.webapp.templates.get_template('modules/wemo/web/discover.html')
            root_breadcrumb(webinterface, request)
            webinterface.add_breadcrumb(request, "/module_settings/wemo/discover", "Discover")
            return page.render(alerts=webinterface.get_alerts())
