#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from utils.helper import get_group, get_path, get_ssh
from utils.tools import scp_file, extract_tar, make_and_install

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
                ssh = get_ssh(server, keyname, config.ROOT)
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

