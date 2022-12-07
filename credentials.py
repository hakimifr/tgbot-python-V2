#!/usr/bin/env python3

from getpass import getpass

print("Note: only need to be ran once. Output is intentionally disabled.")

token = getpass("Paste token here: ")
with open("api_token.py", "w") as file:
    file.write("TOKEN = \"" + token + "\"\n")


print(f"Saved token with length: {len(token)}")

