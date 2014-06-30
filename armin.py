#!/usr/bin/python
#coding:utf-8


import click
import config
import logging
from libs.colorlog import ColorizingStreamHandler

from commands.key import deploy_key
from commands.manage import redis_service, deploy_redis
from commands.build import build

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

commands(deploy_key)
commands(build)
commands(deploy_redis)
commands(redis_service)

#commands(build_redis)
#commands(build_nutcracker)
#commands(deploy_redis)
#commands(deploy_sentinel)
#commands(deploy_nutcracker)


if __name__ == '__main__':
    init()
    cli()

