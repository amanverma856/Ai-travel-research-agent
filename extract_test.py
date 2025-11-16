from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

def extract_flight_details(user_query):
    llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")

    prompt = PromptTemplate(
        input_variables=["user_query"],
        template=(
            "Extract flight details ONLY in JSON.\n"
            "Format: {\"origin\":\"CITY\", \"destination\":\"CITY\", \"date\":\"YYYY-MM-DD\"}\n"
            "Convert 'tomorrow' to actual date.\n\n"
            "Text: {user_query}"
        )
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    result = chain.run(user_query=user_query)

    print("\nRAW LLM OUTPUT:\n", result)

    # Extract JSON block
    start = result.find("{")
    end = result.rfind("}") + 1
    json_str = result[start:end]

    data = json.loads(json_str)

    # fix date
    if "tomorrow" in data["date"].lower():
        data["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    return data


print(extract_flight_details("book flight patna to bengaluru tomorrow"))
