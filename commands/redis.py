#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging

from utils.tools import scp_template_file
from utils.helper import get_ssh, get_address, output_logs, params_check

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def deploy_redis(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    redis = config.REDIS[cluster]['redis']
    meta = redis.pop('meta', {})
    do_deploy(cluster, redis, **meta)

def do_deploy(
    cluster, redis, \
    keyname=None, version=None, \
    maxmemory=config.DEFAULT_REDIS_MAXMEMORY, \
    home=config.DEFAULT_REDIS_HOME, \
    slaveof=None, \
):
    for service_addr, values in redis.iteritems():
        values = values or {}
        server_keyname = values.get('keyname', keyname)
        service_version = values.get('version', version)
        if not server_keyname or not service_version:
            logger.error('There is no keyname or version defined for %s' % service_addr)
            continue
        logger.info('Connect to master %s' % service_addr)
        service_home = values.get('home', home)
        service_maxmem = values.get('maxmemory', maxmemory)
        install_redis(service_addr, server_keyname, service_version, service_maxmem, service_home, slaveof)
        slaves = values.get('slaves', None)
        if slaves:
            do_deploy(cluster, slaves, server_keyname, service_version, service_maxmem, service_home, service_addr)

def install_redis(service_addr, keyname, version, maxmemory, home, slaveof=None):
    server, port = get_address(service_addr)

    dst_dirname = config.REDIS_PATTERN.rstrip('.tar.gz') % version
    remote_path = os.path.join(config.REMOTE_SCP_DIR, dst_dirname)

    ssh = get_ssh(server, keyname, config.ROOT)
    try:
        send_config_file(ssh, maxmemory, server, port, remote_path, slaveof)
        config_and_install(ssh, remote_path, home, port)
    except Exception:
        logger.exception('Install in %s failed' % server)
    else:
        logger.info('Install in %s was done' % server)
    finally:
        logger.info('Close connection to %s' % server)
        ssh.close()

def send_config_file(ssh, maxmemory, server, port, remote_path, slaveof=None):
    slaveof = 'slaveof {0} {1}'.format(*get_address(slaveof)) if slaveof else ''
    remote_path = os.path.join(remote_path, config.REDIS_CONF)
    scp_template_file(
        ssh, remote_path, config.REDIS_CONF, \
        slaveof=slaveof, \
        maxmemory=maxmemory, \
        server=server, \
        port=port, \
    )

def config_and_install(ssh, remote_path, home, port):
    path = os.path.join(remote_path, 'utils')
    conf_dir = os.path.join(home, 'etc')
    log_dir = os.path.join(home, 'log')
    data_dir = os.path.join(home, 'data')
    commands = 'mkdir -p %s %s %s %s' % (home, conf_dir, log_dir, data_dir)
    logger.debug(commands)
    _, err, retval = ssh.execute(commands, sudo=True)
    if retval != 0:
        logger.error('Create redis dirs failed')
        output_logs(logger.error, err)
        return
    conf_file = os.path.join(conf_dir, '%s.conf' % port)
    log_file = os.path.join(log_dir, '%s.log' % port)
    data = '%s\n%s\n%s\n%s\n\n\n\n' % (port, conf_file, log_file, data_dir)
    logger.debug(data.strip('\n'))
    commands = 'cd %s && sh install_server.sh' % path
    logger.debug(commands)
    out, err, retval = ssh.execute(commands, sudo=True, shell=False, data=data)
    if retval != 0:
        logger.error('Config redis failed')
        output_logs(logger.error, err)
        return
    output_logs(logger.debug, out)
    logger.info('Config redis succeed')

