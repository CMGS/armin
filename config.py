#!/usr/bin/python
#coding:utf-8

import os
import yaml

DEBUG = True

ROOT = os.path.realpath(os.path.dirname(__file__))
KEY_DIR = os.path.join(ROOT, 'key')
SRC_DIR = os.path.join(ROOT, 'src')

REDIS_FILE_NAME = 'redis-stable.tar.gz'
REDIS_FILE_PATH = os.path.join(SRC_DIR, REDIS_FILE_NAME)

HOSTS = yaml.load(open('hosts.yaml'))

SSH_TIMEOUT = 4
SUDO_PREFIX = "sudo -S -p ''"
SHELL = '/bin/bash -l -c'
