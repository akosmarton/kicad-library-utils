#!/usr/bin/env python

from __future__ import print_function

import argparse
from kicad_mod import *
from print_color import *
from rules import *

parser = argparse.ArgumentParser()
parser.add_argument('kicad_mod_files', nargs='+')
parser.add_argument('--fix', help='fix the violations if possible', action='store_true')
parser.add_argument('--nocolor', help='does not use colors to show the output', action='store_true')
parser.add_argument('-v', '--verbose', help='show status of all modules and extra information about the violation', action='store_true')
args = parser.parse_args()

printer = PrintColor(use_color = not args.nocolor)

# get all rules
all_rules = []
for f in dir():
    if f.startswith('rule'):
        all_rules.append(globals()[f].Rule)

for filename in args.kicad_mod_files:
    module = KicadMod(filename)
    printer.green('module: %s' % module.name)

    for rule in all_rules:
        rule = rule(module)
        if rule.check():
            printer.yellow(rule.name)
            if args.verbose:
                printer.light_blue(rule.description)
