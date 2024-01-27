import os
import atexit
import pathlib
import logging

import github
import requests


from github import InputFileContent


GIST_ID = "911ec71dae13954d27e513ecfeceb36a"
TOKEN_OK = True
log: logging.Logger = logging.getLogger(__name__)

try:
    from api_token import GITHUB_TOKEN
    if len(GITHUB_TOKEN) == 0:
        log.warning("GH token from api_token.py is empty... attempting to get from environment variable")
        raise ImportError
except ImportError:
    if not (GITHUB_TOKEN := os.getenv("GITHUB_TOKEN")):
        TOKEN_OK = False
        log.error("Failed to get github token.")

gh = github.Github(GITHUB_TOKEN)
gist = gh.get_gist(GIST_ID)
session: requests.Session = requests.Session()
blacklisted_configs = ["updater.json"]


def fetch_file():
    if not TOKEN_OK:
        return

    for file, file_metadata in gist.files.items():
        if file in blacklisted_configs:
            log.warning(f"Skipping blacklisted config file: '{file}'")
            continue

        log.info(f"Fetch config file: '{file}'")
        log.debug(str(dict(file_metadata.raw_data)))

        if not file_metadata.raw_data.get("truncated"):
            with open(file_metadata.filename, "w") as f:
                f.write(file_metadata.content)
        else:
            with open(file_metadata.filename, "w") as f:
                f.write(str(requests.get(file_metadata.raw_url, cookies=session).content))


def backup_file():
    if not TOKEN_OK:
        return

    files = pathlib.Path(".").rglob("*.json")
    for file in files:
        if file in blacklisted_configs:
            log.warning(f"Skipping blacklisted config file: '{file}'")
            continue

        log.info(f"Backing up config file: '{file.name}'")
        with open(file, "r") as f:
            content = f.read()

        gist.edit("Update", {file.name: InputFileContent(content, file.name)})
        log.info(f"Finished backup for file: '{file.name}'")


atexit.register(backup_file)
