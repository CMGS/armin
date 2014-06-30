#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging

from utils.tools import activate_service, start_service, \
        scp_template_file
from utils.helper import get_ssh, get_address, Obj, output_logs, params_check

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def deploy_sentinel(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    sentinel = config.REDIS[cluster]['sentinel']
    meta = sentinel.pop('meta', {})
    do_deploy(sentinel, **meta)

def do_deploy(
    cluster, sentinel, keyname=None, home=None, \
    quorum=config.DEFAULT_SENTINEL_QUORUM, \
    down_after_milliseconds=config.DEFAULT_SENTINEL_DOWN_AFTER_MILLISECONDS, \
    failover_timeout=config.DEFAULT_SENTINEL_FAILOVER_TIMEOUT, \
    parallel_syncs=config.DEFAULT_SENTINEL_PARALLEL_SYNCS, \
):
    for service_addr, values in sentinel.iteritems():
        server_keyname = values.get('keyname', keyname)
        service_home = values.get('home', home)
        if not server_keyname or not service_home:
            logger.error('There is no keyname or home defined for %s' % service_addr)
            continue
        service_quorum = values.get('quorum', quorum)
        service_down_after_milliseconds = values.get(
            'down-after-milliseconds', down_after_milliseconds
        )
        service_failover_timeout = values.get('failover_timeout', failover_timeout)
        service_parallel_syncs = values.get('parallel-syncs', parallel_syncs)

        install_sentinel(
            service_addr, server_keyname, service_home, \
            values['masters'], \
            service_quorum, service_down_after_milliseconds, \
            service_parallel_syncs, service_failover_timeout, \
        )

def install_sentinel(
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

