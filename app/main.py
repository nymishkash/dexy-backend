from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from .scraper import WellFoundScraper
from .db import JobsDB
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your React app URL here (default Vite port)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods including OPTIONS
    allow_headers=["*"],
)

db = JobsDB()

class JobSearchParams(BaseModel):
    location: Optional[str] = None 
    role: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None

@app.post("/jobs/search")
async def search_jobs(params: JobSearchParams):
    try:
        if params.location and params.role:
            jobs = await db.get_jobs_by_location_and_role(params.location, params.role)
            logger.info(f"Fetching jobs for location {params.location} and role {params.role}")
        elif params.location:
            jobs = await db.get_jobs_by_location(params.location)
            logger.info(f"Fetching jobs for location {params.location}")
        elif params.role:
            jobs = await db.get_jobs_by_role(params.role)
            logger.info(f"Fetching jobs for role {params.role}")
        else:
            jobs = await db.get_all_jobs()
            logger.info("Fetching all jobs")

        # Sort jobs if sort parameter is provided
        if params.sort:
            if params.sort == "date":
                jobs.sort(key=lambda x: x["request_time"], reverse=True)
            elif params.sort == "company":
                jobs.sort(key=lambda x: x["company"])
            elif params.sort == "title":
                jobs.sort(key=lambda x: x["title"])

        # Limit results if limit parameter is provided
        if params.limit and isinstance(params.limit, int) and params.limit > 0:
            jobs = jobs[:params.limit]

        return JSONResponse(content={"jobs": jobs}, status_code=200)

    except Exception as e:
        logger.error(f"Failed to fetch jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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