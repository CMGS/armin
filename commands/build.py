#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from libs.ssh import SSHClient
from libs.scp import SCPClient
from utils import get_group

logger = logging.getLogger(__name__)

@click.argument('group')
@click.pass_context
def build_redis(ctx, group):
    groups = get_group(ctx, group)

    logger.info('Redis tar in %s' % config.REDIS_FILE_PATH)

    for gn, gv in groups.iteritems():
        logger.info('Build redis in %s' % gn)
        for server in gv['servers']:
            logger.info('Connect to %s' % server)
            try:
                keyname = gv.get('keyname')
                if keyname:
                    ssh = SSHClient(
                        server, \
                        username='root', \
                        key_filename=os.path.join(config.KEY_DIR, keyname)
                    )
                else:
                    ssh = SSHClient(
                        server, \
                        username=gv['username'], \
                        password=gv.get('password'), \
                    )
                logger.info('SCP redis tar to %s' % server)
                scp_file(ssh, config.REDIS_FILE_PATH, '/tmp')
            except Exception:
                logger.exception('Process in %s failed' % server)
            else:
                logger.info('Build redis in %s was done' % server)
            finally:
                logger.info('Close connection to %s' % server)
                ssh.close()

def scp_file(ssh, local_path, remote_path):
    scp = SCPClient(ssh.get_transport())
    scp.put(local_path, remote_path)

