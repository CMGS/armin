#!/usr/bin/python
#coding:utf-8

import config
import logging
import paramiko
from utils import shell_escape

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

    def execute(self, command, sudo=False, shell=True):
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
        stdin, stdout, stderr = self.client.exec_command(command)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        return stdout, stderr, stdout.channel.recv_exit_status()

    def run_command(self, command, sudo=False, shell=True):
        logger.debug(command)
        out, err, retval = self.execute(command, sudo, shell)
        if retval != 0:
            for line in err:
                logger.debug(line.strip())
            logger.info('Run command failed')
            return
        for line in out:
            logger.debug(line.strip())
        logger.info('Run command succeeded')

    def get_transport(self):
        return self.client.get_transport()

if __name__ == "__main__":
    client = SSHClient(host='10.1.201.49', port=22, username='hunantv', password='hunantv123')
    try:
       ret = client.execute('dmesg', sudo=True)
       print "  ".join(ret["out"].readlines()), "  E ".join(ret["err"].readlines()), ret["retval"]()
    finally:
      client.close()

