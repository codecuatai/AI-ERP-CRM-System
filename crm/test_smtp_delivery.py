"""Actual SMTP transport checks on loopback; no external recipient is contacted."""

from contextlib import contextmanager
from email import policy
from email.parser import BytesParser
from queue import Queue
import socketserver
import threading

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crm.models import Customer, Interaction, LeadFollowUp, LeadRequest


class LocalSMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(5)
        self.wfile.write(b"220 isolated-test SMTP\r\n")
        while line := self.rfile.readline(65536):
            command = line.split(b" ", 1)[0].strip().upper()
            if command in (b"EHLO", b"HELO"):
                self.wfile.write(b"250 isolated-test\r\n")
            elif command == b"RCPT" and self.server.reject_recipient:
                self.wfile.write(b"550 Recipient rejected by isolated test\r\n")
            elif command in (b"MAIL", b"RCPT", b"RSET", b"NOOP"):
                self.wfile.write(b"250 OK\r\n")
            elif command == b"DATA":
                self.wfile.write(b"354 End with dot\r\n")
                body = []
                while data := self.rfile.readline(65536):
                    if data == b".\r\n":
                        break
                    body.append(data[1:] if data.startswith(b"..") else data)
                self.server.messages.put(b"".join(body))
                self.wfile.write(b"250 Accepted\r\n")
            elif command == b"QUIT":
                self.wfile.write(b"221 Bye\r\n")
                return
            else:
                self.wfile.write(b"502 Unsupported in isolated test\r\n")


@contextmanager
def local_smtp(reject_recipient=False):
    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), LocalSMTPHandler) as server:
        server.daemon_threads = True
        server.reject_recipient = reject_recipient
        server.messages = Queue()
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


class LocalSMTPDeliveryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("smtp-test", password="test-only")
        self.customer = Customer.objects.create(full_name="Khách minh họa SMTP", email="smtp@consultation.test")
        self.lead = LeadRequest.objects.create(customer=self.customer, request_text="Cần tư vấn CRM")
        self.client.force_login(self.user)

    def send(self, server):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend", EMAIL_HOST="127.0.0.1",
                           EMAIL_PORT=server.server_address[1], EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="",
                           EMAIL_USE_TLS=False, EMAIL_USE_SSL=False, EMAIL_TIMEOUT=5,
                           DEFAULT_FROM_EMAIL="DigiFlow <no-reply@consultation.test>", PUBLIC_SITE_URL="https://crm.example.test"):
            return self.client.post(reverse("crm:lead_follow_up", args=[self.lead.pk]),
                                    {"question_text": "Anh/chị cần hỗ trợ quy trình nào?"})

    def test_follow_up_sends_multipart_over_actual_local_socket(self):
        with local_smtp() as server:
            self.assertEqual(self.send(server).status_code, 302)
            message = BytesParser(policy=policy.default).parsebytes(server.messages.get(timeout=3))
        self.assertEqual(str(message["To"]), self.customer.email)
        self.assertTrue(message.is_multipart())
        body = message.get_body(preferencelist=("plain",)).get_content()
        self.assertIn("Anh/chị cần hỗ trợ", body)
        self.assertRegex(body, r"https://crm.example.test/crm/bo-sung-thong-tin/[A-Za-z0-9_-]{43}/")
        self.assertEqual(LeadFollowUp.objects.get().status, "SENT")
        self.assertEqual(Interaction.objects.filter(kind="EMAIL").count(), 1)

    def test_actual_smtp_rejection_never_creates_sent_activity_or_live_token(self):
        with local_smtp(reject_recipient=True) as server, self.assertLogs("crm.views", level="ERROR"):
            self.assertEqual(self.send(server).status_code, 302)
            self.assertTrue(server.messages.empty())
        follow_up = LeadFollowUp.objects.get()
        self.assertEqual(follow_up.status, "FAILED")
        self.assertEqual(follow_up.token_hash, "")
        self.assertFalse(Interaction.objects.exists())
