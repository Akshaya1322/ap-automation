from django.core.files.base import ContentFile

ADVICE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Payment Advice - {{ request_number }}</title>
<style>
  body { font-family: Arial, Helvetica, sans-serif; color: #1e293b; padding: 32px; }
  h1 { font-size: 18px; margin-bottom: 4px; }
  .muted { color: #64748b; font-size: 12px; }
  table { width: 100%; border-collapse: collapse; margin-top: 24px; }
  td { padding: 8px 0; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
  td.label { color: #64748b; width: 40%; }
  td.value { font-weight: 600; text-align: right; }
  .banner { margin-top: 24px; padding: 10px 14px; background: #fef3c7; border: 1px solid #fde68a; font-size: 12px; border-radius: 6px; }
  .total { font-size: 16px; }
</style>
</head>
<body>
  <h1>Payment Advice</h1>
  <p class="muted">Request {{ request_number }} &middot; Generated {{ generated_at }}</p>

  <table>
    <tr><td class="label">Vendor</td><td class="value">{{ vendor_name }}</td></tr>
    <tr><td class="label">Invoice Number</td><td class="value">{{ invoice_number }}</td></tr>
    <tr><td class="label">Payment Method</td><td class="value">{{ method }}</td></tr>
    <tr><td class="label">Transaction Reference</td><td class="value">{{ transaction_ref }}</td></tr>
    <tr><td class="label">Status</td><td class="value">{{ status }}</td></tr>
    <tr><td class="label total">Amount Paid</td><td class="value total">{{ currency }} {{ amount }}</td></tr>
  </table>

  <p class="banner">
    This is a SIMULATED payment advice for demo purposes. No real bank transfer was executed --
    {{ gateway_name }} is a mock banking gateway.
  </p>
</body>
</html>
"""


def generate_payment_advice(payment):
    pr = payment.payment_request
    html = _render(pr, payment)

    filename = f"advice_{pr.request_number}.html"
    payment.advice_file.save(filename, ContentFile(html.encode("utf-8")), save=False)
    payment.advice_generated = True
    payment.save(update_fields=["advice_file", "advice_generated"])
    return payment


def _render(pr, payment):
    from django.template import Context, Engine

    engine = Engine(debug=False)
    template = engine.from_string(ADVICE_TEMPLATE)
    return template.render(
        Context(
            {
                "request_number": pr.request_number,
                "generated_at": payment.payment_date or payment.created_at,
                "vendor_name": pr.vendor.name,
                "invoice_number": pr.invoice.invoice_number,
                "method": pr.get_method_display(),
                "transaction_ref": payment.transaction_ref or "N/A",
                "status": payment.status,
                "currency": pr.currency,
                "amount": pr.amount,
                "gateway_name": (payment.bank_response or {}).get("gateway", "MockBank"),
            }
        )
    )
