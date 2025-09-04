from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Union
from logger_config import setup_logger, log_function_start, log_function_end

# Initialize logger
logger = setup_logger(__name__)

# --- API Request Models ---

class AnalysisRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    pr_number: int = Field(..., description="Pull request number", gt=0)
    github_token: Optional[str] = Field(None, description="Optional GitHub token for authentication")

    def __init__(self, **data):
        log_function_start(logger, "AnalysisRequest.__init__", 
                          repo_url=data.get('repo_url', 'N/A'),
                          pr_number=data.get('pr_number', 'N/A'))
        super().__init__(**data)
        log_function_end(logger, "AnalysisRequest.__init__", model_created=True)

# --- Core Data Models for Analysis ---

class AnalysisIssue(BaseModel):
    type: str = Field(..., description="Type of issue, e.g., 'bug', 'performance', 'style', 'security'.")
    line: int = Field(..., description="The line number where the issue occurs.")
    description: str = Field(..., description="A concise description of the issue.")
    suggestion: str = Field(..., description="A concrete suggestion for how to fix the issue.")


def create_analysis_issue(issue_type: str, line: int, description: str, suggestion: str) -> AnalysisIssue:
    
    log_function_start(logger, "create_analysis_issue", 
                      issue_type=issue_type, line=line)
    
    try:
        issue = AnalysisIssue(
            type=issue_type,
            line=line,
            description=description,
            suggestion=suggestion
        )
        
        log_function_end(logger, "create_analysis_issue", issue_created=True)
        return issue
        
    except Exception as e:
        logger.error(f"Failed to create analysis issue: {e}")
        log_function_end(logger, "create_analysis_issue", success=False, error=str(e))
        raise


class FileAnalysis(BaseModel):
    name: str = Field(..., description="The path to the file.")
    issues: List[AnalysisIssue] = Field(default_factory=list, description="List of issues found in the file")


def create_file_analysis(filename: str, issues: List[AnalysisIssue] = None) -> FileAnalysis:
    
    log_function_start(logger, "create_file_analysis", 
                      filename=filename, issues_count=len(issues or []))
    
    try:
        file_analysis = FileAnalysis(
            name=filename,
            issues=issues or []
        )
        
        log_function_end(logger, "create_file_analysis", 
                        file_analysis_created=True, 
                        issues_count=len(file_analysis.issues))
        return file_analysis
        
    except Exception as e:
        logger.error(f"Failed to create file analysis: {e}")
        log_function_end(logger, "create_file_analysis", success=False, error=str(e))
        raise


class AnalysisSummary(BaseModel):
    total_files: int = Field(..., description="Total number of files analyzed", ge=0)
    total_issues: int = Field(..., description="Total number of issues found", ge=0)
    critical_issues: int = Field(..., description="Number of critical issues (bugs/security)", ge=0)


def create_analysis_summary(total_files: int, total_issues: int, critical_issues: int) -> AnalysisSummary:
    
    log_function_start(logger, "create_analysis_summary", 
                      total_files=total_files, 
                      total_issues=total_issues, 
                      critical_issues=critical_issues)
    
    try:
        summary = AnalysisSummary(
            total_files=total_files,
            total_issues=total_issues,
            critical_issues=critical_issues
        )
        
        log_function_end(logger, "create_analysis_summary", summary_created=True)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to create analysis summary: {e}")
        log_function_end(logger, "create_analysis_summary", success=False, error=str(e))
        raise


class FinalReport(BaseModel):
    files: List[FileAnalysis] = Field(default_factory=list, description="List of analyzed files with their issues")
    summary: AnalysisSummary = Field(..., description="Summary of the analysis results")


def create_final_report(files: List[FileAnalysis], summary: AnalysisSummary) -> FinalReport:
    """
    Factory function to create a FinalReport instance.
    
    Args:
        files: List of FileAnalysis instances
        summary: AnalysisSummary instance
        
    Returns:
        FinalReport instance
    """
    log_function_start(logger, "create_final_report", 
                      files_count=len(files),
                      total_issues=summary.total_issues)
    
    try:
        report = FinalReport(
            files=files,
            summary=summary
        )
        
        log_function_end(logger, "create_final_report", 
                        report_created=True,
                        files_in_report=len(report.files))
        return report
        
    except Exception as e:
        logger.error(f"Failed to create final report: {e}")
        log_function_end(logger, "create_final_report", success=False, error=str(e))
        raise


def validate_final_report_data(data: dict) -> FinalReport:

    log_function_start(logger, "validate_final_report_data", 
                      has_files=bool(data.get('files')),
                      has_summary=bool(data.get('summary')))
    
    try:
        validated_report = FinalReport.model_validate(data)
        
        log_function_end(logger, "validate_final_report_data", 
                        validation_success=True,
                        files_count=len(validated_report.files),
                        total_issues=validated_report.summary.total_issues)
        
        return validated_report
        
    except ValidationError as e:
        logger.error(f"Final report validation failed: {e}")
        log_function_end(logger, "validate_final_report_data", success=False, 
                        validation_error=str(e))
        raise


# --- API Response Models ---

class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")

    def __init__(self, **data):
        log_function_start(logger, "TaskStatusResponse.__init__", 
                          task_id=data.get('task_id', 'N/A'),
                          status=data.get('status', 'N/A'))
        super().__init__(**data)
        log_function_end(logger, "TaskStatusResponse.__init__", model_created=True)


class SuccessResultResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(default="COMPLETED", description="Status of the completed task")
    results: FinalReport = Field(..., description="The analysis results")

    def __init__(self, **data):
        log_function_start(logger, "SuccessResultResponse.__init__", 
                          task_id=data.get('task_id', 'N/A'))
        super().__init__(**data)
        log_function_end(logger, "SuccessResultResponse.__init__", 
                        model_created=True,
                        files_count=len(data.get('results', {}).get('files', [])))


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message describing what went wrong")

    def __init__(self, **data):
        log_function_start(logger, "ErrorResponse.__init__", 
                          has_detail=bool(data.get('detail')))
        super().__init__(**data)
        log_function_end(logger, "ErrorResponse.__init__", model_created=True)


def create_task_status_response(task_id: str, status: str) -> TaskStatusResponse:
 
    log_function_start(logger, "create_task_status_response", 
                      task_id=task_id, status=status)
    
    try:
        response = TaskStatusResponse(task_id=task_id, status=status)
        log_function_end(logger, "create_task_status_response", response_created=True)
        return response
        
    except Exception as e:
        logger.error(f"Failed to create task status response: {e}")
        log_function_end(logger, "create_task_status_response", success=False, error=str(e))
        raise


def create_success_result_response(task_id: str, results: FinalReport) -> SuccessResultResponse:
    
    log_function_start(logger, "create_success_result_response", 
                      task_id=task_id, 
                      results_files_count=len(results.files))
    
    try:
        response = SuccessResultResponse(task_id=task_id, results=results)
        log_function_end(logger, "create_success_result_response", response_created=True)
        return response
        
    except Exception as e:
        logger.error(f"Failed to create success result response: {e}")
        log_function_end(logger, "create_success_result_response", success=False, error=str(e))
        raise


def create_error_response(detail: str) -> ErrorResponse:
    
    log_function_start(logger, "create_error_response", detail_length=len(detail))
    
    try:
        response = ErrorResponse(detail=detail)
        log_function_end(logger, "create_error_response", response_created=True)
        return response
        
    except Exception as e:
        logger.error(f"Failed to create error response: {e}")
        log_function_end(logger, "create_error_response", success=False, error=str(e))
        raise