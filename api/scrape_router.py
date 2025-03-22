from schemas.scrap_schema import ScrapingRequest, ScrapingResponse
from fastapi import APIRouter, HTTPException
from services.scrape_service import ScrapeService

router = APIRouter()

@router.post("/scrape", response_model=ScrapingResponse)
async def scrape_url(request: ScrapingRequest):
    """
    Scrape a URL with specified depth level.
    
    - Level 1: Scrape only the provided URL
    - Level 2: Scrape the provided URL and its important linked pages
    """
    request.depth = 1
    # if request.depth < 1 or request.depth > 2:
    #     raise HTTPException(status_code=400, detail="Depth must be 1 or 2")
    
    return await ScrapeService.scrape_url_with_depth(str(request.url), request.depth)