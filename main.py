from fastapi import FastAPI, HTTPException, status
from models import AnalysisRequest, TaskStatusResponse, SuccessResultResponse, ErrorResponse
from worker import celery_app, get_task_status
from logger_config import setup_logger, log_function_start, log_function_end, log_step


logger = setup_logger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Autonomous Code Review Agent API",
    description="An API to trigger AI-powered code reviews for GitHub pull requests.",
    version="1.0.0"
)


def queue_analysis_task(repo_url: str, pr_number: int) -> dict:
    
    log_function_start(logger, "queue_analysis_task", repo_url=repo_url, pr_number=pr_number)
    
    try:
        log_step(logger, "Sending task to Celery")
        task = celery_app.send_task(
            'worker.analyze_pr_task',
            args=[repo_url, pr_number]
        )
        
        result = {"task_id": task.id, "status": "PENDING"}
        
        log_function_end(logger, "queue_analysis_task", task_id=task.id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to queue analysis task: {e}")
        log_function_end(logger, "queue_analysis_task", success=False, error=str(e))
        raise


def validate_analysis_request(request: AnalysisRequest) -> None:
    
    log_function_start(logger, "validate_analysis_request", 
                      repo_url=request.repo_url, pr_number=request.pr_number)
    
    try:
        # Basic validation
        if not request.repo_url or not request.repo_url.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository URL is required and cannot be empty"
            )
            
        if not request.repo_url.startswith("https://github.com/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository URL must be a valid GitHub URL"
            )
            
        if request.pr_number <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PR number must be a positive integer"
            )
            
        log_function_end(logger, "validate_analysis_request", validation_passed=True)
        
    except HTTPException:
        log_function_end(logger, "validate_analysis_request", success=False, error="Validation failed")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        log_function_end(logger, "validate_analysis_request", success=False, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal validation error"
        )


def format_success_response(task_id: str, result_data: dict) -> SuccessResultResponse:
    
    log_function_start(logger, "format_success_response", task_id=task_id)
    
    try:
        response = SuccessResultResponse(
            task_id=task_id, 
            status="COMPLETED", 
            results=result_data
        )
        
        log_function_end(logger, "format_success_response", 
                        files_count=len(result_data.get('files', [])))
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting success response: {e}")
        log_function_end(logger, "format_success_response", success=False, error=str(e))
        raise


def format_error_response(task_id: str, result_data: dict) -> dict:
    
    log_function_start(logger, "format_error_response", task_id=task_id)
    
    try:
        response = {
            "task_id": task_id,
            "status": "FAILED",
            "error": result_data['error'],
            "details": result_data.get('raw_response') or result_data.get('exception_type')
        }
        
        log_function_end(logger, "format_error_response", error_type=result_data.get('error', 'Unknown'))
        return response
        
    except Exception as e:
        logger.error(f"Error formatting error response: {e}")
        log_function_end(logger, "format_error_response", success=False, error=str(e))
        raise


@app.post("/analyze-pr", status_code=status.HTTP_202_ACCEPTED, response_model=TaskStatusResponse)
def submit_analysis(request: AnalysisRequest):
    
    log_function_start(logger, "submit_analysis_endpoint", 
                      repo_url=request.repo_url, pr_number=request.pr_number)
    
    try:
        # Validate the request
        validate_analysis_request(request)
        
        # Queue the analysis task
        result = queue_analysis_task(request.repo_url, request.pr_number)
        
        log_function_end(logger, "submit_analysis_endpoint", task_id=result["task_id"])
        return result
        
    except HTTPException:
        log_function_end(logger, "submit_analysis_endpoint", success=False, error="HTTP exception raised")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in submit_analysis: {e}")
        log_function_end(logger, "submit_analysis_endpoint", success=False, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to queue task: {str(e)}"
        )


@app.get("/status/{task_id}", response_model=TaskStatusResponse)
def check_task_status(task_id: str):
    
    log_function_start(logger, "check_task_status_endpoint", task_id=task_id)
    
    try:
        status_info = get_task_status(task_id)
        result = {"task_id": task_id, "status": status_info['status']}
        
        log_function_end(logger, "check_task_status_endpoint", 
                        task_status=status_info['status'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        log_function_end(logger, "check_task_status_endpoint", success=False, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}"
        )


@app.get("/results/{task_id}")
def get_analysis_results(task_id: str):
    
    log_function_start(logger, "get_analysis_results_endpoint", task_id=task_id)
    
    try:
        status_info = get_task_status(task_id)
        
        if status_info['status'] == 'SUCCESS':
            result_data = status_info['result']
            
            # Check if the worker returned an error structure or the final report
            if 'error' in result_data:
                response = format_error_response(task_id, result_data)
                log_function_end(logger, "get_analysis_results_endpoint", 
                                result_type="error", error=result_data['error'])
                return response
            
            # If successful and valid, format as success response
            response = format_success_response(task_id, result_data)
            log_function_end(logger, "get_analysis_results_endpoint", 
                            result_type="success", 
                            files_count=len(result_data.get('files', [])))
            return response

        elif status_info['status'] == 'FAILURE':
            response = {
                "task_id": task_id,
                "status": "FAILED",
                "error": "An unexpected error occurred in the task.",
                "details": status_info['result']
            }
            log_function_end(logger, "get_analysis_results_endpoint", 
                            result_type="failure")
            return response
            
        # For PENDING or PROGRESS states
        response = {
            "task_id": task_id,
            "status": status_info['status'],
            "details": status_info.get('result')  # Show progress metadata if available
        }
        
        log_function_end(logger, "get_analysis_results_endpoint", 
                        result_type="pending_or_progress", 
                        task_status=status_info['status'])
        
        return response
        
    except Exception as e:
        logger.error(f"Error retrieving analysis results: {e}")
        log_function_end(logger, "get_analysis_results_endpoint", success=False, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis results: {str(e)}"
        )


@app.on_event("startup")
def startup_event():
    log_function_start(logger, "fastapi_startup")
    logger.info("Code Review Agent API started successfully")
    log_function_end(logger, "fastapi_startup")


@app.on_event("shutdown") 
def shutdown_event():
    log_function_start(logger, "fastapi_shutdown")
    logger.info("Code Review Agent API shutting down")
    log_function_end(logger, "fastapi_shutdown")