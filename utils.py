#!/usr/bin/python
#coding:utf-8

import os
import config
import logging
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

class Obj(object): pass

def get_address(server):
    return server.split(':')

def render_lines(lines):
    p = lines.rfind('\n')
    return lines[p+1:], lines[:p+1].splitlines()

def get_path(ctx, d, key, dirname, pattern):
    value = d.get(key)
    if not value:
        ctx.fail('Key %s not exists' % key)
    path = os.path.join(dirname, pattern % value)
    if not os.path.exists(path):
        ctx.fail('Target file %s not exist' % path)
    return value, path

def get_group(ctx, group):
    if group == 'all':
        groups = config.HOSTS
    else:
        defs = config.HOSTS.get(group)
        if not defs:
            ctx.fail('%s not define in hosts.yaml' % group)
        groups = {group: defs}
    return groups

def shell_escape(string):
    """
    Escape double quotes, backticks and dollar signs in given ``string``.

    For example::

        >>> _shell_escape('abc$')
        'abc\\\\$'
        >>> _shell_escape('"')
        '\\\\"'
    """
    for char in ('"', '$', '`'):
        string = string.replace(char, '\%s' % char)
    return string

def scp_file(ssh, local_path, remote_path):
    from libs.scp import SCPClient
    scp = SCPClient(ssh.get_transport())
    scp.put(local_path, remote_path)

def extract_tar(ssh, remote_path, dst_path):
    command = 'tar xvf {remote_path} -C {dst_path}'
    command = command.format(
        remote_path=remote_path, dst_path=dst_path
    )
    buf = ''
    for lines in ssh.stream_execute(command):
        buf, lines = render_lines(buf + lines)
        map(logger.debug, lines)
    logger.info('Extract succeed')

def make_and_install(ssh, remote_path, configure=False):
    if not configure:
        command = 'cd {remote_path} && make install'
    else:
        command = 'cd {remote_path} && ./configure && make install'
    command = command.format(remote_path=remote_path)
    logger.debug(command)
    buf = ''
    for lines in ssh.stream_execute(command):
        buf, lines = render_lines(buf + lines)
        map(logger.debug, lines)
    logger.info('Make install succeed')

def get_ssh(server, keyname=None, username=config.ROOT, password=None):
    from libs.ssh import SSHClient
    if keyname:
        ssh = SSHClient(
            server, \
            username=username, \
            key_filename=os.path.join(config.KEY_DIR, keyname)
        )
    else:
        ssh = SSHClient(
            server, \
            username=username, \
            password=password, \
        )
    return ssh

def scp_temple_file(ssh, tpl_stream, remote_path):
    with NamedTemporaryFile('wb') as fp:
        tpl_stream.dump(fp)
        fp.flush()
        scp_file(ssh, fp.name, remote_path)

