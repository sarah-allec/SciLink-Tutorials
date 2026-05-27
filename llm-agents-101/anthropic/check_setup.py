"""
Run this FIRST -- before the workshop -- to confirm your setup works.

    python check_setup.py

It checks three things:
  1. The required packages are installed.
  2. Your Anthropic API key is present in a .env file.
  3. The key actually works (it makes one tiny API call).
"""

import os
import sys

# Which Claude model to call.
MODEL = "claude-sonnet-4-6"


def main():
    # 1. Are the packages installed?
    try:
        import anthropic
        from anthropic import Anthropic
        from dotenv import load_dotenv
        import numpy   # used by the Lesson 3 tools
        import scipy   # used by the Lesson 3 tools
        import PIL     # used by the Lesson 3 tools
    except ImportError:
        sys.exit(
            "ERROR: Required packages are not installed.\n"
            "       Run:  pip install -r requirements.txt"
        )

    # 2. Is the API key present?
    load_dotenv()  # reads the .env file in this folder
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or "paste-your" in key:
        sys.exit(
            "ERROR: No Anthropic API key found.\n"
            "       Copy .env.example to .env and paste your key into it."
        )

    # 3. Does the key actually work? Make the smallest possible call.
    try:
        client = Anthropic()  # finds ANTHROPIC_API_KEY automatically
        response = client.messages.create(
            model=MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": "Say OK"}],
        )
    except anthropic.AuthenticationError:
        sys.exit("ERROR: The API key was rejected. Check that you copied it correctly.")
    except Exception as error:
        sys.exit(f"ERROR: Something went wrong calling the API:\n       {error}")

    reply = response.content[0].text
    print(f"SUCCESS: All set! The model replied: {reply!r}")
    print("         You're ready for the workshop -- open 1_llm_basics.py next.")


if __name__ == "__main__":
    main()
