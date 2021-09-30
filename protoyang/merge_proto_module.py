#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Copyright (C) 2021. Huawei Technologies Co., Ltd. All rights reserved.

#This program is free software; you can redistribute it and/or modify
#it under the terms of the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#Apache License, Version 2.0 for more details.
import logging
import os
from hpproto.proto_proto import DefinionObj


def get_proto_parents(proto_msg, xpaths):
    if proto_msg.parent is not None:
        xpaths.insert(0, proto_msg.parent.name)
        get_proto_parents(proto_msg.parent, xpaths)


def get_proto_xpaths(proto_msg):
    xpaths = []
    get_proto_parents(proto_msg, xpaths)
    xpath_str = ''
    for xpath in xpaths:
        xpath_str = '%s/%s' % (xpath_str, xpath)

    xpath_str = '%s/%s' % (xpath_str, proto_msg.name)
    return xpath_str


# 1.old proto没有enum_val值，取num值作为enum_val
def get_old_proto_enum_value(proto_msg):
    try:
        if proto_msg.parent.keyword == 'enum'and proto_msg.enum_val == -1:
            proto_msg.enum_val = int(proto_msg.num)
    except:
        logging.info('get enum value from old proto error, proto name:%s, xpath:%s'
                      % (proto_msg.name, get_proto_xpaths(proto_msg)))


def get_msg_type(msg):
    if isinstance(msg.type, DefinionObj):
        return msg.type.keyword
    else:
        return msg.type


def is_proto_type_equal_to_yang_type(proto_msg, yang_msg):
    if isinstance(proto_msg.type, DefinionObj) and isinstance(yang_msg.type, DefinionObj):
        if proto_msg.type.keyword == yang_msg.type.keyword: #and proto_msg.type.name == yang_msg.type.name:
            return True
        else:
            return False
    elif isinstance(proto_msg.type, DefinionObj):
        return False
    elif isinstance(yang_msg.type, DefinionObj):
        return False
    else:
        if proto_msg.type != yang_msg.type:
            logging.info('old proto node type not equal to yang node type, node name:%s, '
                            'old proto type:%s, yang proto type:%s' % (proto_msg.name, proto_msg.type, yang_msg.type))
            if proto_msg.type is None:
                proto_msg.type = yang_msg.type
        return proto_msg.type == yang_msg.type


def compare_enum_name_ignore_case(proto_msg, yang_msg):
    proto_msg_parent = proto_msg.parent
    yang_msg_parent = yang_msg.parent
    if proto_msg_parent.name == yang_msg_parent.name and proto_msg_parent.keyword == 'enum' and \
       yang_msg_parent.keyword == 'enum':
        proto_enum = proto_msg.name.lower()
        yang_enum = yang_msg.name.lower()
        if proto_enum == yang_enum:
            if proto_msg.name != yang_msg.name:
                logging.warning('old proto enum name not equal to yang enum, proto enum:%s, yang enum:%s'
                                % (proto_msg.name, yang_msg.name))
            return True
    return False


def find_proto_msg(proto_definion, yang_msg):
    for proto_msg in proto_definion.statement:
        if proto_msg.name == yang_msg.name:
            proto_msg.scope = yang_msg.scope
            if proto_msg.yang_node_name == '':
                proto_msg.yang_node_name = yang_msg.yang_node_name
            if is_proto_type_equal_to_yang_type(proto_msg, yang_msg):
                get_old_proto_enum_value(proto_msg)
            else:
                logging.info('old proto node type not equal to yang node type, node name:%s, xpath:%s, '
                              'old proto type:%s, yang node type:%s, out yang type.'
                              % (proto_msg.name, get_proto_xpaths(proto_msg), get_msg_type(proto_msg), get_msg_type(yang_msg)))

                # raise Exception('old proto type not equal to yang type')

                if isinstance(yang_msg.type, DefinionObj) and yang_msg.type.keyword == 'oneof':
                    for sub_proto_definion in proto_definion.definions.keys():
                        if proto_msg.type == proto_definion.definions[sub_proto_definion]:
                            del proto_definion.definions[sub_proto_definion]
                            break
                proto_msg.type = yang_msg.type
            return proto_msg
        elif compare_enum_name_ignore_case(proto_msg, yang_msg):  # old proto enum名为小写，比较时不区分大小写，认为是相同的
            return proto_msg

    return None


