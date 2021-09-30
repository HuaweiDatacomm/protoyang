#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright: (c) Huawei Technologies Co., Ltd. 2021. All rights reserved.

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/'+'..'))
from pyang import error

KEYWORD = ['message', 'enum', 'oneof', 'service','rpc']
SCOPE = ['repeated', 'optional', 'required', 'simple', '']


class DefinionObj(object):
    def __init__(self, ref):
        self.keyword = ''  # message enum oneof service
        self.pos = error.Position(ref)
        self.definions = {}
        self.statement = []
        self.is_print = False
        self.parent = None
        self.is_top = False
        self.name = ''
        self.augmented = 0  # 是否是augment的节点：1是，0否
        self.yang_node_order_num = 0  # 记录yang节点的序号，输出proto文件时按该序号排序
        self.proto_xpath = ''


class MessageObj(object):
    def __init__(self, ref):
        self.parent = None
        self.scope = ''  # repeated optional required simple null
        self.type = None
        self.name = ''
        self.num = ''
        self.pos = error.Position(ref)
        self.is_top = False
        self.augmented = 0  # 是否是augment的节点：1是，0否
        self.yang_node_order_num = 0  # 记录yang节点的序号，输出proto文件时按该序号排序
        self.yang_node_name = ''  # 记录proto节点对应yang文件节点名，输出proto时使用，如果oldproto该值为空，则替换；否则，不作改动
        self.enum_val = -1  # 记录proto节点对应yang文件中enum value值，有old proto时，取enum对应的proto num
        self.proto_annotations = []  # 记录old proto中节点对应注释信息
        self.proto_xpath = ''


class RpcObj(object):
    def __init__(self, ref):
        self.parent = None
        self.is_top = False
        self.scope = ''
        self.keyword = 'rpc'
        self.type = ''
        self.Request = ''
        self.Response = ''
        self.name = ''
        self.num = ''
        self.pos = error.Position(ref)
        self.proto_xpath = ''


class AnnotationObj(object):
    def __init__(self, ref, string, index):
        self.str = string
        self.pos = error.Position(ref)
        self.pos.line = index


class ProtoFile(object):
    def __init__(self,ref,version):
        self.i_syntax = version
        self.i_imports = []
        self.i_annotations = []
        self.i_package = ''
        self.i_services = []
        self.i_messages = []
        self.i_root_elements = []
        self.definions = {}
        self.ref = ref
        self.pos = error.Position(ref)


