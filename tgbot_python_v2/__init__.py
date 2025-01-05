import inspect

from pathlib import Path

MODULE_DIR: str = Path(inspect.getfile(lambda _: _)).parent  # type: ignore
