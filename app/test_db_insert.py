import asyncio
from db import JobsDB

async def test_insert():
    # Create an instance of JobsDB
    db = JobsDB()

    # Define a dummy job data
    dummy_job = {
        'id': 'test-job-123',
        'title': 'Test Job Title',
        'company': 'Test Company',
        'company_logo': 'https://example.com/logo.png',
        'location': ['Remote', 'USA'],
        'compensation': '100k-120k',
        'remote': True,
        'slug': 'test-job-title',
        'raw_data': {'description': 'This is a test job description'}
    }

    # Try to save the dummy job
    try:
        saved = await db.save_job(dummy_job)
        if saved:
            print("Dummy job inserted successfully.")
        else:
            print("Dummy job already exists or failed to insert.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await db.close()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_insert()) 