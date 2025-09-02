import json
import os
from typing import Optional
from celery import Celery
from celery.result import AsyncResult
from config import REDIS_URL
from agents import create_code_review_crew

# Initialize Celery
celery_app = Celery('code_review_worker')

celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True
)

@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: Optional[str] = None):

    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting analysis...'})
        
        # Create and run the CrewAI crew
        review_crew = create_code_review_crew(repo_url, pr_number)
        
        self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100, 'status': 'Running CrewAI analysis...'})
        
        result = review_crew.kickoff()
        
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Processing results...'})
        
        
        result_text = ""
        
        
        if hasattr(result, 'raw'):
            result_text = result.raw
        elif isinstance(result, str):
            result_text = result
        else:
            result_text = str(result)
        
        
        result_text = result_text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:]  
        if result_text.startswith('```'):
            result_text = result_text[3:]   
        if result_text.endswith('```'):
            result_text = result_text[:-3]  
        
        result_text = result_text.strip()
        
        
        try:
            parsed_result = json.loads(result_text)
            return parsed_result
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            print(f"Raw result text: {result_text[:500]}...")
            
            
            return {
                "files": [],
                "summary": {
                    "total_files": 0,
                    "total_issues": 0,
                    "critical_issues": 0
                },
                "error": f"Failed to parse AI response as JSON: {str(json_error)}",
                "raw_response": result_text[:2000]  # Include first 1000 chars of response
            }
            
    except Exception as e:
        
        error_msg = f"Task failed for PR {repo_url}#{pr_number}: {str(e)}"
        print(error_msg)
        
        
        return {
            "files": [],
            "summary": {
                "total_files": 0,
                "total_issues": 0,
                "critical_issues": 0
            },
            "error": error_msg,
            "exception_type": type(e).__name__
        }

def get_task_status(task_id: str):
    
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        result = None
        if task_result.state == 'SUCCESS':
            result = task_result.get()
        elif task_result.state == 'FAILURE':
            # Access the exception information
            result = str(task_result.info)

        return {
            "task_id": task_id,
            "status": task_result.state,
            "result": result
        }
    except Exception as e:
        print(f"Error getting task status for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "ERROR",
            "result": f"Error retrieving task status: {str(e)}"
        }