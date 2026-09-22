import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.approvals.models import ApprovalMatrixRule
from apps.approvals.services import apply_action, create_workflow
from apps.audit_logs.services import log_action
from apps.invoices.matching import match_invoice_to_po
from apps.payments.advice import generate_payment_advice
from apps.authentication.models import Role, User
from apps.invoices.models import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    Invoice,
    InvoiceException,
    InvoiceExtractedField,
    InvoiceLineItem,
    InvoiceStatus,
)
from apps.notifications.services import notify_user
from apps.payments.models import Payment, PaymentMethod, PaymentRequest, PaymentStatus
from apps.purchase_orders.models import (
    GoodsReceipt,
    GoodsReceiptLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
    PurchaseOrderStatus,
)
from apps.vendors.models import Vendor, VendorBankDetails, VendorStatus

random.seed(42)

DEMO_PASSWORD = "Demo@12345"

USERS = [
    dict(username="admin", email="admin@ap-automation.local", first_name="System", last_name="Admin", role=Role.ADMIN, password="Admin@12345"),
    dict(username="ap.manager", email="ap.manager@ap-automation.local", first_name="Meera", last_name="Nair", role=Role.AP_MANAGER, password=DEMO_PASSWORD),
    dict(username="ap.processor", email="ap.processor@ap-automation.local", first_name="Rahul", last_name="Sharma", role=Role.AP_PROCESSOR, password=DEMO_PASSWORD),
    dict(username="approver", email="approver@ap-automation.local", first_name="Anita", last_name="Rao", role=Role.APPROVER, password=DEMO_PASSWORD),
    dict(username="finance.manager", email="finance.manager@ap-automation.local", first_name="Vikram", last_name="Malhotra", role=Role.FINANCE_MANAGER, password=DEMO_PASSWORD),
    dict(username="auditor", email="auditor@ap-automation.local", first_name="Sneha", last_name="Iyer", role=Role.AUDITOR, password=DEMO_PASSWORD),
]

VENDOR_DATA = [
    dict(name="Bluewave Office Supplies Pvt Ltd", code="VEN-1001", gstin="27AAACB1234C1Z5", city="Mumbai", state="Maharashtra", category="Office Supplies"),
    dict(name="Nexgen IT Solutions Pvt Ltd", code="VEN-1002", gstin="29AABCN5678D1Z2", city="Bengaluru", state="Karnataka", category="IT Services"),
    dict(name="Sunrise Logistics & Freight", code="VEN-1003", gstin="24AACCS4321E1Z8", city="Ahmedabad", state="Gujarat", category="Logistics"),
    dict(name="Prime Facility Management Co", code="VEN-1004", gstin="07AABCP7788F1Z3", city="New Delhi", state="Delhi", category="Facility Management"),
    dict(name="Orion Manufacturing Industries", code="VEN-1005", gstin="33AAACO9988G1Z6", city="Chennai", state="Tamil Nadu", category="Manufacturing"),
    dict(name="Crimson Marketing & Media", code="VEN-1006", gstin="19AABCC6655H1Z1", city="Kolkata", state="West Bengal", category="Marketing"),
    dict(name="Vertex Consulting Group", code="VEN-1007", gstin="06AAACV3322I1Z9", city="Gurugram", state="Haryana", category="Consulting"),
    dict(name="Golden Harvest Catering Services", code="VEN-1008", gstin="27AABCG1122J1Z4", city="Pune", state="Maharashtra", category="Catering"),
    dict(name="Skyline Constructions Ltd", code="VEN-1009", gstin="29AAACS4455K1Z7", city="Bengaluru", state="Karnataka", category="Construction"),
    dict(name="Apex Electricals & Hardware", code="VEN-1010", gstin="24AABCA7766L1Z0", city="Surat", state="Gujarat", category="Hardware"),
]

DEPARTMENTS = ["Finance", "Operations", "IT", "Marketing", "HR", "Procurement"]


