# db.py
from typing import List, Dict, Any
import os
from libsql_client import create_client
import logging
from dotenv import load_dotenv
import asyncio

class JobsDB:
    def __init__(self):
        self.logger = logging.getLogger("JobsDB")
        
        load_dotenv()
        
        db_url = os.getenv("DB_URL")
        db_token = os.getenv("DB_TOKEN")
        
        if not db_url:
            raise ValueError("DB_URL not found in environment variables")
        if not db_token:
            raise ValueError("DB_TOKEN not found in environment variables")
            
        if not db_url.startswith(('libsql://', 'https://')):
            raise ValueError("DB_URL must start with 'libsql://' or 'https://'")
            
        self.logger.info(f"Connecting to database at {db_url}")
        
        try:
            self.client = create_client(
                url=db_url,
                auth_token=db_token
            )
            self.logger.info("Client created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create client: {str(e)}")
            raise
        
        asyncio.create_task(self._init_db())

    async def _init_db(self):
        """Initialize the Jobs table if it doesn't exist"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS Jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                company_logo TEXT,
                location TEXT,
                compensation TEXT,
                remote BOOLEAN,
                slug TEXT,
                raw_data TEXT,
                request_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await self.client.execute(create_table_sql)
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def close(self):
        """Close the database connection"""
        if self.client:
            await self.client.close()
            self.logger.info("Database connection closed")

    async def job_exists(self, job_id: str) -> bool:
        """Check if a job already exists in the database"""
        try:
            result = await self.client.execute("SELECT 1 FROM Jobs WHERE id = ?", [job_id])
            return len(result.rows) > 0
        except Exception as e:
            self.logger.error(f"Error checking job existence: {str(e)}")
            return False

    async def save_job(self, job: Dict[str, Any]) -> bool:
        """Save a single job to the database"""
        try:
            if await self.job_exists(job['id']):
                self.logger.info(f"Job {job['id']} already exists, skipping")
                return False

            # Convert location list to string
            location_str = ', '.join(job['location']) if job['location'] else ''
            
            # Convert raw_data to string
            raw_data_str = str(job['raw_data'])

            insert_sql = """
            INSERT INTO Jobs (
                id, title, company, company_logo, location, 
                compensation, remote, slug, raw_data, request_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.client.execute(
                insert_sql,
                [
                    job['id'],
                    job['title'],
                    job['company'],
                    job['company_logo'],
                    location_str,
                    job['compensation'],
                    1 if job['remote'] else 0,
                    job['slug'],
                    raw_data_str,
                    job['request_time']
                ]
            )
            
            self.logger.info(f"Successfully saved job {job['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save job {job['id']}: {str(e)}")
            return False

    async def save_jobs(self, jobs: List[Dict[str, Any]]) -> tuple[int, int]:
        """Save multiple jobs to the database"""
        saved_count = 0
        skipped_count = 0
        
        for job in jobs:
            if await self.save_job(job):
                saved_count += 1
            else:
                skipped_count += 1
                
        return saved_count, skipped_count