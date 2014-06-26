#!/usr/bin/python
#coding:utf-8

import config
import select
import logging
import paramiko
from utils.helper import shell_escape, output_logs

logger = logging.getLogger(__name__)

class SSHClient(object):
    "A wrapper of paramiko.SSHClient"

    def __init__(self, host, username, password=None, port=22, key_filename=None, passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            host, port, \
            username=username, \
            password=password, \
            key_filename=key_filename, \
            timeout=config.SSH_TIMEOUT, \
        )

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def parse_command(self, command, sudo=False, shell=True):
        feed_password = False
        c = []

        if sudo and self.username != "root":
            c.append(config.SUDO_PREFIX)
            feed_password = self.password is not None and len(self.password) > 0

        if shell:
            c.append(config.SHELL)
            c.append('"%s"' % shell_escape(command))
        else:
            c.append(command)

        command = ' '.join(c)
        return feed_password, command

    def execute(self, command, sudo=False, shell=True, data=None):
        feed_password, command = self.parse_command(command, sudo, shell)
        stdin, stdout, stderr = self.client.exec_command(command)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        if data:
            stdin.write(data)
            stdin.flush()
        return stdout, stderr, stdout.channel.recv_exit_status()

    def stream_execute(self, command, sudo=False, shell=True, bufsize=-1):
        feed_password, command = self.parse_command(command, sudo, shell)
        chan = self.client.get_transport().open_session()
        chan.exec_command(command)
        stdin = chan.makefile('wb', bufsize)
        stderr = chan.makefile_stderr('r', bufsize)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        while True:
            rl, wl, xl = select.select([chan],[],[],0.0)
            if chan.exit_status_ready():
                break
            if len(rl) > 0:
                yield chan.recv(1024)
        status = chan.recv_exit_status()
        if status != 0:
            logger.error('Command execute failed')
            output_logs(logger.error, stderr.readlines())

    def get_transport(self):
        return self.client.get_transport()

if __name__ == "__main__":
    client = SSHClient(host='10.1.201.49', port=22, username='hunantv', password='hunantv123')
    try:
       ret = client.execute('dmesg', sudo=True)
       print "  ".join(ret["out"].readlines()), "  E ".join(ret["err"].readlines()), ret["retval"]()
    finally:
      client.close()

