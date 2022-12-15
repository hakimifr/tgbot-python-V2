import logging
log = logging.getLogger("help")


class Help:
    """Class for storing help strings. Class methods only."""
    help_messages: dict = {}

    @classmethod
    def register_help(cls, command: str, help_string: str) -> None:
        """Register a unique help string for a command."""
        if cls.help_messages.get(command) is None:
            log.info(f"Registering help for command {command}")
            cls.help_messages[command] = help_string
        else:
            log.warning(f"Command {command} already have help message set!")

    @classmethod
    def remove_help(cls, command: str) -> None:
        """Remove a help string for a command."""
        if cls.help_messages.get(command) is not None:
            log.info(f"Removing help string for command {command}")
            del cls.help_messages[command]
        else:
            log.warning(f"No help message from {command} to be removed!")

    @classmethod
    def get_help(cls, commands: list = None) -> str:
        """Return help string of all commands combined.
        e.g.:
        /foo -> bar
        /baz -> bat"""
        if commands is None:
            commands = []

        help_message = ""
        for cmd in cls.help_messages.keys():
            # help_message += "/" + cmd + " -> " + cls.help_messages[cmd] + '\n'
            help_message += f"/{cmd} -> {cls.help_messages[cmd]}\n"

        return help_message
