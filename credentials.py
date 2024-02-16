# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>

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

