from pydantic import BaseModel, EmailStr


class BearerResponseSchema(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class UserForgotPwdSchema(BaseModel):
    username: str
    email: EmailStr
