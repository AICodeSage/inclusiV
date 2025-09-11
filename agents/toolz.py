import httpx
import os
import uuid
from agno.tools import tool
from typing import Any, Callable, Dict
from dotenv import load_dotenv

# Load .env file from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =====================
# Hook for logging
# =====================
def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    print(f"🔹 About to call {function_name} with arguments: {arguments}")
    result = function_call(**arguments)
    print(f"✅ {function_name} completed with result: {result}")
    return result


# =====================
# Helper - MoMo Auth
# =====================
import base64, os, httpx

def momo_get_token(product: str = "collection") -> str:
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv(f"MOMO_SUB_KEY_{product.upper()}")
    api_user = os.getenv(f"MOMO_API_USER_{product.upper()}")
    api_key = os.getenv(f"MOMO_API_KEY_{product.upper()}")

    # Check if all required environment variables are set
    if not all([subscription_key, api_user, api_key]):
        missing_vars = []
        if not subscription_key:
            missing_vars.append(f"MOMO_SUB_KEY_{product.upper()}")
        if not api_user:
            missing_vars.append(f"MOMO_API_USER_{product.upper()}")
        if not api_key:
            missing_vars.append(f"MOMO_API_KEY_{product.upper()}")
        
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")

    basic_auth = base64.b64encode(f"{api_user}:{api_key}".encode()).decode()

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    response = httpx.post(f"{base_url}/{product}/token/", headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


# =====================
# Tool: Get Data Deals (Mock)
# =====================
@tool(
    name="get_data_deals",
    description="Return a list of available MTN data deals (mock).",
    show_result=True,
    requires_confirmation=False,
    tool_hooks=[logger_hook],
)
def get_data_deals() -> dict:
    """Provide mock data deals for selection and display."""
    deals = [
        {"code": "50MB_DAILY", "name": "50MB Daily", "size": "50MB", "validity": "1 day", "priceZAR": "5"},
        {"code": "200MB_DAILY", "name": "200MB Daily", "size": "200MB", "validity": "1 day", "priceZAR": "12"},
        {"code": "1GB_WEEKLY", "name": "1GB Weekly", "size": "1GB", "validity": "7 days", "priceZAR": "35"},
        {"code": "3GB_WEEKLY", "name": "3GB Weekly", "size": "3GB", "validity": "7 days", "priceZAR": "79"},
        {"code": "5GB_ANYTIME", "name": "5GB Anytime", "size": "5GB", "validity": "30 days", "priceZAR": "149"},
        {"code": "10GB_ANYTIME", "name": "10GB Anytime", "size": "10GB", "validity": "30 days", "priceZAR": "249"},
        {"code": "50GB_ANYTIME", "name": "50GB Anytime", "size": "50GB", "validity": "30 days", "priceZAR": "499"},
    ]
    return {"status": "success", "deals": deals}


# =====================
# Tool: Buy Airtime
# =====================
@tool(
    name="buy_airtime",
    description="Buy airtime for a phone number using MTN MoMo Collection API.",
    show_result=True,
    requires_confirmation=False,
    tool_hooks=[logger_hook],
)
def buy_airtime(phone_number: str, amount: str, currency: str = "ZAR") -> dict:
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_COLLECTION")
    api_user = os.getenv(f"MOMO_API_USER_COLLECTION")
    api_key = os.getenv(f"MOMO_API_KEY_COLLECTION")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    # Convert ZAR to EUR for sandbox API (approximate rate: 1 EUR = 20 ZAR)
    original_amount = amount
    original_currency = currency
    if currency == "ZAR":
        # Convert ZAR to EUR for sandbox API
        eur_amount = str(round(float(amount) / 20, 2))
        api_currency = "EUR"
    else:
        eur_amount = amount
        api_currency = currency

    token = momo_get_token("collection")
    ref_id = str(uuid.uuid4())

    payload = {
        "amount": eur_amount,
        "currency": api_currency,
        "externalId": ref_id,
        "payer": {"partyIdType": "MSISDN", "partyId": phone_number},
        "payerMessage": "Airtime purchase",
        "payeeNote": "MoMo Airtime",
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": ref_id,
        "X-Target-Environment": target_env,
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
    }

    try:
        r = httpx.post(f"{base_url}/collection/v1_0/requesttopay", headers=headers, json=payload, timeout=30)
        
        # Add more detailed response information (show original ZAR amounts to user)
        result = {
            "status": r.status_code, 
            "transaction_ref": ref_id,
            "amount": original_amount,
            "currency": original_currency,
            "message": f"Airtime purchase of {original_currency} {original_amount} submitted successfully"
        }
        
        # Add response details for debugging
        if r.status_code != 202:  # 202 is expected success for MoMo
            try:
                error_detail = r.json() if r.text else "No error details"
                result["error_detail"] = error_detail
                result["message"] = f"Airtime purchase failed. Please try again later.\nReference: {ref_id}"
            except:
                result["error_detail"] = r.text[:200] if r.text else "No response body"
                result["message"] = f"Airtime purchase failed. Please try again later.\nReference: {ref_id}"
        else:
            result["message"] = f"✅ Successfully purchased {original_currency} {original_amount} airtime for {phone_number}\nReference: {ref_id}"
        
        return result
        
    except httpx.TimeoutException:
        return {"status": "timeout", "transaction_ref": ref_id, "message": f"Request timed out - MTN sandbox may be slow\nReference: {ref_id}"}
    except Exception as e:
        return {"status": "error", "transaction_ref": ref_id, "message": f"Network error: {str(e)}\nReference: {ref_id}"}


# =====================
# Tool: Buy Data
# =====================
@tool(
    name="buy_data",
    description="Buy mobile data bundle using MoMo Collection API.",
    show_result=True,
    requires_confirmation=False,
    tool_hooks=[logger_hook],
)
def buy_data(phone_number: str, bundle_code: str, amount: str, currency: str = "ZAR") -> dict:
    """
    Buy data bundles using MTN MoMo API via the Collection product.
    """
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_COLLECTION")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    # Convert ZAR to EUR for sandbox API (approximate rate: 1 EUR = 20 ZAR)
    original_amount = amount
    original_currency = currency
    if currency == "ZAR":
        eur_amount = str(round(float(amount) / 20, 2))
        api_currency = "EUR"
    else:
        eur_amount = amount
        api_currency = currency

    ref_id = str(uuid.uuid4())

    try:
        # Get access token using existing helper
        token = momo_get_token("collection")

        request_data = {
            "amount": eur_amount,
            "currency": api_currency,
            "externalId": ref_id,
            "payer": {"partyIdType": "MSISDN", "partyId": phone_number},
            "payerMessage": f"Data bundle {bundle_code} purchase",
            "payeeNote": f"MoMo Data {bundle_code}",
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": ref_id,
            "X-Target-Environment": target_env,
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Content-Type": "application/json",
        }

        response = httpx.post(
            f"{base_url}/collection/v1_0/requesttopay",
            json=request_data,
            headers=headers,
            timeout=30.0,
        )

        result = {
            "status": response.status_code,
            "transaction_ref": ref_id,
            "amount": original_amount,
            "currency": original_currency,
        }

        if response.status_code == 202:
            result["message"] = (
                f"✅ Successfully purchased {bundle_code} data for {phone_number} "
                f"(ZAR {original_amount})\nReference: {ref_id}"
            )
        else:
            try:
                error_detail = response.json() if response.text else "No error details"
            except Exception:
                error_detail = response.text[:200] if response.text else "No response body"
            result.update(
                {
                    "message": (
                        f"Data bundle {bundle_code} purchase of R{original_amount} failed for {phone_number}\n"
                        f"Reference: {ref_id}"
                    ),
                    "error_detail": error_detail,
                }
            )

        return result

    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "transaction_ref": ref_id,
            "message": (
                f"Request timed out while purchasing {bundle_code} for {phone_number}\n"
                f"Reference: {ref_id}"
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "transaction_ref": ref_id,
            "message": (
                f"Data bundle {bundle_code} purchase of R{original_amount} failed for {phone_number}\n"
                f"Reference: {ref_id}"
            ),
            "error_detail": str(e),
        }


# =====================
# Tool: Transfer Money
# =====================
@tool(
    name="transfer_money",
    description="Send money to another MoMo user using Disbursement API.",
    show_result=True,
    requires_confirmation=False,
    tool_hooks=[logger_hook],
)
def transfer_money(receiver_number: str, amount: str, currency: str = "ZAR") -> dict:
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_DISBURSEMENT")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    # Convert ZAR to EUR for sandbox API (approximate rate: 1 EUR = 20 ZAR)
    original_amount = amount
    original_currency = currency
    if currency == "ZAR":
        # Convert ZAR to EUR for sandbox API
        eur_amount = str(round(float(amount) / 20, 2))
        api_currency = "EUR"
    else:
        eur_amount = amount
        api_currency = currency

    token = momo_get_token("disbursement")
    ref_id = str(uuid.uuid4())

    payload = {
        "amount": eur_amount,
        "currency": api_currency,
        "externalId": ref_id,
        "payee": {"partyIdType": "MSISDN", "partyId": receiver_number},
        "payerMessage": "Money transfer",
        "payeeNote": "Received via MoMo",
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": ref_id,
        "X-Target-Environment": target_env,
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
    }

    r = httpx.post(f"{base_url}/disbursement/v1_0/transfer", headers=headers, json=payload)
    
    # Return response with original ZAR amounts (hide EUR conversion from user)
    result = {
        "status": r.status_code, 
        "transaction_ref": ref_id,
        "amount": original_amount,
        "currency": original_currency,
    }
    
    if r.status_code == 202:  # Success
        result["message"] = f"✅ Successfully sent {original_currency} {original_amount} to {receiver_number}\nReference: {ref_id}"
    else:
        result["message"] = f"Transfer failed. Please try again later.\nReference: {ref_id}"
    
    return result


# =====================
# Tool: Check Balance
# =====================
@tool(
    name="check_balance",
    description="Check MoMo account balance using Remittance API.",
    show_result=True,
    tool_hooks=[logger_hook],
)
def check_balance() -> dict:
    """Check MoMo account balance. Returns mock data for sandbox testing."""
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_REMITTANCE")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    # For sandbox testing, return mock balance data since the API is unreliable
    if target_env == "sandbox":
        import random
        # Generate a realistic mock balance for demo purposes
        mock_balance = random.choice(["1000.00", "2500.50", "750.25", "3200.00", "500.00"])
        return {
            "availableBalance": mock_balance,
            "currency": "ZAR",
            "message": f"Your current balance is ZAR {mock_balance}",
            "status": "success"
        }

    # For production, attempt real API call
    try:
        token = momo_get_token("remittance")
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Target-Environment": target_env,
            "Ocp-Apim-Subscription-Key": subscription_key,
        }

        r = httpx.get(f"{base_url}/remittance/v1_0/account/balance", headers=headers, timeout=10)
        r.raise_for_status()
        balance_data = r.json()
        
        # Convert EUR to ZAR for display (if needed)
        if balance_data.get("currency") == "EUR":
            eur_amount = float(balance_data.get("availableBalance", "0"))
            zar_amount = eur_amount * 20  # Convert EUR to ZAR
            balance_data["availableBalance"] = f"{zar_amount:.2f}"
        
        balance_data["currency"] = "ZAR"
        balance_data["message"] = f"Your current balance is ZAR {balance_data['availableBalance']}"
        balance_data["status"] = "success"
        return balance_data
        
    except Exception as e:
        # Return user-friendly error message
        return {
            "availableBalance": "0",
            "currency": "ZAR",
            "message": "Unable to retrieve balance at the moment. Please try again later.",
            "status": "error",
            "error_detail": str(e)
        }


