#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging

from utils.tools import activate_service, start_service, \
        scp_template_file, control_service
from utils.helper import get_ssh, get_address, Obj, output_logs, params_check

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def start_sentinel(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    sentinel = config.REDIS[cluster]['sentinel']
    do_control_sentinel(sentinel, 'stop')

@click.argument('cluster')
@click.pass_context
def stop_sentinel(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    sentinel = config.REDIS[cluster]['sentinel']
    do_control_sentinel(sentinel, 'stop')

@click.argument('cluster')
@click.pass_context
def restart_sentinel(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    sentinel = config.REDIS[cluster]['sentinel']
    do_control_sentinel(sentinel, 'restart')

@click.argument('cluster')
@click.pass_context
def deploy_sentinel(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    sentinel = config.REDIS[cluster]['sentinel']
    for server, values in sentinel.iteritems():
        keyname = values.get('keyname', None)
        home = values.get('home', None)
        if not keyname or not home:
            logger.error('There is no keyname or home defined for %s' % server)
            continue
        quorum = values.get('quorum', config.DEFAULT_SENTINEL_QUORUM)
        down_after_milliseconds = values.get(
            'down-after-milliseconds', config.DEFAULT_SENTINEL_DOWN_AFTER_MILLISECONDS
        )
        failover_timeout = values.get('failover-timeout', config.DEFAULT_SENTINEL_FAILOVER_TIMEOUT)
        parallel_syncs = values.get('parallel-syncs', config.DEFAULT_SENTINEL_PARALLEL_SYNCS)

        do_deploy_sentinel(
            server, keyname, home, \
            values['masters'], \
            quorum, down_after_milliseconds, \
            parallel_syncs, failover_timeout, \
        )

def do_control_sentinel(sentinel, action='start'):
    for service_addr, values in sentinel.iteritems():
        keyname = values.get('keyname', None)
        control_service(
            service_addr, \
            keyname, 'sentinel', \
            config.SENTINEL_INITFILE_PATTERN, \
            action=action, \
        )

def do_deploy_sentinel(
    server, keyname, home, masters, quorum, \
    down_after_milliseconds, parallel_syncs, \
    failover_timeout, \
):
    server, port = get_address(server)
    defines = generate_masters_config(
        masters, quorum, \
        down_after_milliseconds, parallel_syncs, \
        failover_timeout, \
    )
    config_and_install(server, port, keyname, home, defines)

def config_and_install(server, port, keyname, home, defines):
    etc_dir = os.path.join(home, 'etc')
    log_dir = os.path.join(home, 'log')
    run_dir = os.path.join(home, 'run')

    init = config.SENTINEL_INITFILE_PATTERN.format(port=port)
    etcfile = os.path.join(etc_dir, config.SENTINEL_ETCFILE_PATTERN.format(port=port))

    logfile = os.path.join(log_dir, config.SENTINEL_LOGFILE_PATTERN.format(port=port))
    pidfile = os.path.join(run_dir, config.SENTINEL_PIDFILE_PATTERN.format(port=port))

    ssh = get_ssh(server, keyname, config.ROOT)
    try:
        commands = 'mkdir -p %s %s %s %s' % (home, etc_dir, log_dir, run_dir)
        logger.debug(commands)
        _, err, retval = ssh.execute(commands, sudo=True)
        if retval != 0:
            logger.error('Create redis sentinel dirs failed')
            output_logs(logger.error, err)
            return

        scp_template_file(
            ssh, etcfile, config.SENTINEL_CONF, \
            port=port, home=home, pidfile=pidfile, \
            logfile=logfile, defines=defines, \
        )
        logger.info('Deploy config file in %s was done' % server)

        remote_path = os.path.join('/etc/init.d', init)
        scp_template_file(
            ssh, remote_path, config.SENTINEL_INIT, \
            pidfile=pidfile, etcfile=etcfile, \
            port=port, \
        )
        logger.info('Deploy init file in %s was done' % server)
        activate_service(ssh, init)
        start_service(ssh, init)
    except Exception:
        logger.exception('Install in %s failed' % server)
    else:
        logger.info('Install in %s was done' % server)
    finally:
        logger.info('Close connection to %s' % server)
        ssh.close()

def generate_masters_config(
    masters, quorum, \
    down_after_milliseconds, parallel_syncs, \
    failover_timeout, \
):
    id = 0
    for master, values in masters.iteritems():
        values = values or {}
        define = Obj()
        define.id = id
        define.ip, define.port = get_address(master)
        define.quorum = values.get('quorum', quorum)
        define.down_after_milliseconds = values.get('down_after_milliseconds', down_after_milliseconds)
        define.parallel_syncs = values.get('parallel_syncs', parallel_syncs)
        define.failover_timeout = values.get('failover_timeout', failover_timeout)
        yield define
        id += 1

