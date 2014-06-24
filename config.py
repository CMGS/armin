#!/usr/bin/python
#coding:utf-8

import os
import yaml
from jinja2 import Environment, FileSystemLoader

DEBUG = True

ROOT = os.path.realpath(os.path.dirname(__file__))
KEY_DIR = os.path.join(ROOT, 'key')
SRC_DIR = os.path.join(ROOT, 'src')
ETC_DIR = os.path.join(ROOT, 'etc')

HOSTS = yaml.load(open('hosts.yaml'))
REDIS = yaml.load(open('redis.yaml'))

GET_CONF = Environment(loader=FileSystemLoader(ETC_DIR))

REMOTE_SCP_DIR = '/tmp'

SSH_TIMEOUT = 4
SUDO_PREFIX = "sudo -S -p ''"
SHELL = '/bin/bash -l -c'

NUTCRACKER_PATTERN = 'nutcracker-%s.tar.gz'
REDIS_PATTERN = 'redis-%s.tar.gz'
PUB_KEY_PATTERN = '%s.pub'

REDIS_CONF = 'redis.conf'
SENTINEL_CONF = 'sentinel.conf'