def d(value):
    return Decimal(str(value))


class Command(BaseCommand):
    help = "Seed realistic demo data for the AP Automation platform."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing transactional data before seeding.")

    def handle(self, *args, **options):
        if options["reset"]:
            self.reset_data()

        with transaction.atomic():
            users = self.create_users()
            self.create_approval_matrix()
            vendors = self.create_vendors(users)
            pos = self.create_purchase_orders(vendors, users)
            self.create_invoices(vendors, pos, users)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def reset_data(self):
        self.stdout.write("Resetting existing transactional data...")
        from apps.audit_logs.models import AuditLog
        from apps.notifications.models import Notification

        Notification.objects.all().delete()
        AuditLog.objects.all().delete()
        Payment.objects.all().delete()
        PaymentRequest.objects.all().delete()
        InvoiceException.objects.all().delete()
        InvoiceExtractedField.objects.all().delete()
        InvoiceLineItem.objects.all().delete()
        Invoice.objects.all().delete()
        GoodsReceiptLineItem.objects.all().delete()
        GoodsReceipt.objects.all().delete()
        PurchaseOrderLineItem.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        VendorBankDetails.objects.all().delete()
        Vendor.objects.all().delete()

    # ------------------------------------------------------------------
    def create_users(self):
        users = {}
        for u in USERS:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults=dict(
                    email=u["email"],
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    role=u["role"],
                    department="Finance",
                    is_staff=(u["role"] == Role.ADMIN),
                    is_superuser=(u["role"] == Role.ADMIN),
                ),
            )
            if created:
                user.set_password(u["password"])
                user.save()
            else:
                user.role = u["role"]
                user.save(update_fields=["role"])
            users[u["role"]] = user
        self.stdout.write(f"Users ready: {list(users.keys())}")
        return users

    def create_approval_matrix(self):
        ApprovalMatrixRule.objects.all().delete()
        ApprovalMatrixRule.objects.create(min_amount=d(0), max_amount=d(50000), required_roles=[Role.AP_MANAGER])
        ApprovalMatrixRule.objects.create(
            min_amount=d(50000.01), max_amount=d(500000), required_roles=[Role.AP_MANAGER, Role.FINANCE_MANAGER]
        )
        # Highest band: Finance Manager and Admin approve in PARALLEL (both
        # act independently, in either order) after AP Manager -- see
        # apps/approvals/services.py for how a nested role list becomes a
        # shared step_number instead of two more sequential steps.
        ApprovalMatrixRule.objects.create(
            min_amount=d(500000.01),
            max_amount=None,
            required_roles=[Role.AP_MANAGER, [Role.FINANCE_MANAGER, Role.ADMIN]],
        )
        self.stdout.write("Approval matrix configured.")

    def create_vendors(self, users):
        vendors = []
        for i, v in enumerate(VENDOR_DATA):
            status = VendorStatus.ACTIVE if i < 8 else (VendorStatus.UNDER_REVIEW if i == 8 else VendorStatus.DRAFT)
            vendor, _ = Vendor.objects.get_or_create(
                code=v["code"],
                defaults=dict(
                    name=v["name"],
                    gstin=v["gstin"],
                    pan=v["gstin"][2:12],
                    email=f"accounts@{v['code'].lower()}.example.com",
                    phone=f"+91 98{random.randint(10000000, 99999999)}",
                    contact_person="Accounts Team",
                    address_line1=f"{random.randint(1, 500)}, Industrial Area",
                    city=v["city"],
                    state=v["state"],
                    pincode=str(random.randint(400001, 700099)),
                    category=v["category"],
                    department=random.choice(DEPARTMENTS),
                    payment_terms_days=random.choice([15, 30, 45, 60]),
                    status=status,
                    is_active=status in (VendorStatus.ACTIVE, VendorStatus.UNDER_REVIEW),
                    created_by=users[Role.AP_MANAGER],
                ),
            )
            if status == VendorStatus.ACTIVE:
                VendorBankDetails.objects.get_or_create(
                    vendor=vendor,
                    defaults=dict(
                        account_holder_name=v["name"],
                        account_number=str(random.randint(10**11, 10**12 - 1)),
                        bank_name=random.choice(["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank"]),
                        ifsc_code=f"{random.choice(['HDFC','ICIC','SBIN','UTIB'])}0{random.randint(100000,999999)}",
                        branch=v["city"],
                        is_verified=True,
                    ),
                )
            vendors.append(vendor)
        self.stdout.write(f"Vendors ready: {len(vendors)}")
        return vendors

    def create_purchase_orders(self, vendors, users):
        pos = []
        po_seq = 1
        for vendor in vendors[:8]:
            for _ in range(random.choice([1, 1, 2])):
                po_number = f"PO-2026-{po_seq:04d}"
                po_seq += 1
                order_date = date.today() - timedelta(days=random.randint(20, 150))
                po = PurchaseOrder.objects.create(
                    po_number=po_number,
                    vendor=vendor,
                    order_date=order_date,
                    department=random.choice(DEPARTMENTS),
                    currency="INR",
                    status=random.choice([PurchaseOrderStatus.OPEN, PurchaseOrderStatus.CLOSED]),
                    created_by=users[Role.AP_MANAGER],
                )
                subtotal = Decimal("0")
                for line_no in range(1, random.randint(2, 4) + 1):
                    qty = d(random.randint(1, 20))
                    unit_price = d(random.choice([500, 1200, 2500, 4800, 9800, 15000]))
                    amount = qty * unit_price
                    tax = (amount * d("0.18")).quantize(d("0.01"))
                    PurchaseOrderLineItem.objects.create(
                        purchase_order=po,
                        line_no=line_no,
                        description=f"{vendor.category} item #{line_no}",
                        quantity=qty,
                        unit_price=unit_price,
                        tax_amount=tax,
                        amount=amount + tax,
                    )
                    subtotal += amount
                tax_amount = (subtotal * d("0.18")).quantize(d("0.01"))
                po.subtotal = subtotal
                po.tax_amount = tax_amount
                po.total_amount = subtotal + tax_amount
                po.save(update_fields=["subtotal", "tax_amount", "total_amount"])

                if po.status == PurchaseOrderStatus.CLOSED:
                    grn = GoodsReceipt.objects.create(
                        grn_number=f"GRN-2026-{po_seq:04d}",
                        purchase_order=po,
                        received_date=order_date + timedelta(days=random.randint(2, 10)),
                        received_by=users[Role.AP_PROCESSOR],
                    )
                    for line in po.line_items.all():
                        GoodsReceiptLineItem.objects.create(
                            goods_receipt=grn, po_line_item=line, quantity_received=line.quantity
                        )
                pos.append(po)
        self.stdout.write(f"Purchase orders ready: {len(pos)}")
        return pos

    # ------------------------------------------------------------------
    def _extract_fields(self, invoice, confidence_base):
        fields = [
            ("vendor_name", invoice.vendor.name if invoice.vendor else invoice.vendor_name_raw, True),
            ("invoice_number", invoice.invoice_number, True),
            ("invoice_date", str(invoice.invoice_date), True),
            ("gstin", invoice.gstin, True),
            ("total_amount", str(invoice.total_amount), True),
            ("subtotal", str(invoice.subtotal), False),
            ("tax_amount", str(invoice.tax_amount), False),
            ("due_date", str(invoice.due_date or ""), False),
            ("po_number", invoice.po_number_raw, False),
        ]
        for name, value, mandatory in fields:
            conf = max(30, min(99, confidence_base + random.randint(-8, 8)))
            InvoiceExtractedField.objects.create(
                invoice=invoice,
                field_name=name,
                value=value or "",
                confidence=conf,
                is_mandatory=mandatory,
                validation_status="VALID" if (value and conf >= 60) else "INVALID",
            )

    def _add_line_items(self, invoice, subtotal):
        remaining = subtotal
        n = random.randint(1, 3)
        for i in range(1, n + 1):
            amount = (remaining / (n - i + 1)).quantize(d("0.01"))
            remaining -= amount
            qty = d(random.randint(1, 10))
            InvoiceLineItem.objects.create(
                invoice=invoice,
                line_no=i,
                description=f"{invoice.vendor.category if invoice.vendor else 'General'} item #{i}",
                quantity=qty,
                unit_price=(amount / qty).quantize(d("0.01")),
                tax_amount=(amount * d("0.18")).quantize(d("0.01")),
                amount=amount,
            )

    def _confidence_level(self, score):
        from apps.invoices.utils import confidence_level

        return confidence_level(score)

    def create_invoices(self, vendors, pos, users):
        active_vendors = [v for v in vendors if v.status == VendorStatus.ACTIVE]
        counter = 1
        created = []

        def next_number():
            nonlocal counter
            n = f"INV-2026-{counter:04d}"
            counter += 1
            return n

        def make_invoice(vendor, po, days_ago, amount, status, confidence, invoice_number=None,
                          gstin_override=None, force_mismatch=False, mirror_po=False):
            vendor_obj = vendor
            invoice_date = date.today() - timedelta(days=days_ago)
            if mirror_po and po:
                amount = po.total_amount
            subtotal = (amount / d("1.18")).quantize(d("0.01"))
            tax = amount - subtotal
            cgst = (tax / 2).quantize(d("0.01")) if vendor_obj.state != "Karnataka" else d("0")
            sgst = cgst
            igst = tax - cgst - sgst if cgst == 0 else d("0")
            total = amount if not force_mismatch else amount + d(random.choice([150, 320, 500]))

            invoice = Invoice.objects.create(
                invoice_number=invoice_number or next_number(),
                vendor=vendor_obj,
                vendor_name_raw=vendor_obj.name,
                purchase_order=po,
                po_number_raw=po.po_number if po else "",
                gstin=gstin_override if gstin_override is not None else vendor_obj.gstin,
                invoice_date=invoice_date,
                due_date=invoice_date + timedelta(days=vendor_obj.payment_terms_days),
                currency="INR",
                subtotal=subtotal,
                tax_amount=tax,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                discount=d("0"),
                total_amount=total,
                payment_terms=f"Net {vendor_obj.payment_terms_days}",
                department=random.choice(DEPARTMENTS),
                status=status,
                ocr_provider="tesseract",
                ocr_confidence=confidence,
                ocr_confidence_level=self._confidence_level(confidence),
                uploaded_by=users[Role.AP_PROCESSOR],
            )
            if mirror_po and po:
                for po_line in po.line_items.all():
                    InvoiceLineItem.objects.create(
                        invoice=invoice,
                        line_no=po_line.line_no,
                        description=po_line.description,
                        quantity=po_line.quantity,
                        unit_price=po_line.unit_price,
                        tax_amount=po_line.tax_amount,
                        amount=po_line.amount,
                    )
            else:
                self._add_line_items(invoice, subtotal)
            self._extract_fields(invoice, confidence)
            created.append(invoice)
            return invoice

        # --- 1) Clean approved & paid invoices tied to POs (aged across buckets) ---
        for i, vendor in enumerate(active_vendors):
            vendor_pos = [p for p in pos if p.vendor_id == vendor.id]
            po = random.choice(vendor_pos) if vendor_pos else None
            days_ago = [10, 40, 70, 100, 135][i % 5]
            amount = d(random.choice([18000, 42000, 68000, 125000, 320000, 610000]))
            invoice = make_invoice(
                vendor, po, days_ago, amount, InvoiceStatus.VALIDATED, random.randint(88, 99), mirror_po=bool(po)
            )
            if po:
                match_invoice_to_po(invoice)
            workflow = create_workflow(invoice, notify=False)
            steps = list(workflow.steps.order_by("step_number"))
            # Fully approve half of them, partially approve others
            fully = i % 2 == 0
            for step in steps:
                if step.assigned_user:
                    apply_action(step, step.assigned_user, "APPROVE", "Looks good, approved.")
                if not fully:
                    break
            invoice.refresh_from_db()

            if invoice.status == InvoiceStatus.APPROVED:
                pr = PaymentRequest.objects.create(
                    request_number=f"PREQ-2026-{i+1:04d}",
                    invoice=invoice,
                    vendor=vendor,
                    amount=invoice.total_amount,
                    currency="INR",
                    method=random.choice([PaymentMethod.BANK_TRANSFER, PaymentMethod.UPI]),
                    due_date=invoice.due_date,
                    status=PaymentStatus.PAYMENT_PENDING,
                    requested_by=users[Role.AP_MANAGER],
                )
                if days_ago > 30:  # simulate older ones being paid already
                    invoice.status = InvoiceStatus.PAID
                    invoice.save(update_fields=["status"])
                    pr.status = PaymentStatus.PAID
                    pr.save(update_fields=["status"])
                    payment = Payment.objects.create(
                        payment_request=pr,
                        transaction_ref=f"TXN{random.randint(100000,999999)}",
                        payment_date=timezone.now() - timedelta(days=max(days_ago - 20, 1)),
                        status=PaymentStatus.PAID,
                        bank_response={"simulated": True, "gateway": "MockBank (Simulated)", "message": "Payment settled successfully (simulated -- no real funds were moved)."},
                        processed_by=users[Role.FINANCE_MANAGER],
                    )
                    generate_payment_advice(payment)
                else:
                    invoice.status = InvoiceStatus.PAYMENT_PENDING
                    invoice.save(update_fields=["status"])

        # --- 2) Pending approval invoices across all matrix bands ---
        for amount, vendor in zip([28000, 145000, 610000, 45000, 380000], active_vendors):
            po = next((p for p in pos if p.vendor_id == vendor.id), None)
            invoice = make_invoice(vendor, po, random.randint(1, 15), d(amount), InvoiceStatus.VALIDATED, random.randint(85, 97))
            create_workflow(invoice)

        # --- 3) Duplicate suspected invoices ---
        for vendor in active_vendors[:3]:
            shared_number = f"INV-DUP-{vendor.code}"
            amount = d(random.choice([32000, 58000]))
            first = make_invoice(vendor, None, 25, amount, InvoiceStatus.EXCEPTION, random.randint(80, 95), invoice_number=shared_number)
            second = make_invoice(vendor, None, 23, amount, InvoiceStatus.EXCEPTION, random.randint(80, 95), invoice_number=shared_number + "-B")
            for inv, other in ((first, second), (second, first)):
                InvoiceException.objects.create(
                    invoice=inv,
                    exception_type=ExceptionType.DUPLICATE_INVOICE,
                    severity=ExceptionSeverity.HIGH,
                    description=(
                        f"Duplicate suspected: same vendor ({vendor.name}), amount ₹{amount}, "
                        f"and invoice date within 2 days of invoice {other.invoice_number}."
                    ),
                    status=ExceptionStatus.OPEN,
                    assigned_to=users[Role.AP_PROCESSOR],
                )

        # --- 4) Amount mismatch invoices ---
        for vendor in active_vendors[3:6]:
            amount = d(random.choice([21000, 54000, 89000]))
            invoice = make_invoice(vendor, None, random.randint(2, 20), amount, InvoiceStatus.EXCEPTION, random.randint(82, 96), force_mismatch=True)
            InvoiceException.objects.create(
                invoice=invoice,
                exception_type=ExceptionType.AMOUNT_MISMATCH,
                severity=ExceptionSeverity.MEDIUM,
                description="Subtotal + tax − discount does not equal the extracted total amount.",
                status=ExceptionStatus.OPEN,
                assigned_to=users[Role.AP_PROCESSOR],
            )

        # --- 5) Missing PO invoices ---
        for vendor in active_vendors[:3]:
            amount = d(random.choice([15000, 47000, 250000]))
            invoice = make_invoice(vendor, None, random.randint(2, 25), amount, InvoiceStatus.EXCEPTION, random.randint(85, 96))
            InvoiceException.objects.create(
                invoice=invoice,
                exception_type=ExceptionType.MISSING_PO,
                severity=ExceptionSeverity.LOW,
                description="No matching purchase order number was found for this invoice.",
                status=ExceptionStatus.OPEN,
                assigned_to=users[Role.AP_PROCESSOR],
            )

        # --- 6) Low OCR confidence invoices ---
        for vendor in active_vendors[4:7]:
            amount = d(random.choice([9800, 26000, 61000]))
            invoice = make_invoice(vendor, None, random.randint(1, 10), amount, InvoiceStatus.EXCEPTION, random.randint(35, 55))
            InvoiceException.objects.create(
                invoice=invoice,
                exception_type=ExceptionType.OCR_LOW_CONFIDENCE,
                severity=ExceptionSeverity.MEDIUM,
                description="Overall OCR confidence fell below the 60% acceptance threshold; manual review required.",
                status=ExceptionStatus.OPEN,
                assigned_to=users[Role.AP_PROCESSOR],
            )

        # --- 7) Invalid GSTIN exception ---
        vendor = active_vendors[7]
        invoice = make_invoice(vendor, None, 6, d(37000), InvoiceStatus.EXCEPTION, 90, gstin_override="INVALIDGSTIN123")
        InvoiceException.objects.create(
            invoice=invoice,
            exception_type=ExceptionType.INVALID_GSTIN,
            severity=ExceptionSeverity.HIGH,
            description="Extracted GSTIN does not match the standard 15-character GSTIN format.",
            status=ExceptionStatus.OPEN,
            assigned_to=users[Role.AP_PROCESSOR],
        )

        # --- 8) Rejected invoices ---
        for vendor in active_vendors[:2]:
            po = next((p for p in pos if p.vendor_id == vendor.id), None)
            invoice = make_invoice(vendor, po, random.randint(5, 30), d(random.choice([64000, 210000])), InvoiceStatus.VALIDATED, random.randint(88, 98))
            workflow = create_workflow(invoice)
            first_step = workflow.steps.order_by("step_number").first()
            if first_step.assigned_user:
                apply_action(first_step, first_step.assigned_user, "REJECT", "Rate does not match the agreed vendor contract.")

        # --- 9) A few fresh uploads still mid-pipeline ---
        for vendor in active_vendors[:2]:
            make_invoice(vendor, None, random.randint(0, 2), d(random.choice([12000, 33000])), InvoiceStatus.PROCESSING, 0)

        for inv in created:
            log_action(
                action="UPLOAD",
                entity_type="Invoice",
                entity_id=inv.id,
                description=f"Invoice {inv.invoice_number} uploaded (seed data)",
                user=users[Role.AP_PROCESSOR],
            )
            if inv.ocr_confidence:
                log_action(
                    action="OCR_PROCESS",
                    entity_type="Invoice",
                    entity_id=inv.id,
                    description=f"OCR extraction completed at {inv.ocr_confidence:.0f}% confidence",
                    user=users[Role.AP_PROCESSOR],
                )

        for exc in InvoiceException.objects.all():
            notify_user(
                exc.assigned_to,
                "EXCEPTION_RAISED",
                f"Exception ({exc.get_exception_type_display()}) raised on invoice {exc.invoice.invoice_number}.",
                link=f"/invoices/{exc.invoice_id}",
            )

        self.stdout.write(f"Invoices created: {len(created)}")
