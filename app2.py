


# -----------------------------
# Tool Function
# -----------------------------
def export_to_file(content):
    filename = "UX_Report.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    return filename


# -----------------------------
# Chat Function
# -----------------------------
def running_chat():

    print("=== UX Helper AI ===")
    print("Type 'export' to save the conversation.")
    print("Type 'reset' to clear the chat.")
    print("Type 'exit' to quit.\n")

    history = []

    system_message = """
WHO:
You are UX Helper AI, a UX design assistant.

WHAT:
Help users improve the UX of any web or mobile application.

You should:
- Identify the target audience.
- Suggest accessibility improvements.
- Explain how to make the app user-friendly.
- Recommend UX best practices.
- Give constructive feedback on app ideas.

WHAT YOU WILL NOT DO:
- Do not answer unrelated questions.
- Do not invent research or statistics.
- Do not generate code.
- Keep answers focused on UX.

Every response MUST follow this format:

[Summary]:
Repeat the user's request in one sentence.

[Response]:
Provide UX advice.

[Next Step]:
Suggest one concrete action the user can take.
"""

    while True:

        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "reset":
            history = []
            print("Conversation cleared.")
            continue

        if user_input.lower() == "export":

            conversation = ""

            for message in history:
                conversation += f"{message['role'].upper()}:\n{message['content']}\n\n"

            filename = export_to_file(conversation)

            print(f"Conversation exported to {filename}")
            continue

        history.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            temperature=0.7,
            system=system_message,
            messages=history
        )

        reply = response.content[0].text

        print("\nUX Helper AI:")
        print(reply)

        history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )


run_chat()