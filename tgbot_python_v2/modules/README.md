# modules
To create a module, you must define a class named ModuleMetadata. The module loader will
look for this class, and if not found, will refuse to load it.
```python
from util import module
from telegram.ext import Application


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        # do your module setup here, e.g. registering a handler
        pass
```
The module loader code will run the setup_module() method, so when it is not defined,
the module will not be loaded either.


## help messages
Optionally, you may register help message for your commands.
```python
from util.help import Help
from util import module
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("hello", hello))


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.reply_text("hello, world!")


Help.register_help("hello", "Send hello world")  # <--- this line
```
