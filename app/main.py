from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from .scraper import WellFoundScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/scrape")
async def trigger_scrape():
    try:
        logger.info("Starting scrape process")
        
        scraper = await WellFoundScraper.create()
        
        jobs = await scraper.scrape_jobs()
        
        if jobs is None:
            raise HTTPException(
                status_code=500,
                detail="Scraping failed - no data retrieved"
            )
            
        return JSONResponse(
            content={
                "status": "scrape successful",
                "jobs_count": len(jobs)
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Scraping failed with error: {str(e)}")
        raise HTTPException(
            status_code=500,
            content={
                "status": "scrape failed",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)