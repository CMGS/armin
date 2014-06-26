#!/usr/bin/python
#coding:utf-8

import logging
from tempfile import NamedTemporaryFile
from utils.helper import output_logs, get_lines, scp_file

logger = logging.getLogger(__name__)

def scp_template_file(ssh, tpl_stream, remote_path):
    with NamedTemporaryFile('wb') as fp:
        tpl_stream.dump(fp)
        fp.flush()
        scp_file(ssh, fp.name, remote_path)

def extract_tar(ssh, remote_path, dst_path):
    command = 'tar xvf {remote_path} -C {dst_path}'
    command = command.format(
        remote_path=remote_path, dst_path=dst_path
    )
    buf = ''
    for lines in ssh.stream_execute(command):
        buf, lines = get_lines(buf + lines)
        output_logs(logger.debug, lines)
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
        buf, lines = get_lines(buf + lines)
        output_logs(logger.debug, lines)
    logger.info('Make install succeed')

def activate_service_by_chkconfig(ssh, init):
    commands = 'chkconfig --add {init} && chkconfig --level 345 {init}'.format(init=init)
    out, err, retval = ssh.execute(commands, sudo=True)
    if retval != 0:
        logger.error('chkconfig add %s failed' % init)
        output_logs(logger.error, err)
        return
    output_logs(logger.debug, out)
    logger.info('Successfully added %s service to chkconfig and runlevels 345' % init)

def activate_service_by_updaterc(ssh, init):
    commands = 'update-rc.d {init} defaults'.format(init=init)
    out, err, retval = ssh.execute(commands, sudo=True)
    if retval != 0:
        logger.error('update-rc add %s failed' % init)
        output_logs(logger.error, err)
        return
    output_logs(logger.debug, out)
    logger.info('Successfully added %s to update-rc' % init)

def activate_service(ssh, init):
    commands = 'command -v chkconfig'
    _, _, retval = ssh.execute(commands, sudo=True)
    if retval == 0:
        activate_service_by_chkconfig(ssh, init)
        return
    commands = 'command -v update-rc.d'
    _, _, retval = ssh.execute(commands, sudo=True)
    if retval == 0:
        activate_service_by_updaterc(ssh, init)
        return
    logger.error('No supported init tools found')

