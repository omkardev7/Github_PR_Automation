from crewai import Agent, Task, Crew, Process
# from llm_service import get_gemini_llm
from github_service import get_pr_diff

def create_code_review_crew(repo_url: str, pr_number: int):

    pr_diff = get_pr_diff(repo_url, pr_number)

    code_reviewer_agent = Agent(
        role="Senior Software Engineer and Code Review Specialist",
        goal=f"Analyze the code changes in the pull request #{pr_number} for the repository {repo_url} and provide a detailed review.",
        backstory=(
            "You are an expert software engineer with years of experience in multiple programming languages. "
            "You have a keen eye for detail and a deep understanding of software design principles, best practices, "
            "and common pitfalls. Your task is to perform a thorough code review of a given pull request diff."
        ),
        verbose=True,
        llm="gemini/gemini-1.5-flash",
        allow_delegation=False,
        max_rpm=10,
        max_retry_limit=3,
        #request_timeout=120
    )


    review_task = Task(
        description=(
            f"Analyze the following GitHub pull request diff for repository '{repo_url}' PR #{pr_number}:\n\n"
            f"```diff\n{pr_diff}\n```\n\n"
            "Analyze the diff for the following aspects:\n"
            "1. Code style and formatting consistency.\n"
            "2. Potential bugs, logical errors, or edge cases not handled.\n"
            "3. Opportunities for performance improvements.\n"
            "4. Adherence to software development best practices and principles (e.g., DRY, SOLID).\n\n"
            "Format the output as a JSON object that strictly follows this structure: \n"
            '{\n'
            '  "files": [\n'
            '    {\n'
            '      "name": "path/to/file.py",\n'
            '      "issues": [\n'
            '        {\n'
            '          "type": "style|bug|performance|best_practice",\n'
            '          "line": <line_number>,\n'
            '          "description": "A concise description of the issue.",\n'
            '          "suggestion": "A concrete suggestion for how to fix the issue."\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ],\n'
            '  "summary": {\n'
            '    "total_files": <count>,\n'
            '    "total_issues": <count>,\n'
            '    "critical_issues": <count_of_bug_type_issues>\n'
            '  }\n'
            '}\n'
            "Ensure the entire output is a single, valid JSON object. Do not include any text or markdown before or after the JSON."
        ),
        expected_output="A single, valid JSON object containing the detailed code review.",
        agent=code_reviewer_agent
    )

    code_review_crew = Crew(
        agents=[code_reviewer_agent],
        tasks=[review_task],
        process=Process.sequential,
        verbose=True
    )

    return code_review_crew