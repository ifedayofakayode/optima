import os
from dotenv import load_dotenv
import paystackapi as Paystack
from datetime import datetime, timezone

load_dotenv()

# Initialize Paystack with your secret key
paystack_secret = os.getenv("PAYSTACK_SECRET_KEY")
Paystack.api_key = paystack_secret

def initialize_payment(user_email, amount_in_naira, credits_to_give):
    """
    Start a payment transaction.
    Returns a payment URL that the user should be redirected to.
    """
    try:
        # Call Paystack to create a transaction
        response = Paystack.Transaction.initialize(
            reference=str(datetime.now().timestamp()),  # Unique reference
            amount=amount_in_naira * 100,  # Paystack expects amount in kobo (100 kobo = 1 Naira)
            email=user_email,
            metadata={
                'credits_to_give': credits_to_give
            }
        )
        
        if response['status']:
            return {
                'success': True,
                'payment_url': response['data']['authorization_url'],
                'reference': response['data']['reference']
            }
        else:
            return {'success': False, 'error': response['message']}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}