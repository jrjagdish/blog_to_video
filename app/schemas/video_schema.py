from pydantic import BaseModel, HttpUrl, model_validator
from typing import Optional


class VideoRequest(BaseModel):
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    description: str

    @model_validator(mode="after")
    def check_point(self):
        if not self.url and not self.text:
            raise ValueError("Either url or text must be provided")
        return self

    

class VideoResponse(BaseModel):
    video_url: str

class VideoJobResponse(BaseModel):
    job_id: str
    status: str        