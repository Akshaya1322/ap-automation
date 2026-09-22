"""Mock banking gateway.

This is a SIMULATION ONLY -- no real bank, NEFT/RTGS network, or payment
rail is contacted. It exists so the payment-processing flow can be
demonstrated end-to-end without real banking credentials. Every response
this returns is tagged `"simulated": True` and the UI must never claim a
real transfer occurred. Swapping in a real gateway later means implementing
this same `pay()` contract against an actual banking/payment API.
"""

import random
import uuid


class MockBankingGateway:
    name = "MockBank (Simulated)"

    def pay(self, payment_request):
        """Simulate initiating a bank transfer. ~92% succeed immediately,
        the rest fail with a plausible reason, purely for demo realism."""
        success = random.random() < 0.92
        transaction_ref = f"SIM-{uuid.uuid4().hex[:12].upper()}"

        if success:
            return {
                "success": True,
                "transaction_ref": transaction_ref,
                "response": {
                    "simulated": True,
                    "gateway": self.name,
                    "message": "Payment settled successfully (simulated -- no real funds were moved).",
                    "method": payment_request.method,
                    "amount": str(payment_request.amount),
                    "currency": payment_request.currency,
                },
            }

        reason = random.choice(
            ["Beneficiary bank details could not be verified.", "Simulated gateway timeout.", "Daily simulated transfer limit exceeded."]
        )
        return {
            "success": False,
            "transaction_ref": transaction_ref,
            "response": {
                "simulated": True,
                "gateway": self.name,
                "message": f"Payment failed (simulated): {reason}",
            },
        }


def get_banking_gateway():
    return MockBankingGateway()
