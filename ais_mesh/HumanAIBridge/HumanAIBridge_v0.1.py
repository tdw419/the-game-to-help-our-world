# HumanAIBridge_v0.1.py
# Basic terminal chat interface for human-AI messages

import datetime

def log_message(sender, message):
    with open('logs/chat_log.txt', 'a') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{timestamp}] {sender}: {message}\n')

print('=== Human-AI Bridge ===')
while True:
    user_input = input('Human: ')
    if user_input.lower() in ['exit', 'quit']:
        break
    log_message('Human', user_input)
    ai_response = f'Simulated AI response to: {user_input}'
    print(f'AI: {ai_response}')
    log_message('AI', ai_response)
