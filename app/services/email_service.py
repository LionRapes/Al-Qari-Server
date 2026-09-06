"""Email service implementation for sending magic link authentication notifications[cite: 9]."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import MAIL_SETTINGS

EMAIL_TRANSLATIONS = {
    "ru": {
        "subject": "Вход в приложение Al-Qari",
        "body": """Здравствуйте!

Для входа в аккаунт нажмите на ссылку ниже:
{magic_link}

Ссылка действительна 15 минут. Если вы не запрашивали вход, просто проигнорируйте это письмо.""",
    },
    "en": {
        "subject": "Login to Al-Qari",
        "body": """Hello!

Click the link below to log into your account:
{magic_link}

The link is valid for 15 minutes. If you did not request this login, please ignore this email.""",
    },
}


class EmailService:
    """Service for sending emails, including magic link authentication notifications[cite: 9]."""

    @staticmethod
    def send_magic_link_email(to_email: str, token: str, lang: str = "en") -> None:
        """Send an authentication magic link email to the user in their preferred language[cite: 9]."""
        magic_link = f"{MAIL_SETTINGS.FRONTEND_BASE_URL}/auth/verify?token={token}"

        t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])

        msg = MIMEMultipart()
        msg["From"] = MAIL_SETTINGS.SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = t["subject"]

        body = t["body"].format(magic_link=magic_link)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP_SSL(MAIL_SETTINGS.SMTP_HOST, MAIL_SETTINGS.SMTP_PORT) as server:
                server.login(MAIL_SETTINGS.SMTP_USER, MAIL_SETTINGS.SMTP_PASSWORD)
                server.sendmail(MAIL_SETTINGS.SMTP_USER, to_email, msg.as_string())
        except smtplib.SMTPException as e:
            print(e)
