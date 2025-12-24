import secrets
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from eth_account.messages import encode_defunct
from eth_account import Account
from .models import WalletProfile, WalletNonce
from django.shortcuts import render, redirect
from django.views import View
from .utils import get_next_route, generate_identity_hash
from dashboard.utils import store_identity_hash_onchain

# Create your views here.


class LoginView(View):
    def get(self, request, *args, **kwargs):
        # If user is already authenticated, redirect
        wallet = request.session.get("wallet")
        if wallet:
            profile = WalletProfile.objects.get(wallet=wallet)
            return redirect(get_next_route(profile))
        return render(request, "accounts/login.html")
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        user_wallet = data.get("userAddress")
        if not user_wallet:
            return JsonResponse({"error": "Wallet required"}, status=400)

        user_wallet = user_wallet.lower()

        # Generate new nonce
        new_nonce = secrets.token_hex(16)

        WalletNonce.objects.create(
            wallet=user_wallet,
            nonce=new_nonce,
            purpose="auth"
        )

        return JsonResponse({"nonce": new_nonce})



@csrf_exempt
def verify_signature(request):
    try:
        data = json.loads(request.body)
        wallet = data.get("wallet")
        signature = data.get("signature")
        purpose = data.get("purpose")

        if not wallet or not signature:
            return JsonResponse({"error": "Wallet and signature required"}, status=400)

        wallet_lower = wallet.lower()

        # Get latest unused nonce for wallet
        user_nonce = WalletNonce.objects.filter(
            wallet=wallet_lower, 
            is_used=False,
            purpose=purpose
        ).order_by("-date_created").first()

        if not user_nonce:
            return JsonResponse({"error": "Nonce not found"}, status=400)

        message = None
        if purpose == "auth":
            # Verify signature
            message = encode_defunct(text=f"Sign this message to authenticate: {user_nonce.nonce}")
        elif purpose == "kyc_consent":
            # Verify signature
            message = encode_defunct(text=f"Sign this message to Consent: {user_nonce.nonce}")

        recovered = Account.recover_message(message, signature=signature)

        if recovered.lower() != wallet_lower:
            return JsonResponse({"error": "Signature mismatch"}, status=400)

        # Mark nonce used
        user_nonce.is_used = True
        user_nonce.save()

        if purpose == "auth":
            # Create/fetch profile
            profile, created = WalletProfile.objects.get_or_create(wallet=wallet_lower)


            redirect_url = get_next_route(profile)

            # Set Django session
            request.session['wallet'] = wallet_lower

            return JsonResponse({"success": True, "wallet": wallet_lower, "created": created, "redirect": redirect_url})
        
        elif purpose == "kyc_consent":
            try:  
                profile = WalletProfile.objects.get(wallet=wallet, kyc_level_1=True, kyc_level_2=True)
                hash = generate_identity_hash(profile)
                reciept = store_identity_hash_onchain(wallet, hash)

                profile.kyc_level_3 = True 
                profile.verified = True
                profile.save()
                print("HERE")

                redirect_url = get_next_route(profile)

                return JsonResponse({"success": True, "redirect": redirect_url})
            except:
                pass        

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



class SkipKYCView(View):
    def get(self, request, *args, **kwargs):
        wallet = request.session.get("wallet")

        if not wallet:
            return JsonResponse({"error": "Wallet and signature required"}, status=400)
        
        profile = WalletProfile.objects.get(wallet=wallet, kyc_level_1=True)
        profile.skipped = True
        profile.save()
        redirect_url = get_next_route(profile)
        return JsonResponse({"success": True, "redirect": redirect_url})


class KYCL1View(View):
    def get(self, request, *args, **kwargs):
        wallet = request.session.get("wallet")
        if wallet: 
            try:  
                profile = WalletProfile.objects.get(wallet=wallet, kyc_level_1=True)
                if profile:
                    return redirect(get_next_route(profile))  
            except:
                return render(request, "accounts/kyc1.html", {"wallet":wallet})
        else:
            return redirect("accounts:login_view")
        
    def post(self, request, *args, **kwargs):
        fullName = request.POST.get("fullName")
        email = request.POST.get("email")
        country = request.POST.get("country")
        dob = request.POST.get("dob")
        wallet = request.POST.get("wallet")

        try:
            user = WalletProfile.objects.get(wallet=wallet)

            if user:
                user.fullname = fullName
                user.email = email
                user.country = country
                user.dob = dob
                user.kyc_level_1 = True
                user.save()

                return redirect("accounts:kyc2_view")
            else:
                return redirect("accounts:login_view")
        except:
            return redirect("accounts:login_view")
        


class KYCL2View(View):
    def get(self, request, *args, **kwargs):
        wallet = request.session.get("wallet")
        if wallet: 
            try:  
                profile = WalletProfile.objects.get(wallet=wallet, kyc_level_2=True)
                if profile:
                    return redirect(get_next_route(profile))  
            except:
                return render(request, "accounts/kyc2.html", {"wallet":wallet})
        else:
            return redirect("accounts:login_view")
        
    def post(self, request, *args, **kwargs):
        docType = request.POST.get("docType")
        idFront = request.FILES['idFront']
        idBack = request.FILES['idBack']
        selfie = request.FILES['selfie']
        wallet = request.POST.get("wallet")

        try:
            user = WalletProfile.objects.get(wallet=wallet)

            if user:
                user.docType = docType
                user.id_document_front = idFront
                user.id_document_back = idBack
                user.selfie = selfie
                user.kyc_level_2 = True
                user.save()

                return redirect("accounts:kyc3_view")
            else:
                return redirect("accounts:login_view")
        except:
            return redirect("accounts:login_view")   



class KYCL3View(View):
    def get(self, request, *args, **kwargs):
        wallet = request.session.get("wallet")
        if wallet: 
            try:  
                profile = WalletProfile.objects.get(wallet=wallet, kyc_level_3=True)
                if profile:
                    return redirect(get_next_route(profile)) 
                
            except:
                profile = WalletProfile.objects.get(wallet=wallet)

                # Generate new nonce
                new_nonce = secrets.token_hex(16)
                WalletNonce.objects.create(
                    wallet=wallet,
                    nonce=new_nonce,
                    purpose="kyc_consent"
                )
                return render(request, "accounts/kyc3.html", {"profile":profile, "wallet":wallet, "nonce": new_nonce})
        else:
            return redirect("accounts:login_view")


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        request.session.pop('wallet', None)
        print("HERE") 
        return redirect("accounts:login_view")

    
