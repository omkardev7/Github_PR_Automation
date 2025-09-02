from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY

def get_gemini_llm():

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")


    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  
        verbose=True,
        temperature=0.1,  
        google_api_key=GEMINI_API_KEY
    )
    return llm