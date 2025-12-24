from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login_view"),
    path('logout/', views.LogoutView.as_view(), name="logout_view"),
    path('verify_signature/', views.verify_signature, name='verify_signature'),
    path('skip-kyc/', views.SkipKYCView.as_view(), name='skip_kyc_view'),
    path('kyc1/', views.KYCL1View.as_view(), name='kyc1_view'),
    path('kyc2/', views.KYCL2View.as_view(), name='kyc2_view'),
    path('kyc3/', views.KYCL3View.as_view(), name='kyc3_view'),
]
