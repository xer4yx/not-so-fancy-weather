from pydantic import BaseModel, Field


class Mail(BaseModel):
    subject: str = Field(..., description="The subject of the email")
    body: str = Field(..., description="The body of the email")
    to: str = Field(..., description="The email address of the recipient")
    from_email: str = Field(..., alias="from", serialization_alias="from", description="The email address of the sender")
