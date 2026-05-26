"""
Run this FIRST -- before the workshop -- to confirm your setup works.

    python check_setup.py

It checks three things:
  1. The required packages are installed.
  2. Your Amazon Bedrock API key is present in a .env file.
  3. The key actually works (it makes one tiny API call to Bedrock).
"""

import os
import sys

# Which Claude model to call, on Amazon Bedrock. The "us." prefix is a
# cross-region inference profile, available in US regions.
MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def main():
    # 1. Are the packages installed?
    try:
        import anthropic
        from anthropic import AnthropicBedrock
        from dotenv import load_dotenv
        import numpy   # used by the Lesson 3 tools
        import scipy   # used by the Lesson 3 tools
        import PIL     # used by the Lesson 3 tools
    except ImportError:
        sys.exit(
            "ERROR: Required packages are not installed.\n"
            "       Run:  pip install -r requirements.txt"
        )

    # 2. Is the Bedrock API key present?
    load_dotenv()  # reads the .env file in this folder
    key = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
    if not key or "paste-your" in key:
        sys.exit(
            "ERROR: No Bedrock API key found.\n"
            "       Copy .env.example to .env and paste your key into it."
        )

    # 3. Does the key actually work? Make the smallest possible call.
    #    AnthropicBedrock() picks up AWS_BEARER_TOKEN_BEDROCK and AWS_REGION
    #    from the environment automatically.
    try:
        client = AnthropicBedrock()
        response = client.messages.create(
            model=MODEL,
            max_tokens=5,
            messages=[{"role": "user", "content": "Say OK"}],
        )
    except anthropic.AuthenticationError:
        sys.exit("ERROR: The Bedrock API key was rejected. Check that you copied it correctly.")
    except anthropic.PermissionDeniedError:
        sys.exit(
            "ERROR: Bedrock denied the request.\n"
            "       The key may not have access to this model in this region.\n"
            "       Check with the workshop organizer that the right model is enabled."
        )
    except Exception as error:
        sys.exit(f"ERROR: Something went wrong calling Bedrock:\n       {error}")

    reply = response.content[0].text
    print(f"SUCCESS: All set! The model replied: {reply!r}")
    print("         You're ready for the workshop -- open 1_llm_basics.py next.")


if __name__ == "__main__":
    main()
