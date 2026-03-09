import os
from dotenv import load_dotenv

from groq import Groq
load_dotenv()
grok_key = os.getenv("GROQ_API_KEY")
client = Groq(
    api_key=grok_key
)
async def sanitize_text(text):
    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Extract the main content from the following text and remove any irrelevant information, such as timestamps, speaker labels, or background noise descriptions. Return only the cleaned text without any additional formatting or explanations.\n\n" + text,
        }
    ],
    model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content