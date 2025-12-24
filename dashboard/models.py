from django.db import models
from accounts.models import WalletProfile
from decimal import Decimal


# Create your models here.


class Loan(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]
    onchain_loan_id = models.IntegerField(null=True, blank=True)
    borrower = models.ForeignKey(WalletProfile, on_delete=models.CASCADE)
    asset_name = models.CharField(max_length=50)
    loan_duration = models.IntegerField()
    requested_amount = models.DecimalField(max_digits=18, decimal_places=6)
    interest = models.DecimalField(max_digits=18, decimal_places=6)
    approved_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    total_repay_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    due_date = models.DateTimeField(null=True, blank=True)
    repaid_at = models.DateTimeField(null=True, blank=True)
    withdrawn = models.BooleanField(default=False)
    repaid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)




class Deposit(models.Model):
    onchain_deposit_id = models.IntegerField(null=True, blank=True)
    depositor = models.ForeignKey(WalletProfile, on_delete=models.CASCADE)
    asset_name = models.CharField(max_length=50)
    deposit_duration = models.IntegerField()
    deposit_amount = models.DecimalField(max_digits=18, decimal_places=6)
    interest = models.DecimalField(max_digits=18, decimal_places=6)
    withdrawn_amount = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn = models.BooleanField(default=False)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def total_earned(self):
        return (self.deposit_amount or Decimal(0)) + (self.interest or Decimal(0))
