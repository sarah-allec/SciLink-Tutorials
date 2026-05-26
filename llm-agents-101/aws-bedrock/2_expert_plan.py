"""
Lesson 2 -- The system prompt turns a general model into a specialist.

Lesson 1 sent only a user message. Now we add a SYSTEM prompt: an
instruction that sets WHO the model is and the RULES it must follow.
The system prompt is passed as its own `system` argument, separate from
the messages list.

We give the system prompt two jobs:
  * a persona  -- "you are an expert in <field> experiment design"
  * a layout   -- "always answer using these exact section headings"

You type in a field and an experiment. The script drops your field into the
SAME system prompt template, so the model becomes an expert in whatever
field you named. Run it a few times with different fields: one model behaves
as different domain experts, and every plan comes back in the identical layout.

Run it:

    python 2_expert_plan.py
"""

from anthropic import AnthropicBedrock
from dotenv import load_dotenv

load_dotenv()

# Which Claude model to call, on Amazon Bedrock.
MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# The system prompt has two parts: a {domain} placeholder for the persona,
# and a fixed list of headings that pins down the layout of every answer.
SYSTEM_PROMPT_TEMPLATE = """\
You are an expert in {domain} experiment design.

When asked to design an experiment, you ALWAYS structure your answer using
exactly these seven sections, in this order, with these exact headings:

1. Objective
2. Hypothesis
3. Materials & Instruments
4. Procedure
5. Key Parameters
6. Expected Outcomes
7. Risks & Mitigations

Under "Procedure", use numbered steps. Keep the plan concise and practical.
"""


def make_plan(client, domain, request):
    """Ask the model to produce one experimental plan for one domain."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        # The system prompt is its OWN top-level argument, not a message
        # in the list. It is what makes this same model behave as a
        # different domain expert each time you run the script.
        system=SYSTEM_PROMPT_TEMPLATE.format(domain=domain),
        messages=[
            {"role": "user", "content": request},
        ],
    )
    return response.content[0].text


def main():
    client = AnthropicBedrock()

    # Ask the user what kind of expert they want, and what to design.
    print("Design an experiment with an AI domain expert.\n")
    domain = input("Field of expertise (e.g. materials science, chemistry, physics): ").strip()
    request = input("Experiment to design (e.g. how grain size affects a metal's hardness): ").strip()

    if not domain or not request:
        print("\nBoth a field and an experiment are needed. Run the script again.")
        return

    # Your field goes into the system prompt; your request is the user message.
    print("\n(generating plan, please wait...)\n")
    print(make_plan(client, domain, request))

    # Run the script again with a different field -- the code never changes,
    # only the {domain} word in the system prompt does, yet you get a
    # different expert, and the plan keeps the same seven-section layout.


if __name__ == "__main__":
    main()
