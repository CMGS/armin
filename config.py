#!/usr/bin/python
#coding:utf-8

import os
import yaml
from jinja2 import Environment, FileSystemLoader

DEBUG = True
ROOT = 'root'

ROOT_DIR = os.path.realpath(os.path.dirname(__file__))
KEY_DIR = os.path.join(ROOT_DIR, 'key')
SRC_DIR = os.path.join(ROOT_DIR, 'src')
ETC_DIR = os.path.join(ROOT_DIR, 'etc')

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
REDIS_INITFILE_PATTERN = 'redis_{port}'
DEFAULT_REDIS_MAXMEMORY = 16106127360
DEFAULT_REDIS_HOME = '/tmp'

SENTINEL_CONF = 'sentinel.conf'
SENTINEL_INIT = 'sentinel.init'
SENTINEL_INITFILE_PATTERN = 'sentinel_{port}'
SENTINEL_ETCFILE_PATTERN = 'sentinel_{port}.conf'
SENTINEL_LOGFILE_PATTERN = 'sentinel_{port}.log'
SENTINEL_PIDFILE_PATTERN = 'sentinel_{port}.pid'

DEFAULT_SENTINEL_HOME = '/tmp'
DEFAULT_SENTINEL_QUORUM = 2
DEFAULT_SENTINEL_DOWN_AFTER_MILLISECONDS = 60000
DEFAULT_SENTINEL_PARALLEL_SYNCS = 1
DEFAULT_SENTINEL_FAILOVER_TIMEOUT = 180000

NUTCRACKER_INIT = 'nutcracker.init'
NUTCRACKER_INITFILE_PATTERN = 'nutcracker_{port}'
NUTCRACKER_ETCFILE_PATTERN = 'nutcracker_{port}.yml'
NUTCRACKER_LOGFILE_PATTERN = 'nutcracker_{port}.log'
NUTCRACKER_PIDFILE_PATTERN = 'nutcracker_{port}.pid'

DEFAULT_NUTCRACKER_STATS_PORT = 22222
DEFAULT_NUTCRACKER_HOME = '/tmp'
DEFAULT_NUTCRACKER_MBUF_SIZE = 16384
