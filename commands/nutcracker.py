#!/usr/bin/python
#coding:utf-8

import os
import yaml
import click
import config
import logging
from tempfile import NamedTemporaryFile

from utils.helper import get_ssh, get_address, \
    output_logs, scp_file, params_check
from utils.tools import activate_service, start_service, \
    scp_template_file, control_service

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def start_nutcracker(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    nutcracker = config.REDIS[cluster]['nutcracker']
    proxy = nutcracker.pop('proxy')
    do_control_nutcracker(proxy)

@click.argument('cluster')
@click.pass_context
def stop_nutcracker(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    nutcracker = config.REDIS[cluster]['nutcracker']
    proxy = nutcracker.pop('proxy')
    do_control_nutcracker(proxy, action='stop')

@click.argument('cluster')
@click.pass_context
def restart_nutcracker(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    nutcracker = config.REDIS[cluster]['nutcracker']
    proxy = nutcracker.pop('proxy')
    do_control_nutcracker(proxy, action='restart')

@click.argument('cluster')
@click.pass_context
def deploy_nutcracker(ctx, cluster):
    params_check(ctx, config.REDIS, cluster)
    nutcracker = config.REDIS[cluster]['nutcracker']
    proxy = nutcracker.pop('proxy')
    for server, values in proxy.iteritems():
        keyname = values['keyname']
        stats_port = values.pop('stats_port', config.DEFAULT_NUTCRACKER_STATS_PORT)
        home = values.pop('home', config.DEFAULT_NUTCRACKER_HOME)
        mbuf_size = values.pop('mbuf_size', config.DEFAULT_NUTCRACKER_MBUF_SIZE)

        do_deploy_nutcracker(
            cluster, nutcracker, server, values, \
            keyname, home, stats_port, mbuf_size, \
        )

def do_deploy_nutcracker(
    cluster, nutcracker, server, values, \
    keyname, home, stats_port, mbuf_size, \
):

    defines = {}
    for k, v in nutcracker.iteritems():
        defines[k] = values.get(k) or v
    defines['listen'] = server
    defines = {cluster:defines}

    server, port = get_address(server)
    config_and_install(server, port, keyname, home, defines, stats_port, mbuf_size)

def config_and_install(server, port, keyname, home, defines, stats_port, mbuf_size):
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

        with NamedTemporaryFile('wb') as fp:
            yaml.safe_dump(defines, fp, default_flow_style=False)
            fp.flush()
            scp_file(ssh, fp.name, etcfile)
        logger.debug(etcfile)
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

def do_control_nutcracker(proxy, action='start'):
    for service_addr, values in proxy.iteritems():
        keyname = values.get('keyname', None)
        control_service(
            service_addr, \
            keyname, 'nutcracker', \
            config.NUTCRACKER_INITFILE_PATTERN, \
            action=action, \
        )

