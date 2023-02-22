import json
import atexit
import logging
from pathlib import Path
log: logging.Logger = logging.getLogger(__name__)


class Config:
    active_config: list[str] = []

    def __init__(self, file: str):
        if file in Config.active_config:
            raise ValueError("The config file is already opened by another instance!")

        self.write_pending: bool = False
        self._config: dict = {}
        self.file: str = file
        self.closed: bool = False

        Config.active_config.append(file)

        # Automatically load config from file if exist
        if Path(self.file).exists() and Path(self.file).is_file():
            log.info(f"Auto-loading config from {self.file} since it exists")
            self.read_config()
        else:
            # Create the file to avoid traceback during read_config() call
            with open(self.file, "w") as config:
                config.write("{}")

        # Make sure changes are written upon exit
        atexit.register(self.on_exit)

    @staticmethod
    def _ensure_open(method):
        def wrapper(self, *args, **kwargs):
            if self.closed:
                raise RuntimeError("This config instance is already closed")
            return method(self, *args, **kwargs)
        return wrapper

    def on_exit(self) -> None:
        if self.closed:
            log.info("Instance already closed, will not write config")
            return

        if not self.write_pending:
            log.info("No need to save changes")

        log.info("Writing unsaved changes")
        self.write_config()

    @_ensure_open
    def write_config(self) -> None:
        log.info(f"Writing config to {self.file}")
        with open(self.file, "w") as config_file:
            json.dump(self.config, config_file, indent=2)
        self.write_pending = False

    @_ensure_open
    def read_config(self) -> None:
        log.info(f"Reading config from {self.file}")
        with open(self.file, "r") as config_file:
            self.config = json.load(config_file)

    @property
    def config(self) -> dict:
        return self._config

    @_ensure_open
    @config.setter
    def config(self, value) -> None:
        self._config = value
        self.write_pending = True

    def close(self) -> None:
        self.write_config()
        Config.active_config.remove(self.file)
        self.closed = True

