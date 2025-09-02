from fastapi import FastAPI, HTTPException
from models import AnalysisRequest, TaskStatusResponse, AnalysisResult
from worker import celery_app, get_task_status

app = FastAPI(
    title="Autonomous Code Review Agent API",
    description="An API to trigger AI-powered code reviews for GitHub pull requests.",
    version="1.0.0"
)

@app.post("/analyze-pr", status_code=202, response_model=TaskStatusResponse)
def submit_analysis(request: AnalysisRequest):
    try:
        task = celery_app.send_task(
            'worker.analyze_pr_task',
            args=[request.repo_url, request.pr_number, request.github_token]
        )
        return {"task_id": task.id, "status": "PENDING"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@app.get("/status/{task_id}", response_model=TaskStatusResponse)
def check_task_status(task_id: str):

    status_info = get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status_info['status']}

@app.get("/results/{task_id}")
def get_analysis_results(task_id: str):
    status_info = get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status_info['status'] == 'SUCCESS':
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "results": status_info['result']
        }
    elif status_info['status'] == 'FAILURE':
         return {
            "task_id": task_id,
            "status": "FAILED",
            "error": status_info['result']
        }
    else:
        return {
            "task_id": task_id, 
            "status": status_info['status']
        }