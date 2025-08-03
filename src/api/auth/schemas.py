from pydantic import BaseModel


class BearerResponseSchema(BaseModel):
    access_token: str
    token_type: str = "Bearer"
