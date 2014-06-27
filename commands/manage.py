#!/usr/bin/python
#coding:utf-8

import click
import config
from utils.helper import params_check
from utils.tools import control_service

import logging

logger = logging.getLogger(__name__)

@click.argument('cluster')
@click.argument('service')
@click.argument('action', default='start')
@click.pass_context
def redis_service(ctx, cluster, service, action):
    params_check(ctx, config.REDIS, cluster)
    define = config.REDIS[cluster].get(service)
    if not define:
        ctx.fail('There is no %s define in Redis Cluster' % service)
    meta = define.pop('meta', {})
    keyname = meta.get('keyname')
    if action not in ['start', 'stop', 'restart']:
        ctx.fail('No support action %s' % action)
    r = 'slaves' if service == 'redis' else None
    manage_service(service, keyname, define, action, r)

def manage_service(service, keyname, define, action, r=None):
    for service_addr, values in define.iteritems():
        server_keyname = values.get('keyname', keyname)
        if not server_keyname:
            logger.error('No key for %s@%s' % (service, service_addr))
            continue
        control_service(
            service_addr, \
            server_keyname, service, \
            getattr(config, '%s_INITFILE_PATTERN' % service.upper()), \
            action=action, \
        )
        if r:
            sub_define = values.get(r, None)
            if sub_define:
                manage_service(service, server_keyname, sub_define, action, r)

