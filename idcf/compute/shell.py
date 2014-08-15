#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import urllib
import os
import client
import argparse
import simplejson
import codecs
import csv
import StringIO
from lxml import etree
from prettytable import PrettyTable
from pkg_resources import resource_string

VERSION = '0.9.0'

API_REFS_JSON = resource_string('idcf.compute', 'apirefs.json')
API_REFS = simplejson.loads(API_REFS_JSON)

class ShellCommand(object):
    """コマンドのベースクラス
    """
    def options(self):
        return list()

    def execute(self, args):
        d = dict(vars(args))
        command = d.pop("command_class")
        fields = d.pop("table")

        xml = d.pop("xml")
        if xml:
            d['response'] = 'xml'
        else:
            d['response'] = 'json'

        csv_fields = d.pop("csv")
        no_headers = d.pop("noheaders")

        for k,v in d.items():
            if v is None:
                del(d[k])

        retval = client.connect().get(command.__name__,d)

        return retval, fields, xml, csv_fields, no_headers

def arg(*args,**kw):
    return (args, kw)

class IdcfShell(object):
    def __init__(self):
        self.arg_parser = argparse.ArgumentParser(
            prog = 'idcf-compute-api',
            #usage='%(prog)s [-h]',
            )
        self.arg_parser.add_argument('-v','--version', action='version', version="%(prog)s v"+VERSION)
        self.register_commands()

    def register_commands(self):
        """コマンドのサブクラスを登録する
        """
        cmd_parsers = self.arg_parser.add_subparsers()
        commands = self.create_commands()
        for cmd in commands:
            help = (cmd.__doc__ or "no help").strip().splitlines()[0]
            cmd_parser = cmd_parsers.add_parser(cmd.__name__, help=help)
            for (args, kw) in cmd().options():
                cmd_parser.add_argument(*args, **kw)
            cmd_parser.set_defaults(command_class=cmd)

    def create_commands(self):
        """ShellCommadサブクラスを生成する
        """
        commands = []
        for index, desc in enumerate(API_REFS):
            key = desc["name"]
            command = type(key.encode("utf-8"),(ShellCommand,),{"__doc__":desc["help"], "index":index})
            def options(self):
                def opt_required(required):
                    if required == "true":
                        return True
                    else:
                        return False
                retval = [arg(opt["option"],required=opt_required(opt["required"]),
                            help=opt["help"])
                        for opt in API_REFS[self.index]["options"]]

                retval.append(arg("-t","--table",help="displaying tabular format",
                                  nargs="?", const="*"))
                retval.append(arg("-x","--xml",help="displaying xml format",
                                  nargs="?", const="*"))
                retval.append(arg("-c","--csv",help="displaying csv format",
                                  nargs="?", const="*"))
                retval.append(arg("--noheaders",help="suppress csv header",
                                  action="store_true"))
                return retval
            setattr(command,"options",options)
            commands.append(command)
        return commands

    def execute(self,raw_args,shell=False):
        args = self.arg_parser.parse_args(raw_args)
        command = args.command_class()
        retval,fields,xml,csv_fields,no_headers = command.execute(args)
        if shell:
            print_pretty(retval,fields,xml,csv_fields,no_headers)
        else:
            return retval

def print_pretty(retval,fields,xml,csv_fields,no_headers):
    if not retval:
        return
    elif xml:
        return print_xml(retval)
    elif fields:
        res = retval.get(retval.keys()[0])
        count = res.get("count")
        if not count:
            return print_dict(res,fields)
        else:
            res.pop("count")
            return print_list(res,fields)
    elif csv_fields:
        res = retval.get(retval.keys()[0])
        count = res.get("count")
        if not count:
            return print_dict_csv(res,csv_fields,no_headers)
        else:
            res.pop("count")
            return print_list_csv(res,csv_fields,no_headers)
    else:
        return print_json(retval)

def print_xml(xml):
    root = etree.XML(xml)
    print etree.tostring(root,xml_declaration=True,
                         pretty_print=True,encoding='utf-8')

def print_json(json):
    print simplejson.dumps(json,sort_keys=True, indent=2)


def get_csv_writer():
    data = StringIO.StringIO()
    writer = csv.writer(data,quoting=csv.QUOTE_NONNUMERIC)
    return data,writer

def print_dict_csv(obj,fields,no_headers):
    if not obj:
        print "no data found"
    else:
        headers = and_headers(obj,fields)
        if not headers:
            headers = obj.keys()

        data,writer = get_csv_writer()
        if not no_headers:
            writer.writerow(headers)
        writer.writerow([obj.get(k) for k in headers])
        print data.getvalue()

def print_list_csv(res,fields,no_headers):
    rows_key = res.keys()[0]
    rows = res.get(rows_key)
    for i,obj in enumerate(rows):
        if i < 1:
            if fields:
                headers = and_headers(obj,fields)
                if not headers:
                    headers = obj.keys()
            else:
                headers = obj.keys()

            data,writer = get_csv_writer()
            if not no_headers:
                writer.writerow(headers)
        writer.writerow([obj.get(k) for k in headers])
    print data.getvalue()

def and_headers(obj,fields):
    return list(set([ f.strip() for f in fields.split(',')]) & set(obj.keys()))

def print_dict(obj,fields):
    if not obj:
        print "no data found"
    else:
        headers = and_headers(obj,fields)
        if not headers:
            headers = obj.keys()
        pt = PrettyTable(headers)
        pt.add_row( [obj.get(k) for k in headers])
        pt.printt(sortby=headers[0])

def print_list(res,fields):
    rows_key = res.keys()[0]
    rows = res.get(rows_key)
    for i,obj in enumerate(rows):
        if i < 1:
            if fields:
                headers = and_headers(obj,fields)
                if not headers:
                    headers = obj.keys()
            else:
                headers = obj.keys()

            pt = PrettyTable(headers)
            [pt.set_field_align("%s"%h,"l") for h in headers]
        pt.add_row( [obj.get(k) for k in headers])

    pt.printt(sortby=headers[0])

def main():
    IdcfShell().execute(sys.argv[1:],True)
