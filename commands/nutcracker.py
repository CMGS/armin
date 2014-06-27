#!/usr/bin/python
#coding:utf-8

import os
import click
import config
import logging

from utils.helper import get_ssh, get_address, \
    output_logs, params_check
from utils.tools import activate_service, start_service, \
    scp_template_file

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def deploy_nutcracker(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    nutcracker = config.REDIS[cluster]['nutcracker']
    meta = nutcracker.pop('meta', {})
    do_deploy_nutcracker(cluster, nutcracker, **meta)

def do_deploy_nutcracker(
    cluster, nutcracker, \
    keyname=None, home=config.DEFAULT_NUTCRACKER_HOME, \
    stats_port=config.DEFAULT_NUTCRACKER_STATS_PORT, \
    mbuf_size=config.DEFAULT_NUTCRACKER_MBUF_SIZE, \
    masters=[], \
):
    for service_addr, values in nutcracker.iteritems():
        values = values or {}
        server_keyname = values.get('keyname', keyname)
        service_home = values.get('home', home)
        if not server_keyname or not service_home:
            logger.error('There is no keyname or home defined for %s' % service_addr)
            continue
        service_stats_port = values.get('stats_port', stats_port)
        service_mbuf_size = values.get('mbuf_size', mbuf_size)
        service_masters = values.get('masters', masters)

        config_and_install(
            cluster, service_addr, server_keyname, \
            service_home, service_stats_port, \
            service_mbuf_size, service_masters, \
        )

def config_and_install(cluster, service_addr, keyname, home, stats_port, mbuf_size, servers):
    server, port = get_address(service_addr)
    etc_dir = os.path.join(home, 'etc')
    log_dir = os.path.join(home, 'log')
    run_dir = os.path.join(home, 'run')

    init = config.NUTCRACKER_INITFILE_PATTERN.format(port=port)
    etcfile = os.path.join(etc_dir, config.NUTCRACKER_ETCFILE_PATTERN.format(port=port))

    logfile = os.path.join(log_dir, config.NUTCRACKER_LOGFILE_PATTERN.format(port=port))
    pidfile = os.path.join(run_dir, config.NUTCRACKER_PIDFILE_PATTERN.format(port=port))

    ssh = get_ssh(server, keyname, config.ROOT)

    try:
        commands = 'mkdir -p %s %s %s %s' % (home, etc_dir, log_dir, run_dir)
        logger.debug(commands)
        _, err, retval = ssh.execute(commands, sudo=True)
        if retval != 0:
            logger.error('Create nutcracker dirs failed')
            output_logs(logger.error, err)
            return

        scp_template_file(
            ssh, etcfile, config.NUTCRACKER_CONF, \
            cluster=cluster, \
            addr=service_addr, \
            rds=servers, \
        )
        logger.info('Deploy config file in %s was done' % server)

        remote_path = os.path.join('/etc/init.d', init)
        scp_template_file(
            ssh, remote_path, config.NUTCRACKER_INIT, \
            pidfile=pidfile, etcfile=etcfile, \
            logfile=logfile, stats_port=stats_port, \
            mbuf_size=mbuf_size, \
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

