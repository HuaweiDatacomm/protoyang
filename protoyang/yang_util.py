#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright (C) 2021. Huawei Technologies Co., Ltd. All rights reserved.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License, Version 2.0 for more details.
import os
import io
import logging
import re
import sys
import traceback

from pyang.context import Context
from pyang.repository import FileRepository
import pyang

ERR_TYPE_GRAMMA = "Gramma"
ERR_TYPE_LOST = "Lost"
ERR_INFO = {
    # yang file it self has grammatical errors, use pyang check get detailed error information
    ERR_TYPE_GRAMMA: "***parse***: [yang file {0} has grammatical errors] Error 1",
    # yang module declared in white list, but correspond yang file not exists
    ERR_TYPE_LOST: "***check***: [yang file {0} doesn't exists] Erro 1",
}
ERR_REPORT_STAT = {
    ERR_TYPE_GRAMMA: [],
    ERR_TYPE_LOST: []
}
start_error = r"#########yang_Error_start##########"
end_error = r"#######yang_Error_end##########"


def init_ctx(path='./yang'):
    repos = FileRepository(path)
    ctx = Context(repos)
    return ctx


def parse_yang_module(yang_file_path, ctx):
    r = re.compile(r"^(.*?)(\@(\d{4}-\d{2}-\d{2}))?\.(yang|yin)$")
    r1 = re.compile(r"^(.*?)\.(yang|yin)$")
    try:
        if sys.version_info[0] == 2:
            fd = io.open(yang_file_path, "r", encoding="UTF-8")
        else:
            fd = open(yang_file_path, "r", encoding="UTF-8")
        text = fd.read()
        m1 = r1.search(yang_file_path)
        if m1 is None:
            return ctx
        m = r.search(yang_file_path)
        ctx.yin_module_map = {}
        if m is not None:
            (name, _dummy, rev, format) = m.groups()
            name = os.path.basename(name)
            ctx.add_module(yang_file_path, text, format, name, rev)
        else:
            ctx.add_module(yang_file_path, text)
    except Exception:
        yang_error_write("can not open the file %s" % yang_file_path)
    finally:
        if fd is not None:
            fd.close()
    logging.info('parse yang module %s success!', yang_file_path)
    return ctx


def parse_yang_modules(yang_directory, ctx):
    if os.path.isfile(yang_directory):
        parse_yang_module(yang_directory, ctx)
    else:
        for yang_file in sorted(os.listdir(yang_directory)):
            yang_file_path = os.path.join(yang_directory, yang_file)
            if os.path.isdir(yang_file_path):
                parse_yang_modules(yang_file_path, ctx)
            parse_yang_module(yang_file_path, ctx)
    ctx.validate()
    return ctx

def get_moudle_name_from_annotations(annotations):
    for annotation_obj in annotations:
        pos = annotation_obj.str.find('module')
        if pos != -1:
            module_name = annotation_obj.str[pos + len('module'):].strip(' ').strip('\n')
            return module_name


def yang_module_has_error(ctx,module_name=None):
    for p,t,a in ctx.errors:
        if module_name is None:
            if is_error(t):
                return True
        else:
            if (is_error(t) and check_error_if_need(p, module_name)):
                return True

    return False

def check_error_if_need(pos, module_name):
    yang_error_name = ''
    try:
        yang_error_name = pos.top.arg
    except:
        pass
    if yang_error_name == module_name:
        return True
    return False

def is_error(error_type):
    error_level = pyang.error.err_level(error_type)
    if pyang.error.is_error(error_level):
        return True
    else:
        return False


def print_yang_errors(ctx, module_name=None):
    for p, t, a in ctx.errors:
        error_str = None
        error_level = pyang.error.err_level(t)
        if pyang.error.is_error(error_level):
            error_level_str = "Error"
        else:
            error_level_str = "Warning"
        if module_name is not None:
            if is_error(t) and check_error_if_need(p, module_name):
                error_str = ''.join([p.label(), " ", error_level_str,': ',pyang.error.err_to_str(t, a)])
        else:
            error_str = ''.join([p.label(), " ", error_level_str,': ',pyang.error.err_to_str(t, a)])
        if error_str is not None:
            print(error_str)
            yang_error_write(error_str)
    return

def yang_error_write(error_string):
    exc_info = sys.exc_info()
    exc_value = exc_info[1]

    if exc_value and traceback.format_exc().strip() != 'None':
        logging.error(traceback.format_exc())
    logging.error("%s",error_string)


def log_serious_errors(err_type, **kwargs):
    if err_type not in ERR_INFO:
        logging.info("receive unsupported error type")
        return

    if kwargs["file_name"] in ERR_REPORT_STAT[err_type]:
        return
    ERR_REPORT_STAT[err_type].append(kwargs["file_name"])
    logging.error(ERR_INFO[err_type].format(kwargs["file_name"]))


if __name__ == '__main__':
    pass
