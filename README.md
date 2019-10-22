# dirty-pig-bot
Breathe life into your Telegram chat with /b-level content.

### Deployment:
* Create `pig/config.py` and add your `TOKEN: str` received from @Botfather, `DEV_KWARGS: dict` to edit requests configuration (default = `{}` or `None`), `WHITELIST: list` to allow certain users execute `@whitelist_only` commands
* Run `collector.py` to get fresh content, save it and create a collection.
* Run `bot.py`, `/start` your bot and send `/2ch` to get up-to-date butthurts