# =====================
# Tool: Validate Number
# =====================
@tool(
    name="validate_number",
    description="Check if a given phone number is a registered MoMo account.",
    show_result=True,
    tool_hooks=[logger_hook],
)
def validate_number(phone_number: str) -> dict:
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_COLLECTION")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    token = momo_get_token("collection")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": target_env,
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    r = httpx.get(f"{base_url}/collection/v1_0/accountholder/MSISDN/{phone_number}/active", headers=headers)
    r.raise_for_status()
    return r.json()


# =====================
# Tool: Check Transaction Status
# =====================
@tool(
    name="test_momo_connection",
    description="Test MTN MoMo API connectivity and authentication.",
    show_result=True,
    requires_confirmation=False,
    tool_hooks=[logger_hook],
)
def test_momo_connection() -> dict:
    """Test MTN MoMo API connectivity."""
    try:
        token = momo_get_token("collection")
        if token:
            return {
                "status": "success",
                "message": "✅ MTN MoMo API connection successful",
                "token_received": True
            }
        else:
            return {
                "status": "error", 
                "message": "❌ Failed to get authentication token",
                "token_received": False
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Connection test failed: {str(e)}",
            "token_received": False
        }

@tool(
    name="check_tx_status",
    description="Check the status of a MoMo transaction by reference ID.",
    show_result=True,
    tool_hooks=[logger_hook],
)
def check_tx_status(ref_id: str) -> dict:
    base_url = os.getenv("MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com")
    subscription_key = os.getenv("MOMO_SUB_KEY_COLLECTION")
    target_env = os.getenv("MOMO_TARGET_ENV", "sandbox")

    token = momo_get_token("collection")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": target_env,
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    r = httpx.get(f"{base_url}/collection/v1_0/requesttopay/{ref_id}", headers=headers)
    r.raise_for_status()
    return r.json()


# Export all functions
__all__ = [
    'buy_airtime', 'buy_data', 'transfer_money',
    'check_balance', 'validate_number', 'check_tx_status', 'get_data_deals', 'test_momo_connection'
]
