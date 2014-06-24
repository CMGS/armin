#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from libs.ssh import SSHClient
from libs.scp import SCPClient
from tempfile import NamedTemporaryFile
from utils import get_path, scp_file, get_ssh

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def start_redis(ctx, cluster):
    cluster = config.REDIS.get(cluster)
    if not cluster:
        ctx.fail('%s not define' % cluster)

    maxmemory = cluster['maxmemory']
    redis = cluster['redis']
    sentinel = cluster['sentinel']

    for master, values in redis.iteritems():
        logger.info('Connect to master %s' % master)
        do_redis_install(master, values, maxmemory)

def do_redis_install(server, values, maxmemory):
    server, port = get_bind_port(server)
    keyname = values.get('keyname')
    version = values.get('version')

    dst_dirname = config.REDIS_PATTERN.rstrip('.tar.gz') % version
    remote_path = os.path.join(config.REMOTE_SCP_DIR, dst_dirname, config.REDIS_CONF)

    try:
        ssh = get_ssh(server, keyname, 'root')
        send_conf(ssh, config.REDIS_CONF, '', maxmemory, server, remote_path)

    except Exception:
        logger.exception('Process in %s failed' % server)
    else:
        logger.info('Process in %s was done' % server)
    finally:
        logger.info('Close connection to %s' % server)
        ssh.close()

def get_bind_port(ip):
    return ip.split(':')

def send_conf(ssh, conf, slaveof, maxmemory, server, path):
    tpl = config.GET_CONF.get_template(conf)
    tpl_stream = tpl.stream(
        slaveof=slaveof, \
        maxmemory=maxmemory, \
        server=server, \
    )
    with NamedTemporaryFile('wb') as fp:
        tpl_stream.dump(fp)
        scp_file(ssh, fp.name, path)

