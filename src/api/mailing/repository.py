from email.message import EmailMessage
from typing import Protocol, Annotated

import aiosmtplib
from fastapi import Depends

from core import settings, broker


class EmailRepositoryProtocol(Protocol):

    @staticmethod
    @broker.task(task_name="send_email")
    async def send_email(recipient: str, subject: str, body: str) -> None:
        pass

    @staticmethod
    @broker.task(task_name="send_verification_email")
    async def send_verification_email(recipient: str, token: str, user_id: int) -> None:
        pass


class EmailRepositoryImpl:

    @staticmethod
    @broker.task(task_name="send_email")
    async def send_email(recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = settings.mail.admin_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body, subtype="html")

        await aiosmtplib.send(
            message,
            sender=settings.mail.admin_email,
            recipients=recipient,
            hostname=settings.mail.host,
            port=settings.mail.port,
        )

    @staticmethod
    @broker.task(task_name="send_verification_email")
    async def send_verification_email(recipient: str, token: str, user_id: int) -> None:
        url = f"http://{settings.run.host}:{settings.run.port}/api/auth/reset-password?token={token}&user_id={user_id}"

        body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Восстановление пароля</title>
            </head>
            <body>
                <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <p>Мы получили ваш запрос на восстановление пароля.</p>
                    <p>Для восстановления пароля перейдите по ссылке: 
                       <a href="{url}">Восстановить пароль</a>
                    </p>
                    <p>Ссылка действительна в течение 1 часа.</p>
                    <br>
                    <p>Если вы не запрашивали восстановление пароля, 
                       проигнорируйте это письмо.</p>
                </div>
            </body>
            </html>
            """

        message = EmailMessage()
        message["From"] = settings.mail.admin_email
        message["To"] = recipient
        message["Subject"] = "Восстановление пароля"

        message.add_header("Content-Type", "text/html; charset=utf-8")
        message.set_payload(body, "utf-8")

        await aiosmtplib.send(
            message,
            sender=settings.mail.admin_email,
            recipients=recipient,
            hostname=settings.mail.host,
            port=settings.mail.port,
        )


def get_email_repository() -> EmailRepositoryProtocol:
    return EmailRepositoryImpl()


EmailRepositoryDep = Annotated[EmailRepositoryProtocol, Depends(get_email_repository)]
