from typing import Optional, List
from smtplib import SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPNotSupportedError
from requests.exceptions import RequestException, RetryError, Timeout

from core.entities import Mail
from core.interface import ApiInterface, SmtpInterface
from infrastructure.logger import get_logger

logger = get_logger("core.services.mail_service", "logs/core.log")

class MailService:
    def __init__(self, service_protocol: Optional[List[ApiInterface | SmtpInterface]]):
        self.service_protocol = service_protocol
        self.raise_exception = False
    
    def send_mail(self, mail: Mail) -> bool:
        """
        Sends an email using the first available protocol.
        
        Args:
            mail (Mail): The email to send.
            
        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        try:
            for protocol in self.service_protocol:
                try:
                    if isinstance(protocol, SmtpInterface):
                        self.raise_exception = False
                        return protocol.send_mail(mail)
                    elif isinstance(protocol, ApiInterface):
                        self.raise_exception = False
                        return protocol.call(mail)
                except (SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPNotSupportedError) as e:
                    logger.warning(f"An exception was raised while using the {protocol.__class__.__name__} protocol. Switching to alternate protocol.",
                                   extra={
                                       "error": e,
                                       "protocol": protocol.__class__.__name__,
                                   })
                    self.raise_exception = True
                    continue
                except (RequestException, RetryError, Timeout) as e:
                    logger.warning(f"An exception was raised while using the {protocol.__class__.__name__} protocol. Switching to alternate protocol.",
                                extra={
                                    "error": e,
                                    "protocol": protocol.__class__.__name__,
                                })
                    self.raise_exception = True
                    continue
                finally:
                    if self.raise_exception:
                        raise Exception
        except Exception as e:
            logger.critical(f"The available service protocol/s are not working. Please check the configuration.",
                            extra={
                                "error": e,
                                "service_protocols": [protocol.__class__.__name__ for protocol in self.service_protocol],
                            })
            return False
