#!/usr/bin/python
#coding:utf-8

import config

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
