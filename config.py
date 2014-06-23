#!/usr/bin/python
#coding:utf-8

import os
import yaml

DEBUG = True

ROOT = os.path.realpath(os.path.dirname(__file__))
KEY_DIR = os.path.join(ROOT, 'key')
SRC_DIR = os.path.join(ROOT, 'src')

HOSTS = yaml.load(open('hosts.yaml'))

REMOTE_SCP_DIR = '/tmp'

SSH_TIMEOUT = 4
SUDO_PREFIX = "sudo -S -p ''"
SHELL = '/bin/bash -l -c'

REDIS_PATTERN = 'redis-%s.tar.gz'
PUB_KEY_PATTERN = '%s.pub'

