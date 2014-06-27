#!/usr/bin/python
#coding:utf-8


import click
import config
import logging
from libs.colorlog import ColorizingStreamHandler

from commands.key import deploy_key
from commands.redis import deploy_redis, \
    start_redis, stop_redis, restart_redis
from commands.sentinel import deploy_sentinel, \
    start_sentinel, stop_sentinel, restart_sentinel
from commands.nutcracker import deploy_nutcracker, \
    start_nutcracker, stop_nutcracker, restart_nutcracker
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
commands(restart_redis)
commands(build_redis)
commands(deploy_redis)

commands(stop_sentinel)
commands(start_sentinel)
commands(restart_sentinel)
commands(deploy_sentinel)

commands(start_nutcracker)
commands(stop_nutcracker)
commands(restart_nutcracker)
commands(deploy_nutcracker)
commands(build_nutcracker)

commands(deploy_key)

if __name__ == '__main__':
    init()
    cli()

