from pydantic import BaseModel

class DefaultResponse(BaseModel):
    is_success: bool = True
    message: str = ''
    response: BaseModel | None = None
    
    def success(self, response: BaseModel | None = None):
        self.response = response
    
    def fail(self, message: str):
        self.is_success = False
        self.message = message

class BoundingBox(BaseModel):
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0