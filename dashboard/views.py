from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Loan, Deposit
from .utils import evaluate_loan_request, get_contract_balance, mint_loan_onchain
from accounts.models import WalletProfile
from datetime import datetime, timedelta
from django.db.models import Sum
from decouple import config
from django.http import JsonResponse
import json
from django.utils import timezone
from decimal import Decimal


# Create your views here.


class DashboardView(View):
    def get(self, request, *args, **kwargs):
        # If user is not authenticated, redirect
        wallet = request.session.get("wallet")

        if wallet:
            profile = WalletProfile.objects.get(wallet=wallet)

            loans = Loan.objects.filter(borrower=profile).order_by("-created_at")

            deposits = Deposit.objects.filter(depositor=profile).order_by("-created_at")

            # Total borrowed (sum of approved amounts)
            total_borrowed = loans.filter(status="approved").aggregate(total=Sum("approved_amount"))["total"] or 0
            # Outstanding debts (approved but not fully repaid)
            outstanding = loans.filter(status="approved", repaid=False).aggregate(total=Sum("approved_amount"))["total"] or 0
            # Credit score 
            credit_score = profile.credit_score
            #liquidity Amount
            liquidity = get_contract_balance()
            #KYC
            kyc = profile.verified

            LOAN_CONTRACT_ADDRESS = config('LOAN_CONTRACT_ADDRESS')
            context = {
                "total_borrowed": total_borrowed,
                "outstanding": outstanding,
                "credit_score": credit_score,
                "liquidity":liquidity,
                "wallet": wallet,
                "kyc":kyc,
                "loans":loans,
                "deposits":deposits,
                "LOAN_CONTRACT_ADDRESS": LOAN_CONTRACT_ADDRESS
            }
            return render(request, "dashboard/dashboard-home.html", context)

        return redirect("accounts:login_view")
    

    def post(self, request, *args, **kwargs):
        asset = request.POST.get("asset")
        amount = request.POST.get("amount")
        duration = request.POST.get("duration")
        wallet = request.POST.get("wallet")

        try:
            borrower = WalletProfile.objects.get(wallet=wallet)
        except:
            return redirect("accounts:login_view")

        try:
            if Loan.objects.filter(borrower=borrower, status="approved", withdrawn=True, repaid=False).count() >=10:
                # message here to let them know they already owe us
                return redirect("dashboard:dashboard_view")
        except:
            pass
        
        loan_request = Loan.objects.create(
            borrower = borrower,
            loan_duration = int(duration),
            asset_name = asset,
            requested_amount = Decimal(amount),
            interest = Decimal(amount) * Decimal("10") * (Decimal(duration) / Decimal("365")),
            status = "pending",
            due_date = datetime.now() + timedelta(days=int(duration))
            
        )

        evaluate_loan_request(loan_request, wallet, duration)

        if loan_request.status == "approved":
            onchain_loan_id = mint_loan_onchain(loan_request.borrower.wallet, loan_request.asset_name, loan_request.approved_amount, loan_request.interest, loan_request.total_repay_amount)

            print(onchain_loan_id[0])

            loan_request.onchain_loan_id = onchain_loan_id[0]
            loan_request.save()

            return redirect("dashboard:claim_view", loan_id=loan_request.id)
        else:
            return redirect("dashboard:dashboard_view")
    


class ClaimView(View):
    def get(self, request, loan_id, *args, **kwargs):
        # If user is not authenticated, redirect
        wallet = request.session.get("wallet")

        if wallet:
            profile = WalletProfile.objects.get(wallet=wallet)

            loan = get_object_or_404(Loan, id=loan_id)

            LOAN_CONTRACT_ADDRESS = config('LOAN_CONTRACT_ADDRESS')

            #KYC
            kyc = profile.verified

            # Pass loan object to template
            context = {
                "loan": loan,
                "LOAN_CONTRACT_ADDRESS": LOAN_CONTRACT_ADDRESS,
                "kyc":kyc
                
            }
            return render(request, "dashboard/claim.html", context)
       
        return redirect("accounts:login_view")
    

    def post(self, request, loan_id, *args, **kwargs):
        try:
            loan = Loan.objects.get(id=loan_id)
        except:
            return JsonResponse({"error": "NO LOAN WITH THAT ID"}, status=404)
        
        loan.withdrawn = True
        loan.save()

        return JsonResponse({"status":"success"})



class RepayView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        loan_id = data.get("loanID")

        loan = Loan.objects.get(id=int(loan_id))

        loan.repaid = True
        loan.repaid_at = timezone.now()
        loan.save()
        
        return JsonResponse({"status":"success"})
    



class DepositView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        onchainDepoID = data.get("onchainDepoID")
        asset = data.get("asset")
        amount = data.get("amount")
        interest = data.get("interest")
        duration = data.get("duration")
        wallet = data.get("wallet")

        print(onchainDepoID)

        try:
            depositor = WalletProfile.objects.get(wallet=wallet)
        except:
            return redirect("accounts:login_view")
        
        Deposit.objects.create(
            onchain_deposit_id = onchainDepoID,
            depositor = depositor,
            deposit_duration = int(duration),
            asset_name = asset,
            deposit_amount = float(amount),
            interest = float(interest),
            status = True,
            due_date = datetime.now() + timedelta(days=int(duration))
            
        )
        
        return JsonResponse({"status":"success"})



class WithdrawDepositView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        onchainDepoID = int(data.get("onchainDepoID"))
        withdrawnAmount = data.get("withdrawnAmount")
        wallet = data.get("wallet")

        print(onchainDepoID)

        try:
            depositor = WalletProfile.objects.get(wallet=wallet)
        except:
            return redirect("accounts:login_view")
        
        try:
            deposit_obj = Deposit.objects.get(onchain_deposit_id = onchainDepoID, depositor=depositor, withdrawn=False, status=True)
        except:
            return JsonResponse({"error": "Object not found"}, status=404)
        
        deposit_obj.withdrawn = True
        deposit_obj.withdrawn_amount = withdrawnAmount
        deposit_obj.withdrawn_at = timezone.now()
        deposit_obj.save()

        return JsonResponse({"status":"success"})
        

    