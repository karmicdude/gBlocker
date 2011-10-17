#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

"""gBlocker - iptables rules generator

Usage:
gblocker [args]

-h, --help      show help message
-c config-file  use speciefed config file
-d dir          set blacklist dir
-o file         output file for iptables rules
-u              update blacklists
-n              don't generate rules
-r              refresh iptables
"""

import csv
import os
import ConfigParser
import sys
import getopt
import commands
import filecmp
import shutil
from blacklistreader import BlacklistReader


class UsageError(Exception):
    """Exception raised to print __doc__"""
    def __init__(self, msg='', forhelp=False):
        self.msg = msg
        self.forhelp = forhelp


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    configfile = '/etc/gblocker/config.ini'

    blacklist_dir = ''
    output_file = ''
    make_rules = True
    update_lists = False
    refresh_iptables = False

    conf = ConfigParser.ConfigParser()

    try:
        try:
            opts, args = getopt.getopt(argv, 'hc:d:uno:r', ['help'])
        except getopt.error as e:
            raise UsageError(e)

        for o, a in opts:
            if o in ['-h', '--help']:
                raise UsageError(forhelp=True)
            if o in ['-c']:
                configfile = a
            if o in ['-d']:
                blacklist_dir = a
            if o in ['-o']:
                output_file = a
            if o in ['-n']:
                make_rules = False
            if o in ['-u']:
                update_lists = True
            if o in ['-r']:
                refresh_iptables = True

        if not (os.path.exists(configfile) and os.path.isfile(configfile)):
            print 'Error: Bad config file!'
            exit(1)
        conf.read(configfile)
        if blacklist_dir:
            conf.set('General', 'blacklist_dir', blacklist_dir)
        if output_file:
            conf.set('General', 'output_file', output_file)

        if update_lists:
            print 'Updating blacklists...'
            updateLists(conf)

        blacklist = readLists(conf)

        if make_rules:
            print 'Generating rules...'
            makeRules(conf, blacklist)

        if refresh_iptables:
            print 'Refreshing iptables...'
            refreshIptables(conf)

        print 'Done.'
    except UsageError as e:
        if e.forhelp:
            print __doc__
        else:
            print e.msg
            print 'Use \'gblocker --help\''

def updateLists(conf):
    """Download new blacklists"""
    bldir = conf.get('General', 'blacklist_dir')
    for i, v in conf.items('wget'):
        if 'wget' in v:
            v = v.replace('%directory%', bldir)
            commands.getoutput(v)

def readLists(conf):
    """Parse blacklists"""
    try:
        bldir = conf.get('General', 'blacklist_dir')
    except ConfigParser.NoOptionError:
        print 'Error: No blacklist_dir selected!'
        exit(1)

    blacklist = []
    for f in os.listdir(bldir):
        reader = BlacklistReader.getReader(os.path.join(bldir, f))
        if reader:
            blacklist.extend([ip for ip in reader.list if not ip in blacklist])

    blacklist.sort()
    return blacklist

def makeRules(conf, blacklist):
    """Generate iptables rules"""
    try:
        rules = conf.get('General', 'output_file')
    except ConfigParser.NoOptionError:
        print 'Error: No output_file selected!'
        exit(1)

    try:
        defaults = conf.get('iptables', 'defaults')
    except ConfigParser.NoOptionError:
        print 'Error: No defaults file selected!'
        exit(1)

    try:
        shutil.move(rules, rules+'.old')
    except IOError:
        pass

    out = open(rules, 'w')
    try:
        defaults = open(defaults, 'r')
    except IOError:
        print 'Error: No defaults file!'
        exit(1)

    tables = conf.get('iptables', 'rules', '').split(',')
    rules = {}
    for t in tables:
        try:
            table = conf.get(t, 'table')
            chain = conf.get(t, 'chain')
            options = conf.get(t, 'options')
        except ConfigParser.NoSectionError:
            continue

        rules[table] = []
        for ip in blacklist:
            if len(ip) >= 7:
                rules[table].append('-A {0} -s {1} {2}'.format(chain, ip, options))

    out.write(defaults.read())

    for t, r in rules.items():
        print>>out, '*' + t
        for line in r:
            print>>out, line
        print>>out, 'COMMIT'

    out.close()

def refreshIptables(conf):
    """Apply new rules to iptables"""
    try:
        rules = conf.get('General', 'output_file')
    except ConfigParser.NoOptionError:
        print 'Error: No output_file selected!'
        exit(1)

    try:
        if filecmp.cmp(rules, rules+'.old'):
            print 'No new rules!'
            return
        else:
            raise OSError()
    except OSError:
        print commands.getoutput('iptables-restore < ' + rules)


if __name__ == '__main__':
    sys.exit(main())
