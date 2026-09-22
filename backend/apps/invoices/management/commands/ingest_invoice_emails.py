"""Poll an IMAP inbox for unread emails with invoice attachments and feed
each attachment through the same pipeline as a manual upload.

This app has no background task queue (see README's "Known Limitations") --
consistent with that, this command is meant to be run periodically by an
external scheduler (cron, Windows Task Scheduler, or just by hand) rather
than as a long-running daemon:

    python manage.py ingest_invoice_emails

Configure the mailbox via environment variables (see .env.example):
    EMAIL_INGEST_HOST, EMAIL_INGEST_PORT, EMAIL_INGEST_USER,
    EMAIL_INGEST_PASSWORD, EMAIL_INGEST_FOLDER, EMAIL_INGEST_DEPARTMENT
"""

import email
import imaplib
import os
from email.header import decode_header

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

from apps.invoices.services import ingest_invoice_file
from apps.invoices.uploads import ALLOWED_EXTENSIONS


def _decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        chunk.decode(enc or "utf-8", errors="replace") if isinstance(chunk, bytes) else chunk
        for chunk, enc in parts
    )


class Command(BaseCommand):
    help = "Ingest invoice attachments from an unread-email IMAP inbox, running each through the OCR pipeline."

    def handle(self, *args, **options):
        host = settings.EMAIL_INGEST_HOST
        user = settings.EMAIL_INGEST_USER
        password = settings.EMAIL_INGEST_PASSWORD

        if not host or not user or not password:
            raise CommandError(
                "EMAIL_INGEST_HOST, EMAIL_INGEST_USER and EMAIL_INGEST_PASSWORD must all be set in .env "
                "before this command can run. See the 'Email ingestion' section of .env.example."
            )

        self.stdout.write(f"Connecting to {host}:{settings.EMAIL_INGEST_PORT} as {user}...")
        connection = imaplib.IMAP4_SSL(host, settings.EMAIL_INGEST_PORT)
        try:
            connection.login(user, password)
            connection.select(settings.EMAIL_INGEST_FOLDER)

            status, data = connection.search(None, "UNSEEN")
            if status != "OK":
                raise CommandError(f"IMAP SEARCH failed: {status}")

            message_ids = data[0].split()
            self.stdout.write(f"Found {len(message_ids)} unread email(s).")

            invoices_created = 0
            emails_with_no_attachment = 0

            for msg_id in message_ids:
                status, msg_data = connection.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    self.stderr.write(f"Could not fetch message {msg_id}: {status}")
                    continue

                message = email.message_from_bytes(msg_data[0][1])
                sender = _decode(message.get("From", "unknown sender"))
                subject = _decode(message.get("Subject", "(no subject)"))

                attachments_found = 0
                for part in message.walk():
                    disposition = part.get("Content-Disposition", "")
                    if not disposition.lower().startswith("attachment"):
                        continue
                    filename = _decode(part.get_filename())
                    if not filename:
                        continue
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        self.stdout.write(f"  Skipping '{filename}' from {sender} -- unsupported file type {ext}.")
                        continue

                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue

                    uploaded_file = SimpleUploadedFile(filename, payload)
                    invoice = ingest_invoice_file(
                        uploaded_file,
                        department=settings.EMAIL_INGEST_DEPARTMENT,
                        uploaded_by=None,
                        source=f"Email from {sender} (subject: {subject})",
                    )
                    attachments_found += 1
                    invoices_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  Created invoice {invoice.id} from '{filename}' (sender: {sender})")
                    )

                if attachments_found == 0:
                    emails_with_no_attachment += 1
                    self.stdout.write(f"  No usable attachments in email from {sender} (subject: {subject}).")

                # Mark handled either way so re-runs don't reprocess it.
                connection.store(msg_id, "+FLAGS", "\\Seen")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. {invoices_created} invoice(s) created, "
                    f"{emails_with_no_attachment} email(s) had no usable attachment."
                )
            )
        finally:
            try:
                connection.logout()
            except Exception:
                pass
