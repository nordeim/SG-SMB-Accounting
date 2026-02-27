"""
Asynchronous tasks for Invoicing module.
"""

import logging
from uuid import UUID
from celery import shared_task

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from apps.core.models import Organisation, InvoiceDocument, Contact
from apps.invoicing.services import DocumentService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_invoice_email_task(self, org_id: str, document_id: str, recipients: list):
    """
    Background task to generate PDF and send invoice via email.
    """
    try:
        org = Organisation.objects.get(id=org_id)
        document = InvoiceDocument.objects.get(id=document_id, org_id=org_id)
        contact = document.contact
        
        context = {
            "org_name": org.name,
            "contact_name": contact.name,
            "document_number": document.sequence_number,
            "total_amount": document.total_incl,
            "currency": org.base_currency,
            "due_date": document.due_date,
        }
        
        subject = f"Invoice {document.sequence_number} from {org.name}"
        text_content = render_to_string("invoicing/email/invoice_email.txt", context)
        html_content = render_to_string("invoicing/email/invoice_email.html", context)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_content, "text/html")
        
        # Attach PDF
        pdf_stream = DocumentService.generate_pdf(UUID(org_id), UUID(document_id))
        email.attach(
            f"{document.sequence_number}.pdf",
            pdf_stream.getvalue(),
            "application/pdf"
        )
        
        email.send()
        logger.info(f"Successfully sent invoice {document_id} to {recipients}")
        
        return {"status": "sent", "document_id": document_id}
        
    except Exception as exc:
        logger.error(f"Error sending invoice email {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
