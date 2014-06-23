#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from libs.ssh import SSHClient
from libs.scp import SCPClient
from utils import get_group, get_path

logger = logging.getLogger(__name__)

@click.argument('group')
@click.pass_context
def build_redis(ctx, group):
    groups = get_group(ctx, group)

    for gn, gv in groups.iteritems():
        logger.info('Build redis in %s' % gn)
        version, redis_file_path = get_path(ctx, gv, 'redis', config.SRC_DIR, config.REDIS_PATTERN)
        logger.info('Redis %s tar in %s' % (version, redis_file_path))
        tar_name = config.REDIS_PATTERN % version
        dst_dirname = config.REDIS_PATTERN.rstrip('.tar.gz') % version
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
                scp_file(ssh, redis_file_path, config.REMOTE_SCP_DIR)
                remote_path = os.path.join(config.REMOTE_SCP_DIR, tar_name)
                extract_tar(ssh, remote_path, config.REMOTE_SCP_DIR)
                remote_path = os.path.join(config.REMOTE_SCP_DIR, dst_dirname)
                make_and_install(ssh, remote_path)
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

def extract_tar(ssh, remote_path, dst_path):
    command = 'tar xvf {remote_path} -C {dst_path}'
    command = command.format(
        remote_path=remote_path, dst_path=dst_path
    )
    for line in ssh.stream_execute(command):
        logger.debug(line.strip())
    logger.info('Extract succeed')

def make_and_install(ssh, remote_path):
    command = 'cd {remote_path}; make install'
    command = command.format(remote_path=remote_path)
    for line in ssh.stream_execute(command):
        logger.debug(line.strip())
    logger.info('Make install succeed')

