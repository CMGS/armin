#!/usr/bin/python
#coding:utf-8


import click
import config
import logging
from libs.colorlog import ColorizingStreamHandler

from commands.key import deploy_key
from commands.redis import deploy_redis, start_redis, stop_redis
from commands.sentinel import start_sentinel
from commands.nutcracker import start_nutcracker
from commands.build import build_redis, build_nutcracker

logger = logging.getLogger(__name__)

def init():
    logging.StreamHandler = ColorizingStreamHandler
    logging.BASIC_FORMAT = "%(asctime)s [%(name)s] %(message)s"
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
    logger = logging.getLogger('paramiko')
    logger.setLevel(logging.WARNING)


@click.group()
@click.pass_context
def cli(ctx):
    logger.info('Armin System Start')

commands = cli.command()

commands(stop_redis)
commands(start_redis)
commands(build_redis)
commands(deploy_redis)

commands(deploy_key)
commands(build_nutcracker)
commands(start_sentinel)
commands(start_nutcracker)

if __name__ == '__main__':
    init()
    cli()

