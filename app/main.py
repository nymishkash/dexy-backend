from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from .scraper import WellFoundScraper
from .db import JobsDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
db = JobsDB()

@app.get("/jobs/all")
async def get_all_jobs():
    try:
        jobs = await db.get_all_jobs()
        return JSONResponse(content={"jobs": jobs}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/location/{location}")
async def get_jobs_by_location(location: str):
    try:
        jobs = await db.get_jobs_by_location(location)
        return JSONResponse(content={"jobs": jobs}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to fetch jobs for location {location}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/role/{role}")
async def get_jobs_by_role(role: str):
    try:
        jobs = await db.get_jobs_by_role(role)
        return JSONResponse(content={"jobs": jobs}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to fetch jobs for role {role}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/location/{location}/role/{role}")
async def get_jobs_by_location_and_role(location: str, role: str):
    try:
        jobs = await db.get_jobs_by_location_and_role(location, role)
        return JSONResponse(content={"jobs": jobs}, status_code=200)
    except Exception as e:
        logger.error(f"Failed to fetch jobs for location {location} and role {role}: {str(e)}")
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