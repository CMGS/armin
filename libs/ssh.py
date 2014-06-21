#!/usr/bin/python
#coding:utf-8

import config
import paramiko
from utils import shell_escape

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
            timeout=self.TIMEOUT, \
        )

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, command, sudo=False):
        feed_password = False
        if sudo and self.username != "root":
            command = config.SUDO_PREFIX + config.SHELL + '"%s"' % shell_escape(command)
            feed_password = self.password is not None and len(self.password) > 0
        stdin, stdout, stderr = self.client.exec_command(command)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        return {
            'out': stdout.readlines(), \
            'err': stderr.readlines(), \
            'retval': stdout.channel.recv_exit_status(), \
        }

    def get_transport(self):
        return self.client.get_transport()

if __name__ == "__main__":
    client = SSHClient(host='10.1.201.49', port=22, username='hunantv', password='hunantv123')
    try:
       ret = client.execute('dmesg', sudo=True)
       print "  ".join(ret["out"]), "  E ".join(ret["err"]), ret["retval"]
    finally:
      client.close()

