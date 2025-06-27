class DemoApp:
    def __init__(self):
        self.name = "Demo App"
    
    def execute_command(self, command: str) -> str:
        if command == "hello":
            return "Hello from Demo App!"
        return "Command not recognized"

def main():
    return DemoApp()