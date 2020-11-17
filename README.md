# The Executor

The executor is a discord bot that allows you to execute scripts within discord. \
Scripts are executed inside Docker containers so it provide a safe execution environment.

## How it works

All you have to do is [markdown](https://support.discord.com/hc/fr/articles/210298617-Bases-de-la-mise-en-forme-de-texte-Markdown-mise-en-forme-du-chat-gras-italique-soulign%C3%A9-) the code you want to execute followed by the `!run` command.

Example :
```
```py
print("Hello World!")
```!run
```

## Config

The Executor need Docker and python to work properly.

## Installation

### Install

First you'll need to run :
```sh
./setup.sh install
```

The installation will pull Docker images and install the requirements.txt modules.

### Config

To run The Executor, you have to configure config.yaml to define your **API_KEY**, **scope** and **exec**. \
The configuration file *config.yaml* is composed of the following variables :

```yaml
exec:
  # Timeout before script is being killed by Subprocess.
  timeout: INT
bot:
  # API Key of your discord bot, see https://discord.com/developers/applications
  API_KEY: "YOUR_DISCORD_API_KEY"
server:
  # Define The Executor permissions
  scope:
    channels:
      - "CHANNEL_ID"
    roles:
      - "ROLE_NAME"
```

### Run
Then finally, run bot.py
```py
python bot.py
```

## Security

For safety reasons, each execution is made inside docker containers, so it provide a safe execution environment. \
All script exceeding **TIMEOUT** are killed. You can define [Discord roles] so you can choose who can execute script within your server.

## Supports
For now The Executor support the following languages :
  - Python
  - Javascript
  - PHP
  - Bash
