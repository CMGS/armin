#!/usr/bin/python
#coding:utf-8

import os
import config

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
