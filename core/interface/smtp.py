from core.entities import Mail

class SmtpInterface:
    def send_mail(self, mail: Mail) -> bool:
        pass
