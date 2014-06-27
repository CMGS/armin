#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging
from utils.helper import get_ssh, get_address, output_logs
from utils.tools import scp_template_file, stop_service, start_service

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def deploy_redis(ctx, cluster):
    cluster = config.REDIS.get(cluster)
    if not cluster:
        ctx.fail('%s not define' % cluster)

    redis = cluster['redis']

    do_deploy_redis(redis, config.DEFAULT_REDIS_HOME, config.DEFAULT_REDIS_MAXMEMORY)

@click.argument('cluster')
@click.pass_context
def start_redis(ctx, cluster):
    cluster = config.REDIS.get(cluster)
    if not cluster:
        ctx.fail('%s not define' % cluster)

    redis = cluster['redis']
    do_start_redis(redis)

@click.argument('cluster')
@click.pass_context
def stop_redis(ctx, cluster):
    cluster = config.REDIS.get(cluster)
    if not cluster:
        ctx.fail('%s not define' % cluster)

    redis = cluster['redis']
    do_stop_redis(redis)

def do_start_redis(redis, keyname=None):
    for server, values in redis.iteritems():
        server, port = get_address(server)
        keyname = values.get('keyname', keyname)
        init = config.REDIS_INITFILE_PATTERN.format(port=port)
        ssh = get_ssh(server, keyname, config.ROOT)
        try:
            start_service(ssh, init)
        except Exception:
            logger.exception('Start redis in %s failed' % server)
        else:
            logger.info('Start redis in %s was done' % server)
        finally:
            logger.info('Close connection to %s' % server)
            ssh.close()
        slaves = values.get('slaves', None)
        if slaves:
            do_start_redis(slaves, keyname)

def do_stop_redis(redis, keyname=None):
    for server, values in redis.iteritems():
        server, port = get_address(server)
        keyname = values.get('keyname', keyname)
        init = config.REDIS_INITFILE_PATTERN.format(port=port)
        ssh = get_ssh(server, keyname, config.ROOT)
        try:
            stop_service(ssh, init)
        except Exception:
            logger.exception('Stop redis in %s failed' % server)
        else:
            logger.info('Stop redis in %s was done' % server)
        finally:
            logger.info('Close connection to %s' % server)
            ssh.close()
        slaves = values.get('slaves', None)
        if slaves:
            do_stop_redis(slaves, keyname)

def do_deploy_redis(redis, home, maxmemory, keyname=None, version=None, slaveof=None):
    for server, values in redis.iteritems():
        values = values or {}
        keyname = values.get('keyname', keyname)
        version = values.get('version', version)
        if not keyname or not version:
            logger.error('There is no keyname or version defined for %s' % server)
            continue
        logger.info('Connect to master %s' % server)
        home = values.get('home', home)
        maxmemory = values.get('maxmemory', maxmemory)
        install_redis(server, keyname, version, maxmemory, home, slaveof)
        slaves = values.get('slaves', None)
        if slaves:
            do_deploy_redis(slaves, home, maxmemory, keyname, version, server)

def install_redis(server, keyname, version, maxmemory, home, slaveof=None):
    server, port = get_address(server)

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

