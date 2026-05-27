"""
Lesson 1 -- An LLM call is just a function.

The big idea: talking to an LLM through the API is ONE function call.
You hand it a list of messages, you get back text. That is the whole model.

    messages  -->  [ LLM ]  -->  text

This script runs top to bottom -- read it like a recipe, line by line.

Run it:

    python 1_llm_basics.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load the Anthropic API key from the .env file

# Which Claude model to call. Change this in one place if your workshop
# uses a different model id.
MODEL = "claude-sonnet-4-6"

# The client is your connection to the Anthropic API. It picks up your
# API key from the ANTHROPIC_API_KEY environment variable automatically.
client = Anthropic()

# A conversation is a list of messages. Each message has a ROLE:
#   "user"      = something you (or your program) said
#   "assistant" = something the model said
# Here we send a single user message.
messages = [
    {
        "role": "user",
        "content": "In two sentences, what is an X-ray diffractogram?",
    }
]

print("Sending one message to the model...\n")

# THE call. Send the messages, get a response back.
response = client.messages.create(
    model=MODEL,
    max_tokens=1000,   # an upper limit on how long the reply can be
    messages=messages,
)

# The reply comes back as a list of "content blocks". For a plain text reply
# there is just one block, of type "text" -- pull its text out.
reply = response.content[0].text
print(reply)

# That is it: one function call in, text out. The model has no memory --
# to continue a conversation you resend the whole message list yourself.
