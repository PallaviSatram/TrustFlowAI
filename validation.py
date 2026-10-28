from typing import Literal
from pydantic import BaseModel, ValidationError, field_validator

class RequestResult(BaseModel): # validation model
  action: Literal["list_failed_builds", "unknown"]
  service: Literal["payment-service", "user-service"] | None = None

  @field_validator("service", mode="before")
  @classmethod
  def normalize_service(cls, value):
    if value is None:
      return None

    aliases = {
      "payment": "payment-service",
      "user": "user-service",
    }

    if isinstance(value, str):
      value = value.strip().lower()
      return aliases.get(value, value)
    
    return value
  
# Test data — no Gemini request required
if __name__ == "__main__":
  test_cases = [
      {
          "action": "list_failed_builds",
          "service": "payment",
      },
      {
          "action": "list_failed_builds",
          "service": "user-service",
      },
      {
          "action": "unknown",
          "service": None,
      },
      {
        "action": "list_failed_builds",
        "service": "customer-service"
      },
      {
        "action": "list_sucess_builds",
        "service": "customer-service"
      }
  ]

  for data in test_cases:
    try:
      result = RequestResult.model_validate(data)
      print("VALID:", result.model_dump())
    except ValidationError as error:
      print("INVALID:", error)
