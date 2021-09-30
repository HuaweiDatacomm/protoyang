#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright: (c) Huawei Technologies Co., Ltd. 2021. All rights reserved.


import os
from . import proto_parse
from . import proto_proto

__version__ = '1.1.0'
__date__ = '2021-08-02'


class Context(object):
    def __init__(self):
        self.errors = []

    def add_modules(self, ref, text):
        proto_module = proto_parse.ProtoParser()
        module = proto_module.parse(self, ref, text)
        if module is None:
            return None
        return module