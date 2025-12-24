from datetime import datetime, timedelta
from web3 import Web3, Account
from dashboard.models import Loan
from accounts.models import WalletProfile
import time
from decouple import config
import json
from django.utils import timezone
from decimal import Decimal, getcontext


# Load the JSON file
contract_json = None
with open("dashboard/LOAN_CONTRACT_ABI.json", "r") as f:
    contract_json = json.load(f)

# Get the ABI
ABI = contract_json


LOAN_CONTRACT_ADDRESS = config('LOAN_CONTRACT_ADDRESS')
SERVER_PRIVATE_KEY = config('SERVER_PRIVATE_KEY')
w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network"))
contract = w3.eth.contract(address=LOAN_CONTRACT_ADDRESS, abi=ABI)
SERVER_ACCOUNT = Account.from_key(SERVER_PRIVATE_KEY)



def get_wallet_age(wallet_address):
    """
    Attempts to estimate wallet age by checking for the earliest transaction.
    If not found, assumes wallet is new.
    """
    try:
        latest_block = w3.eth.block_number
        scan_range = 5000
        start = max(0, latest_block - scan_range)

        for block_num in range(start, latest_block + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if tx["from"].lower() == wallet_address.lower():
                    return int(time.time()) - block.timestamp

        return 24 * 3600  # assume 1 day old (fallback)
    except:
        return 24 * 3600


def evaluate_loan_request(loan_request: Loan, borrower_wallet, duration):
    profile = WalletProfile.objects.get(wallet=borrower_wallet)
    requested_amount = float(loan_request.requested_amount)

    # -------------------------------
    # BASE SCORE
    # -------------------------------
    score = 1.0  # Starts perfect; penalties adjust from here
    credit_score = loan_request.borrower.credit_score

    # --------------------------------
    # PAST LOAN BEHAVIOR
    # --------------------------------
    user_loans = Loan.objects.filter(borrower=profile, status="approved")

    for loan in user_loans:

        # 1. DEFAULTED = unpaid + past due
        if loan.repaid is False and loan.due_date:
            if loan.due_date < timezone.now():
                score -= 0.35
                credit_score -= 0.2

        # 2. LATE REPAYMENT
        if loan.repaid is True and loan.repaid_at and loan.due_date:
            if loan.repaid_at > loan.due_date:
                score -= 0.18
                credit_score -= 0.1
                
        # 3. ON-TIME REPAYMENT (small reward)
        if loan.repaid is True and loan.repaid_at and loan.due_date:
            if loan.repaid_at <= loan.due_date:
                score += 0.05
                credit_score += 0.05

    # --------------------------------
    # KYC STATUS
    # --------------------------------
    if not profile.verified:
        score -= 0.25
    else:
        credit_score += 0.05

    # --------------------------------
    # ONCHAIN CHECKS
    # --------------------------------
    wallet = Web3.to_checksum_address(borrower_wallet)

    # TX COUNT
    try:
        tx_count = w3.eth.get_transaction_count(wallet)
    except:
        tx_count = 0

    if tx_count == 0:
        score -= 0.20

    # BALANCE LEVEL
    try:
        balance = w3.eth.get_balance(wallet) / 1e18
    except:
        balance = 0

    if balance < 0.001:
        score -= 0.20

    # WALLET AGE CHECK
    # wallet_age_days = get_wallet_age(wallet) / 86400
    # if wallet_age_days < 2:
    #     score -= 0.25

    # --------------------------------
    # FINAL SCORE NORMALIZATION
    # --------------------------------
    score = max(0, min(score, 1))

    score = 0.6 * score + 0.4 * credit_score


    # --------------------------------
    # LOAN OUTCOME
    # --------------------------------
    getcontext().prec = 28  # high enough for small fractions

    requested_amount = Decimal(requested_amount)
    duration = Decimal(duration)

    if score >= Decimal("0.8"):
        status = "approved"
        approved_amount = requested_amount
    elif Decimal("0.7") <= score < Decimal("0.8"):
        status = "approved"
        approved_amount = requested_amount * Decimal("0.7")
    elif Decimal("0.6") <= score < Decimal("0.7"):
        status = "approved"
        approved_amount = requested_amount * Decimal("0.6")
    elif Decimal("0.5") <= score < Decimal("0.6"):
        status = "approved"
        approved_amount = requested_amount * Decimal("0.5")
    else:
        status = "rejected"
        approved_amount = Decimal("0")
        interest = Decimal("0")


    # Use Decimal for interest calculation
    interest = approved_amount * Decimal("10") * (duration / Decimal("365"))

    # Attach results to the loan instance
    loan_request.status = status
    loan_request.approved_amount = approved_amount
    loan_request.interest = interest
    loan_request.total_repay_amount = approved_amount + interest
    loan_request.save()

    return loan_request.id



def get_contract_balance():
    balance = w3.eth.get_balance(LOAN_CONTRACT_ADDRESS)
    return balance / 10**18



# ------------------------
# Store borrower identity hash
# ------------------------
def store_identity_hash_onchain(borrower_address, identity_hash_hex):
    borrower = Web3.to_checksum_address(borrower_address)
    hash_bytes = bytes.fromhex(identity_hash_hex.replace("0x", ""))
    tx = contract.functions.setIdentityHash(borrower, hash_bytes).build_transaction({
        "from": SERVER_ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(SERVER_ACCOUNT.address),
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=SERVER_PRIVATE_KEY)
    print(signed_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt



def to_token_units(val, decimals=6):
    return int(Decimal(str(val)) * Decimal(10 ** decimals))

# ------------------------
# Mint loan on-chain
# ------------------------
def mint_loan_onchain(borrower_address, symbol, amount, interest, repayAmount):
    borrower = Web3.to_checksum_address(borrower_address)
    tx = contract.functions.createLoan(
        borrower,
        symbol,
        to_token_units(amount),
        to_token_units(interest),
        to_token_units(repayAmount)
    ).build_transaction({
        "from": SERVER_ACCOUNT.address,
        "nonce": w3.eth.get_transaction_count(SERVER_ACCOUNT.address),
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=SERVER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Parse LoanCreated event
    logs = contract.events.LoanCreated().process_receipt(receipt)
    loan_id = logs[0]["args"]["loanId"] if logs else None
    return loan_id, receipt





