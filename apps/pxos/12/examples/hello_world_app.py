#!/usr/bin/env python3
"""
Hello World App - Simple example for PXBot
"""

class HelloWorldApp:
    def __init__(self, pxbot_instance=None):
        self.name = "Hello World"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
        self.message_count = 0
    
    def execute_command(self, command):
        if command.startswith("hello:"):
            cmd = command[6:]
            
            if cmd == "world":
                self.message_count += 1
                return f"Hello, World! (Message #{self.message_count})"
            elif cmd == "user":
                return "Hello, User! Welcome to PXBot!"
            elif cmd.startswith("name:"):
                name = cmd[5:]
                return f"Hello, {name}! Nice to meet you!"
            elif cmd == "stats":
                return f"Hello statistics: {self.message_count} messages sent"
            else:
                return "Commands: hello:world, hello:user, hello:name:YourName, hello:stats"
        
        return "Use hello: prefix for commands"

def main():
    return HelloWorldApp()

if __name__ == "__main__":
    app = main()
    print("Hello World App Test")
    print(app.execute_command("hello:world"))
    print(app.execute_command("hello:name:Alice"))
