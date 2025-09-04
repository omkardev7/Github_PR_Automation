import json
from celery import Celery
from celery.result import AsyncResult
from pydantic import ValidationError

from config import REDIS_URL
from agents import create_code_review_crew
from models import FinalReport
from logger_config import setup_logger, log_function_start, log_function_end, log_step


logger = setup_logger(__name__)

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


def clean_llm_output(text: str) -> str:
    
    log_function_start(logger, "clean_llm_output", text_length=len(text))
    
    try:
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        
        if text.endswith('```'):
            text = text[:-3]
            
        cleaned_text = text.strip()
        
        log_function_end(logger, "clean_llm_output", 
                        original_length=len(text), 
                        cleaned_length=len(cleaned_text))
        
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error cleaning LLM output: {e}")
        log_function_end(logger, "clean_llm_output", success=False, error=str(e))
        return text  # Return original text if cleaning fails


def parse_and_validate_result(raw_result: str) -> dict:
    
    log_function_start(logger, "parse_and_validate_result", result_length=len(raw_result))
    
    try:
        # Clean the raw output
        log_step(logger, "Cleaning LLM output")
        cleaned_result = clean_llm_output(raw_result)
        
        # Parse JSON
        log_step(logger, "Parsing JSON")
        try:
            parsed_json = json.loads(cleaned_result)
            log_step(logger, "JSON parsed successfully", keys=list(parsed_json.keys()) if isinstance(parsed_json, dict) else "not_dict")
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse AI response as JSON. Error: {e}"
            logger.error(error_message)
            log_function_end(logger, "parse_and_validate_result", success=False, error="JSON_DECODE_ERROR")
            return {
                "error": error_message,
                "raw_response": cleaned_result[:1000]  # Include snippet for debugging
            }

        # Validate with Pydantic
        log_step(logger, "Validating with Pydantic model")
        try:
            validated_report = FinalReport.model_validate(parsed_json)
            result = validated_report.model_dump()
            
            log_function_end(logger, "parse_and_validate_result", 
                            files_count=len(result.get('files', [])),
                            total_issues=result.get('summary', {}).get('total_issues', 0))
            
            return result
            
        except ValidationError as e:
            error_message = f"AI response failed Pydantic validation. Error: {e}"
            logger.error(error_message)
            log_function_end(logger, "parse_and_validate_result", success=False, error="VALIDATION_ERROR")
            return {
                "error": error_message,
                "raw_response": parsed_json
            }
            
    except Exception as e:
        error_message = f"Unexpected error during parsing and validation: {e}"
        logger.error(error_message)
        log_function_end(logger, "parse_and_validate_result", success=False, error="UNEXPECTED_ERROR")
        return {
            "error": error_message,
            "exception_type": type(e).__name__
        }


@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int):
    
    task_id = self.request.id
    log_function_start(logger, "analyze_pr_task", 
                      task_id=task_id, repo_url=repo_url, pr_number=pr_number)
    
    try:
        log_step(logger, "Updating task state to PROGRESS - Initializing")
        self.update_state(state='PROGRESS', meta={'status': 'Initializing multi-agent crew...'})
        
        log_step(logger, "Creating code review crew")
        review_crew = create_code_review_crew(repo_url, pr_number)
        
        log_step(logger, "Updating task state to PROGRESS - Running analysis")
        self.update_state(state='PROGRESS', meta={'status': 'Running specialized agent analysis...'})
        
        log_step(logger, "Executing CrewAI crew")
        result = review_crew.kickoff()
        
        log_step(logger, "Updating task state to PROGRESS - Validating")
        self.update_state(state='PROGRESS', meta={'status': 'Validating final report...'})
        
        log_step(logger, "Processing crew result")
        final_result = parse_and_validate_result(result.raw)
        
        if 'error' in final_result:
            log_function_end(logger, "analyze_pr_task", success=False, 
                           error_type=final_result.get('error', 'Unknown'))
            return final_result
        
        log_function_end(logger, "analyze_pr_task", 
                        files_analyzed=len(final_result.get('files', [])),
                        total_issues=final_result.get('summary', {}).get('total_issues', 0))
        
        return final_result
        
    except Exception as e:
        error_msg = f"Task failed for PR {repo_url}#{pr_number}: {str(e)}"
        logger.error(error_msg)
        log_function_end(logger, "analyze_pr_task", success=False, 
                        error=error_msg, exception_type=type(e).__name__)
        
        return {
            "error": error_msg,
            "exception_type": type(e).__name__
        }


def get_task_status(task_id: str) -> dict:
    
    log_function_start(logger, "get_task_status", task_id=task_id)
    
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        result = None
        if task_result.state == 'SUCCESS':
            result = task_result.get()
            log_step(logger, "Task completed successfully")
        elif task_result.state == 'FAILURE':
            result = str(task_result.info)
            log_step(logger, "Task failed", error=result)
        elif task_result.state == 'PROGRESS':
            result = task_result.info  
            log_step(logger, "Task in progress", progress_info=result)
        else:
            log_step(logger, "Task in state", state=task_result.state)

        status_info = {
            "task_id": task_id,
            "status": task_result.state,
            "result": result
        }
        
        log_function_end(logger, "get_task_status", 
                        task_status=task_result.state,
                        has_result=bool(result))
        
        return status_info
        
    except Exception as e:
        error_msg = f"Error retrieving task status for {task_id}: {e}"
        logger.error(error_msg)
        log_function_end(logger, "get_task_status", success=False, error=error_msg)
        
        return {
            "task_id": task_id,
            "status": "ERROR",
            "result": error_msg
        }