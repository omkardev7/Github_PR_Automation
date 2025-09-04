from crewai import Agent, Task, Crew, Process
from github_service import get_pr_context
from typing import Dict, Any


def format_pr_context(context: Dict[str, Any]) -> str:
    
    try:
        file_contents = ""
        if context.get('changed_files'):
            file_contents = "\n\n".join([
                f"--- File: {file['filename']} ---\n```\n{file['content']}\n```"
                for file in context['changed_files']
            ])
        
        formatted_text = (
            f"Pull Request Title: {context.get('title', 'N/A')}\n"
            f"Pull Request Description: {context.get('description', 'N/A')}\n\n"
        )
        
        if file_contents:
            formatted_text += f"Changed Files Content:\n{file_contents}\n\n"
            
        if context.get('diff'):
            formatted_text += f"Raw Diff:\n{context['diff']}"
        
        return formatted_text
        
    except Exception as e:
        print(f"Error formatting PR context: {e}")
        return context.get('diff', 'No diff available')


def create_comprehensive_reviewer_agent() -> Agent:
    
    return Agent(
        role="Senior Software Engineer and Code Review Specialist",
        goal=(
            "Perform comprehensive code review analyzing security vulnerabilities, "
            "performance issues, code style violations, and best practice deviations. "
            "Provide actionable feedback with specific suggestions."
        ),
        backstory=(
            "You are an expert software engineer with 10+ years of experience across "
            "multiple programming languages and frameworks. You have deep expertise in "
            "security best practices, performance optimization, and software architecture. "
            "You're known for thorough, constructive code reviews that help teams "
            "improve code quality and prevent bugs from reaching production."
        ),
        llm="gemini/gemini-1.5-flash",
        verbose=True,
        allow_delegation=False,
        max_rpm=10,
        max_retry_limit=3,
    )


def create_review_task(formatted_context: str, agent: Agent) -> Task:
    return Task(
        description=(
            f"Perform a comprehensive code review of the following pull request:\n\n"
            f"{formatted_context}\n\n"
            "Analyze the code changes for:\n"
            "1. **Security Issues**: Look for vulnerabilities like SQL injection, XSS, "
            "authentication bypasses, insecure data handling, etc.\n"
            "2. **Potential Bugs**: Identify logical errors, null pointer exceptions, "
            "race conditions, off-by-one errors, etc.\n"
            "3. **Performance Problems**: Find inefficient algorithms, database query issues, "
            "memory leaks, unnecessary loops, etc.\n"
            "4. **Code Style & Best Practices**: Check for naming conventions, code organization, "
            "SOLID principles, DRY violations, proper error handling, etc.\n\n"
            "For each issue found, determine the severity:\n"
            "- Use 'security' or 'bug' for critical issues that could cause system failures\n"
            "- Use 'performance' for efficiency problems\n"
            "- Use 'style' for formatting and best practice violations\n\n"
            "Focus on providing constructive, actionable feedback with specific line references."
        ),
        expected_output=(
            "A valid JSON object with this exact structure:\n"
            "{\n"
            '  "files": [\n'
            '    {\n'
            '      "name": "path/to/file.py",\n'
            '      "issues": [\n'
            '        {\n'
            '          "type": "security|bug|performance|style",\n'
            '          "line": <line_number>,\n'
            '          "description": "Clear, specific description of the issue",\n'
            '          "suggestion": "Concrete, actionable fix suggestion"\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ],\n'
            '  "summary": {\n'
            '    "total_files": <number_of_files_analyzed>,\n'
            '    "total_issues": <total_issues_found>,\n'
            '    "critical_issues": <count_of_security_and_bug_issues>\n'
            '  }\n'
            "}\n\n"
            "IMPORTANT: Return ONLY the JSON object, no markdown formatting or extra text."
        ),
        agent=agent
    )


def create_code_review_crew(repo_url: str, pr_number: int) -> Crew:

    try:
        
        print(f"Fetching PR context for {repo_url} #{pr_number}")
        pr_context = get_pr_context(repo_url, pr_number)

        formatted_context = format_pr_context(pr_context)

        reviewer_agent = create_comprehensive_reviewer_agent()

        review_task = create_review_task(formatted_context, reviewer_agent)
 
        code_review_crew = Crew(
            agents=[reviewer_agent],
            tasks=[review_task],
            process=Process.sequential,
            verbose=True
        )
        
        return code_review_crew
        
    except Exception as e:
        print(f"Failed to create code review crew: {e}")
        raise


# Fallback function
def create_simple_code_review_crew(repo_url: str, pr_number: int) -> Crew:
    """
    Fallback implementation using just the diff (your current approach).
    """
    from github_service import get_pr_diff
    
    try:
        
        pr_diff = get_pr_diff(repo_url, pr_number)
        
        
        reviewer_agent = create_comprehensive_reviewer_agent()
        
        
        review_task = Task(
            description=(
                f"Analyze the following GitHub pull request diff for repository '{repo_url}' PR #{pr_number}:\n\n"
                f"```diff\n{pr_diff}\n```\n\n"
                "Analyze the changes for security issues, potential bugs, performance problems, "
                "and code style violations. Provide specific, actionable feedback."
            ),
            expected_output=(
                "A valid JSON object with files array containing issues and a summary. "
                "Use types: security, bug, performance, style. "
                "Include line numbers and specific suggestions."
            ),
            agent=reviewer_agent
        )
        
        return Crew(
            agents=[reviewer_agent],
            tasks=[review_task],
            process=Process.sequential,
            verbose=True
        )
        
    except Exception as e:
        print(f"Failed to create simple code review crew: {e}")
        raise