def find_proto_definion(proto_definions, yang_definion, recursive=False):
    if len(proto_definions) > 0:
        for obj in proto_definions.values():
            if obj.name == yang_definion.name:
                return obj
            else:
                if recursive:
                    find_proto_definion(obj.definions, yang_definion, True)


def find_yang_definion_existed_in_proto_definion(proto_definion, yang_definion):
    return find_proto_definion(proto_definion.definions, yang_definion, True)


# if any value in yang enum type, use yang value num
def judge_use_old_enum(yang_definion):
    for yang_msg in yang_definion.statement:
        if yang_msg.enum_val != -1:
            return False
    return True


def _compare_statement(yang_definion, proto_definion):

    if not judge_use_old_enum(yang_definion):
        # ignore old proto enum structure
        proto_definion.statement = yang_definion.statement
        return

    for yang_msg in yang_definion.statement:
        proto_msg = find_proto_msg(proto_definion, yang_msg)
        if proto_msg is None:
            logging.info("statement nonexistent %s" % yang_msg.name)

            # check if proto file has old definions of msg obj with statement none.
            if isinstance(yang_msg.type, DefinionObj):
                def_obj = find_yang_definion_existed_in_proto_definion(proto_definion, yang_msg.type)
                if def_obj is not None:
                    yang_msg.type = def_obj
                else:
                    logging.info("def obj nonexistent %s" % yang_msg.type.name)

            proto_definion.statement.append(yang_msg)


def _compare_definions(yang_definions, proto_definions, proto_parent_definion=None):
    if len(yang_definions) > 0:
        for yang_definion in yang_definions.values():
            proto_definion = find_proto_definion(proto_definions, yang_definion)
            if proto_definion is not None:
                _compare_definions(yang_definion.definions, proto_definion.definions, proto_definion)
                _compare_statement(yang_definion, proto_definion)
            else:
                logging.info('ignore definion %s' % yang_definion.name)
                proto_definions[yang_definion.name] = yang_definion
                if proto_parent_definion is not None:
                    proto_parent_definion.definions = proto_definions


def _replace_annotations(yang_proto, proto):
    proto.i_annotations = yang_proto.i_annotations


def del_same_node_in_proto(module):
    del_definions = []
    del_statements = []
    if isinstance(module, DefinionObj) and not judge_xpath_has_same_node(module.proto_xpath):
        del_definions.append(module.name)
        return del_definions

    for definion in list(module.definions.values()):
        if not judge_xpath_has_same_node(definion.proto_xpath):
            del_definions.append(definion.name)
            logging.info('proto path have same node name! %s'% definion.proto_xpath)
        if definion.definions:
            for child_definion in list(definion.definions.values()):
                del_definions.extend(del_same_node_in_proto(child_definion))
    for del_definion in del_definions:
        if del_definion not in module.definions.keys():
            continue
        module.definions.pop(del_definion)

    for statement in list(module.statement):
        if not judge_xpath_has_same_node(statement.proto_xpath):
            del_statements.append(statement)
            logging.info('proto path have same node name! %s' % statement.proto_xpath)
        if isinstance(statement.type, DefinionObj):
            if del_same_node_in_proto(statement.type):
                del_statements.append(statement)
    for del_stat in del_statements:
        if del_stat not in module.statement:
            continue
        module.statement.remove(del_stat)
    return []


def judge_xpath_has_same_node(xpath):
    node = xpath.split('/')
    if len(node) == len(set(node)):
        return True
    return False


def merge_proto_module(yang_module, proto_module):
    try:
        if yang_module is not None and proto_module is not None:
            yang_definions = yang_module.definions
            proto_definions = proto_module.definions
            _compare_definions(yang_definions, proto_definions)
            _replace_annotations(yang_module, proto_module)
        else:
            if yang_module is None:
                logging.info('proto node translated from yang file is None')
            elif proto_module is None:
                logging.info('old proto is empty, out yang module')
                return 1
    except Exception:
        logging.info('can not merge old proto, old proto: %s, new proto: %s'
                      % (os.path.basename(proto_module.pos.ref), os.path.basename(yang_module.pos.ref)))
        return 1
    return 0
