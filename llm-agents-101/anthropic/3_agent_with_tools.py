"""
Lesson 3 -- Tools + a loop = an "agent".

A plain LLM can only produce text (Lessons 1 and 2). It cannot actually
look at an image or run an analysis. TOOLS close that gap.

How tool use really works -- and the part beginners get wrong:
the model never runs your code. It only *requests* a tool by name.
YOUR code runs the tool and hands the result back. An "agent" is just:

    LLM  +  tools  +  a loop that runs until the model stops asking for tools.

Here the model has three real microscopy tools (see tools.py). They genuinely
open and analyze the synthetic data files in the data/ folder. You type a
question; the model reads the tool descriptions and picks the matching tool.
Ask different kinds of questions and watch it choose a different tool.

Run it:

    python 3_agent_with_tools.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

from tools import TOOL_SCHEMAS, TOOL_FUNCTIONS

load_dotenv()

# Which Claude model to call.
MODEL = "claude-sonnet-4-6"


def run_agent(client, question):
    """Run the agent loop for one question and return the final answer."""
    # The running conversation. We append to it every time around the loop.
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            tools=TOOL_SCHEMAS,   # <-- this is what makes tool use possible
            messages=messages,
        )

        # If the model stopped because it has produced its final text answer
        # (not because it wants a tool), we are done -- pull the text out.
        # `response.content` is a list of blocks; the text we want is the
        # last "text" block.
        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        # The model asked for one or more tools. First, echo its full message
        # (which carries the tool requests as content blocks) back into the
        # conversation. Anthropic wants every tool_use to be matched by a
        # tool_result in the very next user message.
        messages.append({"role": "assistant", "content": response.content})

        # ...then run each requested tool ourselves and add the results
        # together in a single user message.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            name = block.name
            args = block.input   # already a dict -- no JSON parsing needed
            print(f"    model picked tool: {name}  with {args}")

            run_tool = TOOL_FUNCTIONS[name]   # name -> our function
            result = run_tool(**args)         # WE run it, not the model

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,   # ties result to the request
                    "content": str(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

        # Loop again: the model now has the data and will either ask for
        # another tool or produce a final answer.


def main():
    client = Anthropic()

    # Tell the user what data is available, then let them ask anything.
    print("Ask the agent a question about the sample data in the data/ folder:")
    print("  data/nanoparticles.png  -- a microscopy image")
    print("  data/eds_spectrum.csv   -- an EDS spectrum")
    print("Try asking how many particles there are, how big they are, or")
    print("which elements are present -- name a file in your question.\n")

    question = input("Your question: ").strip()
    if not question:
        print("No question entered. Run the script again.")
        return

    # Hand the question to the agent and print its answer.
    print(f"\nQ: {question}")
    answer = run_agent(client, question)
    print(f"A: {answer}")

    # Run the script again with a different question -- the model reads the
    # tool DESCRIPTIONS in tools.py and matches each question to the right one.


if __name__ == "__main__":
    main()
