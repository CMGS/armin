#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from libs.ssh import SSHClient
from utils import get_group, get_path

logger = logging.getLogger(__name__)

@click.argument('group')
@click.pass_context
def deploy_key(ctx, group):
    groups = get_group(ctx, group)

    ssh_dir = '/root/.ssh'
    ssh_pub_key = os.path.join(ssh_dir, 'authorized_keys')

    for gn, gv in groups.iteritems():
        keyname, pub_key_path = get_path(ctx, gv, 'keyname', config.KEY_DIR, config.PUB_KEY_PATTERN)
        logger.info('Deploy key to %s' % gn)
        logger.info('Key path %s' % pub_key_path)
        with open(pub_key_path, 'r') as f:
            key = f.readline().strip()
        for server in gv['servers']:
            logger.info('Connect to %s' % server)
            try:
                ssh = SSHClient(server, username=gv['username'], password=gv['password'])
                commands = (
                    'mkdir -p {ssh_dir};'
                    'chmod 700 {ssh_dir};'
                    'touch {ssh_pub_key};'
                    'cat {ssh_pub_key}'
                )
                commands = commands.format(ssh_pub_key=ssh_pub_key, ssh_dir=ssh_dir)
                logger.debug(commands)
                ret = ssh.execute(commands, sudo=True)
                if not check_key(ret['out'], key):
                    continue
                commands = (
                    'echo "{key}" >> {ssh_pub_key};'
                    'chmod 644 {ssh_pub_key};'
                )
                commands = commands.format(ssh_pub_key=ssh_pub_key, key=key)
                logger.debug(commands)
                ret = ssh.execute(commands, sudo=True)
                if ret['retval']() == 0:
                    logger.info('Deploy succeeded')
                else:
                    logger.warn('Deploy failed')
            except Exception:
                logger.exception('Process in %s failed' % server)
            else:
                logger.info('Deploy key to %s done' % server)
            finally:
                logger.info('Close connection to %s' % server)
                ssh.close()

def check_key(out, key):
    for line in out:
        if key not in line:
            continue
        return False
    return True

