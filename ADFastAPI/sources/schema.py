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