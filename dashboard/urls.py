from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.DashboardView.as_view(), name="dashboard_view"),
    path('claim/<int:loan_id>', views.ClaimView.as_view(), name="claim_view"),
    path('deposit/', views.DepositView.as_view(), name="deposit_view"),
    path('withdraw-deposit/', views.WithdrawDepositView.as_view(), name="withdraw_deposit_view"),
    path('repay-loan/', views.RepayView.as_view(), name="repay_loan_view"),
]
