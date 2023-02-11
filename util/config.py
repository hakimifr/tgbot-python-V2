import json
import atexit
import logging
from pathlib import Path
log = logging.getLogger("config")


class Config:
    def __init__(self, file: str):
        self.write_pending: bool = False
        self._config: dict = {}
        self.file: str = file

        # Automatically load config from file if exist
        if Path(self.file).exists() and Path(self.file).is_file():
            log.info(f"Auto-loading config from {self.file} since it exists")
            self.read_config()
        else:
            # Create the file to avoid traceback during read_config() call
            with open(self.file, "w")as config:
                config.write("{}")

        # Make sure changes are written upon exit
        atexit.register(self.on_exit)

    def on_exit(self) -> None:
        if not self.write_pending:
            log.info("No need to save changes")

        log.info("Writing unsaved changes")
        self.write_config()

    def write_config(self) -> None:
        log.info(f"Writing config to {self.file}")
        with open(self.file, "w") as config_file:
            json.dump(self.config, config_file, indent=2)
        self.write_pending = False

    def read_config(self) -> None:
        log.info(f"Reading config from {self.file}")
        with open(self.file, "r") as config_file:
            self.config = json.load(config_file)

    @property
    def config(self) -> dict:
        return self._config

    @config.setter
    def config(self, value) -> None:
        self._config = value
        self.write_pending = True

