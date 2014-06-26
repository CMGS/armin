#!/usr/bin/python
#coding:utf-8

import os
import yaml
import click
import config
import logging
from tempfile import NamedTemporaryFile

from utils.helper import get_ssh, get_address, output_logs, scp_file
from utils.tools import activate_service, scp_template_file

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.pass_context
def start_nutcracker(ctx, cluster):
    cluster_name = cluster
    cluster = config.REDIS.get(cluster)
    if not cluster:
        ctx.fail('%s not define' % cluster)

    nutcracker = cluster['nutcracker']

    proxy = nutcracker.pop('proxy')

    for server, values in proxy.iteritems():

        keyname = values['keyname']
        stats_port = values.pop('stats_port', config.DEFAULT_NUTCRACKER_STATS_PORT)
        home = values.pop('home', config.DEFAULT_NUTCRACKER_HOME)
        mbuf_size = values.pop('mbuf_size', config.DEFAULT_NUTCRACKER_MBUF_SIZE)

        do_deploy_nutcracker(
            cluster_name, nutcracker, server, values, \
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
    deploy_nutcracker(server, port, keyname, home, defines, stats_port, mbuf_size)

def deploy_nutcracker(server, port, keyname, home, defines, stats_port, mbuf_size):
    etc_dir = os.path.join(home, 'etc')
    log_dir = os.path.join(home, 'log')
    run_dir = os.path.join(home, 'run')

    init = config.NUTCRACKER_INITFILE_PATTERN.format(port=port)
    init_file = os.path.join('/etc/init.d', init)
    etc_file = os.path.join(etc_dir, config.NUTCRACKER_ETCFILE_PATTERN.format(port=port))

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
            scp_file(ssh, fp.name, etc_file)
        logger.debug(etc_file)
        logger.info('Deploy config file in %s was done' % server)

        tpl = config.GET_CONF.get_template(config.NUTCRACKER_INIT)
        tpl_stream = tpl.stream(
            pidfile=pidfile, \
            etc_file=etc_file, \
            logfile=logfile, \
            stats_port=stats_port, \
            mbuf_size=mbuf_size, \
        )
        scp_template_file(ssh, tpl_stream, init_file)
        logger.debug(init_file)
        logger.info('Deploy init file in %s was done' % server)

        commands = 'chmod +x {init_file} && {init_file} start'.format(init_file=init_file)
        logger.debug(commands)
        out, err, retval = ssh.execute(commands, sudo=True)
        if retval != 0:
            logger.error('Start redis sentinel failed')
            output_logs(logger.error, err)
            return
        output_logs(logger.debug, out)
        activate_service(ssh, init)
    except Exception:
        logger.exception('Install in %s failed' % server)
    else:
        logger.info('Install in %s was done' % server)
    finally:
        logger.info('Close connection to %s' % server)
        ssh.close()

