# test_components.py - Test individual components
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_github_service():
    """Test GitHub service independently"""
    try:
        from github_service import get_pr_diff
        
        # Test with a public repository
        repo_url = "https://github.com/potpie-ai/potpie"
        pr_number = 432
        
        print(f"Testing GitHub service with {repo_url} PR #{pr_number}")
        diff = get_pr_diff(repo_url, pr_number)
        print(f"Successfully fetched diff (length: {len(diff)})")
        print(f"First 10000 chars: {diff[:10000]}...")
        return True
    except Exception as e:
        print(f"GitHub service test failed: {e}")
        return False

def test_llm_service():
    """Test LLM service independently"""
    try:
        from llm_service import get_gemini_llm
        
        print("Testing Gemini LLM service")
        llm = get_gemini_llm()
        print("Successfully initialized Gemini LLM")
        return True
    except Exception as e:
        print(f"LLM service test failed: {e}")
        return False

def test_crewai_simple():
    """Test CrewAI with a simple example"""
    try:
        from crewai import Agent, Task, Crew, Process
        
        print("Testing CrewAI with simple task using string LLM")
        
        agent = Agent(
            role="Code Reviewer",
            goal="Analyze code and provide feedback",
            backstory="You are a senior developer",
            verbose=True,
            llm="gemini/gemini-1.5-flash",  # Using string format
            max_rpm=10,
            max_retry_limit=3,
            request_timeout=120
        )
        
        task = Task(
            description="Analyze this simple Python code: print('hello world'). Return JSON format: {\"analysis\": \"simple print statement\"}",
            expected_output="JSON object with analysis",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential
        )
        
        result = crew.kickoff()
        print(f"CrewAI test result: {result}")
        return True
        
    except Exception as e:
        print(f"CrewAI test failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        from config import REDIS_URL
        
        print(f"Testing Redis connection to {REDIS_URL}")
        r = redis.from_url(REDIS_URL)
        r.ping()
        print("Redis connection successful")
        return True
    except Exception as e:
        print(f"Redis connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running component tests...\n")
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("GitHub Service", test_github_service),
        ("LLM Service", test_llm_service),
        ("CrewAI Simple", test_crewai_simple),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*50}")
    print("TEST RESULTS")
    print('='*50)
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")