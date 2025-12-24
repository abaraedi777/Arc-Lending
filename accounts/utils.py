from django.urls import reverse
from eth_utils import keccak
from django.utils.timezone import now
from web3 import Web3


def get_next_route(profile):
    if profile.skipped:
        return reverse("dashboard:dashboard_view")
    if not profile.kyc_level_1:
        return reverse("accounts:kyc1_view")   # e.g. /kyc-level-1/
    if not profile.kyc_level_2:
        return reverse("accounts:kyc2_view")   # e.g. /kyc-level-2/
    if not profile.kyc_level_3:
        return reverse("accounts:kyc3_view")   # e.g. /kyc-level-3/
    return reverse("dashboard:dashboard_view")        # user fully verified


def generate_identity_hash(profile):
    data = f"{profile.wallet.lower()}|{profile.fullname}|{profile.country}|{profile.email}|{profile.dob}|{profile.docType}|{profile.date_created.isoformat()}"
    return keccak(text=data).hex()


# def push_hash_to_blockchain(user_address, identity_hash):
#     w3 = Web3(Web3.HTTPProvider("https://rpc.testnet.arc.network"))

#     contract_address = "0xYourContract"
#     abi = [...]  # Your IdentityContract ABI here

#     contract = w3.eth.contract(address=contract_address, abi=abi)

#     tx = contract.functions.registerUser(
#         Web3.to_checksum_address(user_address),
#         identity_hash
#     ).build_transaction({
#         "from": Web3.to_checksum_address(user_address),
#         "nonce": w3.eth.get_transaction_count(user_address),
#         "gas": 200000,
#         "gasPrice": w3.eth.gas_price,
#     })

#     signed = w3.eth.account.sign_transaction(tx, private_key="USER_PRIVATE_KEY")
#     tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

#     return tx_hash.hex()
