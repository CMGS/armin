#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from libs.ssh import SSHClient
from libs.scp import SCPClient
from utils import get_group, get_path, render_lines

logger = logging.getLogger(__name__)

def _build(name, ctx, group, configure=False):
    groups = get_group(ctx, group)

    for gn, gv in groups.iteritems():
        pattern = getattr(config, '%s_PATTERN' % name.upper())
        logger.info('Build %s in %s' % (name, gn))
        version, file_path = get_path(ctx, gv, name, config.SRC_DIR, pattern)
        logger.info('%s will extract and install' % file_path)
        tar_name = pattern % version
        dst_dirname = pattern.rstrip('.tar.gz') % version
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
                scp_file(ssh, file_path, config.REMOTE_SCP_DIR)
                remote_path = os.path.join(config.REMOTE_SCP_DIR, tar_name)
                extract_tar(ssh, remote_path, config.REMOTE_SCP_DIR)
                remote_path = os.path.join(config.REMOTE_SCP_DIR, dst_dirname)
                make_and_install(ssh, remote_path, configure)
            except Exception:
                logger.exception('Process in %s failed' % server)
            else:
                logger.info('Build redis in %s was done' % server)
            finally:
                logger.info('Close connection to %s' % server)
                ssh.close()

@click.argument('group')
@click.pass_context
def build_redis(ctx, group):
     _build('redis', ctx, group)

@click.argument('group')
@click.pass_context
def build_nutcracker(ctx, group):
     _build('nutcracker', ctx, group, configure=True)

def scp_file(ssh, local_path, remote_path):
    scp = SCPClient(ssh.get_transport())
    scp.put(local_path, remote_path)

def extract_tar(ssh, remote_path, dst_path):
    command = 'tar xvf {remote_path} -C {dst_path}'
    command = command.format(
        remote_path=remote_path, dst_path=dst_path
    )
    buf = ''
    for lines in ssh.stream_execute(command):
        buf, lines = render_lines(buf + lines)
        map(logger.debug, lines)
    logger.info('Extract succeed')

def make_and_install(ssh, remote_path, configure=False):
    if not configure:
        command = 'cd {remote_path} && make install'
    else:
        command = 'cd {remote_path} && ./configure && make install'
    command = command.format(remote_path=remote_path)
    logger.debug(command)
    buf = ''
    for lines in ssh.stream_execute(command):
        buf, lines = render_lines(buf + lines)
        map(logger.debug, lines)
    logger.info('Make install succeed')
