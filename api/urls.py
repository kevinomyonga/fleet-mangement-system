from django.urls import path, include

urlpatterns = [
    path("user/", include("api.user.urls")),
    path("order/", include("api.order.urls")),
    # Uses custom token
    path("driver/", include("api.driver.urls")),
    path("appointments/", include("api.appointments.urls")),
    # path("organizations/", include("api.organizations.urls")),
]
