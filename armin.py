#!/usr/bin/python
#coding:utf-8


import click
import config
import logging
from libs.colorlog import ColorizingStreamHandler

from commands.key import deploy_key
from commands.redis import deploy_redis
from commands.sentinel import deploy_sentinel
from commands.nutcracker import deploy_nutcracker
from commands.manage import redis_service
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

commands(build_redis)
commands(deploy_redis)

commands(deploy_sentinel)

commands(redis_service)
commands(deploy_nutcracker)
commands(build_nutcracker)

commands(deploy_key)

if __name__ == '__main__':
    init()
    cli()

