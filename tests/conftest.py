import os


# Unit tests must never consume a developer's Gemini quota from a local .env file.
os.environ["GEMINI_API_KEY"] = ""
