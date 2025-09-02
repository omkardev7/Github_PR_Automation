from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class AnalysisRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str] = None


class AnalysisIssue(BaseModel):
    type: str
    line: int
    description: str
    suggestion: str

class FileAnalysisResult(BaseModel):
    name: str
    issues: List[AnalysisIssue]

class AnalysisSummary(BaseModel):

    total_files: int
    total_issues: int
    critical_issues: int

class AnalysisResult(BaseModel):
    files: List[FileAnalysisResult]
    summary: AnalysisSummary

class TaskStatusResponse(BaseModel):
   
    task_id: str
    status: str

class SuccessTaskResult(BaseModel):
    task_id: str
    status: str
    results: AnalysisResult

class FailedTaskResult(BaseModel):
    task_id: str
    status: str
    error: str

class PendingTaskResult(BaseModel):
    task_id: str
    status: str

TaskResultResponse = Union[SuccessTaskResult, FailedTaskResult, PendingTaskResult]