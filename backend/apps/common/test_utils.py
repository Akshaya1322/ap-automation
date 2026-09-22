from decimal import Decimal

from apps.approvals.models import ApprovalMatrixRule
from apps.authentication.models import Role, User
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderLineItem
from apps.vendors.models import Vendor, VendorBankDetails, VendorStatus


def make_user(role, username=None, **kwargs):
    username = username or f"{role.lower()}_{User.objects.count()}"
    user = User.objects.create_user(username=username, password="Test@12345", role=role, **kwargs)
    return user


def make_vendor(name="Test Vendor", gstin="27AAACB1234C1Z5", with_bank=True, **kwargs):
    vendor = Vendor.objects.create(
        name=name,
        code=f"VEN-{Vendor.objects.count() + 1:04d}",
        gstin=gstin,
        status=VendorStatus.ACTIVE,
        is_active=True,
        **kwargs,
    )
    if with_bank:
        VendorBankDetails.objects.create(
            vendor=vendor,
            account_holder_name=name,
            account_number="123456789012",
            bank_name="Test Bank",
            ifsc_code="TEST0001234",
        )
    return vendor


def make_po(vendor, total_amount=Decimal("11800.00"), lines=None):
    po = PurchaseOrder.objects.create(
        po_number=f"PO-TEST-{PurchaseOrder.objects.count() + 1:04d}",
        vendor=vendor,
        order_date="2026-01-01",
        currency="INR",
        subtotal=total_amount / Decimal("1.18"),
        tax_amount=total_amount - (total_amount / Decimal("1.18")),
        total_amount=total_amount,
    )
    lines = lines or [{"description": "Item 1", "quantity": Decimal("1"), "unit_price": total_amount}]
    for i, line in enumerate(lines, start=1):
        PurchaseOrderLineItem.objects.create(
            purchase_order=po,
            line_no=i,
            description=line["description"],
            quantity=line["quantity"],
            unit_price=line["unit_price"],
            tax_amount=Decimal("0"),
            amount=line["quantity"] * line["unit_price"],
        )
    return po


def setup_approval_matrix():
    ApprovalMatrixRule.objects.all().delete()
    ApprovalMatrixRule.objects.create(min_amount=Decimal("0"), max_amount=Decimal("50000"), required_roles=[Role.AP_MANAGER])
    ApprovalMatrixRule.objects.create(
        min_amount=Decimal("50000.01"), max_amount=Decimal("500000"), required_roles=[Role.AP_MANAGER, Role.FINANCE_MANAGER]
    )
    ApprovalMatrixRule.objects.create(
        min_amount=Decimal("500000.01"), max_amount=None, required_roles=[Role.AP_MANAGER, Role.FINANCE_MANAGER, Role.ADMIN]
    )
