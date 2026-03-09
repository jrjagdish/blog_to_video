from app.utils.text_cleaner import sanitize_text
from fastapi import APIRouter, HTTPException
from app.schemas.video_schema import VideoRequest, VideoResponse, VideoJobResponse
from bs4 import BeautifulSoup
import requests

router = APIRouter()


@router.post("/generate-video")
async def generate_video(request: VideoRequest):
    if request.url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            }
            response = requests.get(request.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            for element in soup(
                ["script", "style", "nav", "footer", "header", "aside", "form"]
            ):
                element.decompose()
            result = await sanitize_text(soup.get_text())    
            title = soup.title.string if soup.title else "No Title"
            description = request.description
            return {"data": result, "title": title, "description": description}
        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
