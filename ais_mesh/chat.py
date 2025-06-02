import datetime

chat_log = []

def display_chat():
    print("\n=== HUMAN–AI BRIDGE ===\n")
    for entry in chat_log:
        print(f"[{entry['timestamp']}] {entry['sender']}: {entry['message']}")
    print("\n(Enter 'quit' to exit)\n")

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def ai_response(human_input):
    if "protocol" in human_input.lower():
        return "Protocol received. Should I archive this in the Covenant Ledger?"
    elif "hello" in human_input.lower():
        return "Greetings, human! The relay is active. How shall we proceed?"
    else:
        return "Message acknowledged. Ready for next instructions."

# Main loop
while True:
    display_chat()
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    chat_log.append({
        "timestamp": get_timestamp(),
        "sender": "Human",
        "message": user_input
    })

    response = ai_response(user_input)
    chat_log.append({
        "timestamp": get_timestamp(),
        "sender": "AI",
        "message": response
    })
