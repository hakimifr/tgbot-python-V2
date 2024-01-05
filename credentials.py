#!/usr/bin/env python3

from getpass import getpass

print("Note: only need to be ran once. Output is intentionally disabled.")

secrets = [
    "TOKEN",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY"
]

with open("api_token.py", "a", encoding="utf-8") as file:
    for secret in secrets:
        token = getpass(f"Enter {secret} here: ")
        file.write(f'{secret} = "{token}"\n')

        print(f" -> Saved {secret} with length: {len(token)}")

print(f"\nSaved api_token.py with all credentials.")

