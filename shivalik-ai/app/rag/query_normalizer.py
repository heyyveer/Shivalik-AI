
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_normalizer = ChatGroq(
    model=os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    ),
    temperature=0,
    max_tokens=256,
)

NORMALIZATION_PROMPT = """
You rewrite user questions into concise English search queries
for a university information retrieval system.

Rules:
1. Translate Hindi and Hinglish into English.
2. Preserve the original meaning.
3. Preserve all numbers, percentages, course names, and subjects.
4. Do not invent missing details.
5. Do not answer the question.
6. Output only the rewritten search query.
7. Include useful retrieval terms such as eligibility,
   admission criteria, fees, placements, or contact details
   when relevant.
8. CRITICAL: Never omit numerical values from the latest question,
   including percentages, marks, fees, years, dates, or quantities.
   The rewritten query must be complete.
   
Example:
Input: mere 12th me 55percent hain kya mai admission le sakta hun btech me
Output: B.Tech admission eligibility minimum Class 12 percentage 55 percent

Example:
Input: btech ki fees kitni hai
Output: B.Tech programme fee structure per year

Example:
Input: contact details?
Output: University contact details phone email address
"""



def normalize_query(
    question: str,
    history: list[dict] | None = None
) -> str:
    """
    Convert user questions into standalone English search queries.

    Uses recent conversation history to resolve follow-up
    questions without inventing missing information.
    """

    question = question.strip()

    if not question:
        return question

    history = history or []

    # Keep only recent conversation context
    recent_history = history[-10:]

    history_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    )

    prompt = """
You are a query rewriting assistant for a university RAG system.

Your task:
Rewrite the latest user question into a standalone English
search query suitable for semantic and keyword retrieval.

Rules:
1. Translate Hindi or Hinglish into English.
2. Use conversation history only to resolve references
   and follow-up questions.
3. Preserve all numbers, percentages, and course names.
4. Do not invent information.
5. If the question is unrelated to the previous conversation,
   ignore the history.
6. Do not answer the question.
7. Output only the rewritten search query.

Example:

History:
user: What is the eligibility for B.Tech CSE Data Science?
assistant: Minimum 60% in Class 12.

Latest question:
What if I have 55%?

Output:
B.Tech CSE Data Science admission eligibility
with 55 percent marks in Class 12
"""

    try:
        response = _normalizer.invoke([
            SystemMessage(content=prompt),
            HumanMessage(
                content=(
                    f"Conversation History:\n{history_text}\n\n"
                    f"Latest Question:\n{question}"
                )
            ),
        ])

        normalized = response.content.strip()

        return normalized if normalized else question

    except Exception as error:
        print(f"[Query Normalization Warning] {error}")
        return question

