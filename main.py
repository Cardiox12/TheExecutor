from srcs.config.Config import Config
from srcs.context.Contexts import Contexts
from srcs.bot.Bot import Bot
from srcs.docker.Docker import Docker
import os

conf = Config("config.yaml")
cts = Contexts("context.yaml")
# bot = Bot(conf, cts)