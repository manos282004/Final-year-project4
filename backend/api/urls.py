from django.urls import path
from .views import (
    dashboard_data,
    business_types,
    kpi_data,
    strategy_data,
    chatbot,
    analytics_data,
    locations_list,
    location_detail,
    chat_sessions,
    chat_history,
    delete_chat_session,
)

urlpatterns = [
    path("dashboard/", dashboard_data),
    path("strategy/", strategy_data),
    path("kpi/", kpi_data),
    path("business-types/", business_types),
    path("chat/", chatbot),
    path("analytics/", analytics_data),
    path("chat-sessions/", chat_sessions),
    path("chat-history/", chat_history),
    path("chat-sessions/<uuid:session_id>/", delete_chat_session),

    path("locations/", locations_list),
    path("locations/<str:location_id>/", location_detail),
]
