from django.db import models

# Create your models here.


class WalletNonce(models.Model):
    PURPOSE_CHOICES = [
        ("auth", "Wallet Authentication"),
        ("kyc_consent", "KYC Consent"),
    ]
    wallet = models.CharField(max_length=42)  # Ethereum wallet address
    nonce = models.CharField(max_length=16)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)


class WalletProfile(models.Model):
    wallet = models.CharField(max_length=42, unique=True)  # Ethereum wallet address
    fullname = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    dob = models.DateField(blank=True, null=True)
    credit_score = models.FloatField(default=0.5)
    docType = models.CharField(max_length=100)
    id_document_front = models.FileField(upload_to='documents/', blank=True, null=True)
    id_document_back = models.FileField(upload_to='documents/', blank=True, null=True)
    selfie = models.FileField(upload_to='selfie/', blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    kyc_level_1 = models.BooleanField(default=False)
    kyc_level_2 = models.BooleanField(default=False)
    kyc_level_3 = models.BooleanField(default=False)

    verified = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False) # to skip KYC
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wallet
    

