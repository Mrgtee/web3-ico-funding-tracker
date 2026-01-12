import os
from dotenv import load_dotenv
from agent import app

load_dotenv()

if __name__ == "__main__":
    print("Web3 ico and funding tracker is starting...")
    # This loop lets you chat with it in the terminal
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        for chunk in app.stream({"messages": [("user", user_input)]}):
            print(chunk)