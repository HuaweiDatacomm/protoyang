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

import os
import io
import sys
import logging
import hpproto
from operator import attrgetter
from merge_proto_module import *
import copy


java_keyword_names = ["BUILDPARTIAL", "CLEAR", "CLEARFIELD", "CLEARONEOF", "CLONE", "EQUALS", "FINDVALUEBYNUMBER",
                    "FORNUMBER", "GETDEFAULTINSTANCE", "GETDEFAULTINSTANCEFORTYPE", "GETDESCRIPTOR",
                    "GETDESCRIPTORFORTYPE", "GETNUMBER", "GETPARSERFORTYPE", "GETSERIALIZEDSIZE", "GETUNKNOWNFIELDS",
                    "GETVALUEDESCRIPTOR", "HASHCODE", "INTERNALGETFIELDACCESSORTABLE", "INTERNALGETVALUEMAP",
                    "INTERNALVALUEMAP", "ISINITIALIZED", "MAYBEFORCEBUILDERINITIALIZATION", "MERGEFROM",
                    "MERGEUNKNOWNFIELDS", "NEWBUILDER", "NEWBUILDERFORTYPE", "PARSEDELIMITEDFROM", "PARSEFROM",
                    "PARSEPARTIALFROM", "PARSER", "REGISTERALLEXTENSIONS", "SETFIELD", "SETREPEATEDFIELD",
                    "SETUNKNOWNFIELDS", "TOBUILDER", "VALUEOF", "WRITETO", "DEFAULTINSTANCE", "DEFAULTINSTANCEFORTYPE",
                      "DESCRIPTOR", "DESCRIPTORFORTYPE", "NUMBER",
                     "PARSERFORTYPE", "SERIALIZEDSIZE", "UNKNOWNFIELDS", "VALUEDESCRIPTOR", "FIELD", "REPEATEDFIELD",
                     "UNKNOWNFIELDS"]


class Proto_writer():
    def __init__(self, proto_file):
        self.proto_file = proto_file
        self.crt_line_num = 1
        self.last_annotation_num = 0

    def sort_services(self, services):
        if type(services) == list and services != []:
            services.sort(key=attrgetter('name'))
        # sort statements in services
        for service in services:
            unsort_statement = []
            sorted_statement = []
            if type(service.statement) == list and service.statement != []:
                for statement in service.statement:
                    if statement.num == '':
                        unsort_statement.append(statement)
                    else:
                        sorted_statement.append(statement)
                if unsort_statement:
                    unsort_statement.sort(key=attrgetter('name'))
                    for tmp in unsort_statement:
                        service.statement.remove(tmp)
                        service.statement.append(tmp)
                crt_num = -1
                for statement in service.statement:
                    crt_num = self.get_current_num(crt_num, statement)
                    if statement.num == '':
                        statement.num = str(crt_num)
                    crt_num += 1
        return True

    def service_statement_str(self, scope, type, name, request, response):
        str = ''
        if scope is not None and scope != '' and scope != 'simple':
            str = ''.join([str, scope, ' '])
        if type is not None and type!='':
            str = ''.join([str, type, ' '])
        if name is not None and name!='':
            str = ''.join([str, 'rpc ', name, ' '])
        if request is not None and request!='':
            str = ''.join([str, '(', request, ') '])
        if response is not None and response!='':
            str = ''.join([str, 'returns (', response, ')'])
        str = ''.join([str, ';\n'])
        return str

    # output services
    def output_services(self, file, services):
        self.sort_services(self.proto_file.i_services)
        for service in services:
            # output structure of service
            if service.is_print == False:
                str = self.message_struct_str(service.keyword, service.name)
                self.file_write(file, str)
                service.is_print = True
            # output statement of service
            space = '   '
            # output statement of service
            for statement in service.statement:
                str = self.service_statement_str(statement.scope, statement.type,
                                                 statement.name, statement.Request, statement.Response)
                self.file_write(file, space+str)
            self.file_write(file, '}\n')
            # output requests of service
            request_definions = {}
            response_definions = {}
            for statement in service.statement:
                request_definions[statement.Request] = self.proto_file.definions[statement.Request]
                response_definions[statement.Response] = self.proto_file.definions[statement.Response]
            self.output_definions(request_definions, file, '')
            # output responses of service
            self.output_definions(response_definions, file, '')
        return True

    def file_write(self, file, str):
        file.write(str)
        self.crt_line_num += 1
        return True

    def output_annotations_begin(self, file, annotations):
        i = 0
        for i in range(self.last_annotation_num, len(annotations)):
            if annotations[i].pos.line > self.crt_line_num:
                break
            else:
                if annotations[i].pos.uses_pos is None:
                    self.file_write(file, annotations[i].str)
                    annotations[i].pos.uses_pos = self.crt_line_num
        self.last_annotation_num = i
        self.file_write(file, '\n')
        return True

    def output_annotations_end(self, file, annotations):
        i = 0
        for i in range(self.last_annotation_num, len(annotations)):
            if annotations[i].pos.uses_pos is None:
                self.file_write(file,annotations[i].str)
                annotations[i].pos.uses_pos = self.crt_line_num
        self.last_annotation_num = i
        self.file_write(file, '\n')
        return True

    def get_public_import(self, import_str):
        imports = import_str.split(' ')
        if len(imports) == 2 and imports[0] == 'public':
            return imports[1]
        else:
            return ''

    # output heads
    def output_heads(self, file):
        syntax = 'proto3'
        # print syntex
        if self.proto_file.i_syntax is not None and self.proto_file.i_syntax != '':
            syntax = self.proto_file.i_syntax
        self.file_write(file, 'syntax = "%s";\n' % syntax)
        # print annotations
        self.output_annotations_begin(file, self.proto_file.i_annotations)
        # print imports
        for mpt in self.proto_file.i_imports:
            public_import = self.get_public_import(mpt)
            if public_import != '':
                self.file_write(file, 'import public "%s";\n' % public_import)
            else:
                self.file_write(file, 'import "%s";\n' % mpt)
        # print package
        if self.proto_file.i_package is not None:
            self.file_write(file, 'package %s;\n' % self.proto_file.i_package)
            self.file_write(file, '\n')
        # print service
        self.output_services(file, self.proto_file.i_services)
        return True

    def get_current_num(self, num, sub_msg):

        # arrange oneof num
        if sub_msg.num != '':
            crt_num = int(sub_msg.num)
            return crt_num
        crt_num = num + 1
        if num == -1:  # set the initial value for num
            if sub_msg.parent is not None and sub_msg.parent.keyword == 'enum':
                crt_num = 0  # initial value for enum element
            else:
                crt_num = 1  # initial value for others
        return crt_num

    def insert_dummy_enum_in_first(self, statements):
        enum_prefix = statements[0].name.split('_')[0]
        dummy_enum = copy.copy(statements[0])
        dummy_enum.enum_val = 0
        dummy_enum.name = '%s_INVALID_ENUM_VALUE' % enum_prefix
        statements.insert(0, dummy_enum)



    def sort_enum_statement(self, statements):
        #sort the enum by value
        statements.sort(key=attrgetter('enum_val'))
        if statements[0].enum_val != 0:
            self.insert_dummy_enum_in_first(statements)

    def assign_old_proto_num_to_yang_order_num(self, old_proto_statement):
        for old_stat in old_proto_statement:
            old_stat.yang_node_order_num = int(old_stat.num)

    def sort_statement_by_key(self, statement, parent_statements):
        statement.sort(key=attrgetter('yang_node_order_num'))
        for stat in statement:
            parent_statements.remove(stat)
            parent_statements.append(stat)

    # sort statements
    def sort_statements(self, statements, crt_num=-1):
        unsort_statement = []
        old_proto_statement = []
        # current max num
        max_num = crt_num
        if type(statements) == list and statements != []:
            for statement in statements:
                if statement.num == '':
                    unsort_statement.append(statement)
                else:
                    if statement.num and int(statement.num) > max_num:
                        max_num = int(statement.num)
                    old_proto_statement.append(statement)
            #the node with smaller proto num maybe occurs behind the node with greater proto num, so need resort the nodes
            #according proto num of old proto
            self.assign_old_proto_num_to_yang_order_num(old_proto_statement)
            self.sort_statement_by_key(old_proto_statement, statements)

            # if the proto num of nodes are empty, sort them according the sequence of yang file
            self.sort_statement_by_key(unsort_statement, statements)

            # 对enum排序：1.有old proto时，先按old proto顺序排序；2.没有old proto时，按enum value排序
            if statements[0].parent.keyword == 'enum':
                self.sort_enum_statement(statements)
                #self.assign_enum_value_to_num(statements)
            statement_len = len(statements)
            for i in range(0, statement_len):
                if type(statements[i].type) == hpproto.proto_proto.DefinionObj \
                             and statements[i].type.keyword == 'oneof':
                    continue
                crt_num = self.get_current_num(crt_num, statements[i])
                if not statements[i].num:
                    crt_num = max(crt_num, max_num+1)
                    max_num = crt_num
                    statements[i].num = str(crt_num)
                else:
                    # enum or oneof ignore
                    if statements[i].parent.keyword == 'enum':
                        continue
                    # 多个proto文件合并时，可能出现后面statement的num值小于前面的情形，此时给后面num值+1处理
                    if i+1 < statement_len and statements[i+1].num != '':
                        last_stat_num = int(statements[i].num)
                        next_stat_num = int(statements[i+1].num)
                        if next_stat_num <= last_stat_num:
                            next_stat_num = last_stat_num + 1
                            statements[i+1].num = str(next_stat_num)
                        crt_num = last_stat_num
                if type(statements[i].type) == hpproto.proto_proto.DefinionObj :
                    if statements[i].type.keyword == 'oneof':
                        self.sort_statements(statements[i].type.statement, max_num)
                        if statements[i].type.statement:
                            max_num = max(int(statements[i].type.statement[-1].num), max_num)
                            crt_num = max_num
                    else:
                        self.sort_statements(statements[i].type.statement)
        return True

    # sort definions
    def sort_definions(self, definions):
        if not definions:
            return True
        for definion in definions.values():
            if definion.statement:
                self.sort_statements(definion.statement)
        return True

    def message_struct_str(self, keyword, str_type):
        if str_type == 'Empty':
            str_out = '%s Empty { ' % keyword
        else:
            str_out = '%s %s {\n' % (keyword, str_type)
        return str_out

    def message_statement_str(self, statement):
        str_out = ''
        yang_node_name = statement.yang_node_name
        scope = statement.scope
        if isinstance(statement.type, hpproto.proto_proto.DefinionObj):
            type_str = statement.type.name
        else:
            type_str = statement.type
        name = statement.name
        num = statement.num
        proto_annotations = statement.proto_annotations
        if scope and scope != 'simple':
            str_out = '%s%s ' % (str_out, scope)
        if type_str :
            str_out = '%s%s ' % (str_out, type_str)
        if name :
            str_out = '%s%s ' % (str_out, name)
        if yang_node_name != '':
            if yang_node_name.startswith('[') and yang_node_name.endswith(']'):  # old proto中有[]，直接将[]弄过来
                yang_node_str = ' %s' % yang_node_name
            else:
                yang_node_str = ' [json_name = "%s"]' % yang_node_name

            if proto_annotations:
                str_out = '%s=%s%s; ' % (str_out, num, yang_node_str)
                for annotation in proto_annotations:
                    str_out = '%s//%s' % (str_out, annotation)
            else:
                str_out = '%s= %s%s;\n' %(str_out, num, yang_node_str)
        else:
            str_out = '%s= %s;\n' % (str_out, num)
            if statement.parent.keyword != 'enum':
                logging.info('node %s json name is null, xpath:%s' % (statement.name, get_proto_xpaths(statement)))
        return str_out

    # output statement
    def output_statement(self, statement, file, definions, space=''):
        if not statement:
            return True
        for sub_statement in statement:
            if type(sub_statement.type) != hpproto.proto_proto.DefinionObj:
                if sub_statement.name != '':
                    str_out = self.message_statement_str(sub_statement)
                    self.file_write(file, ''.join([space, str_out]))
            elif sub_statement.type.keyword == 'oneof':
                # out_put sub_message out of oneof
                if sub_statement.type.statement:
                    self.output_statement(sub_statement.type.statement, file, sub_statement.type.definions,
                                          space)
                    str_out = self.message_struct_str(sub_statement.type.keyword, sub_statement.type.name)
                    self.file_write(file, ''.join([space, str_out]))
                    for sub_stmt in sub_statement.type.statement:
                        str_line = self.message_statement_str(sub_stmt)
                        if str_line:
                            self.file_write(file, ''.join(['%s   ' % space, str_line]))
                    self.file_write(file, '%s}\n' % space)
                    sub_statement.type.is_print = True
            else:
                tail_str = ''
                # output structure of type
                if sub_statement.type.keyword in hpproto.proto_proto.KEYWORD and not sub_statement.type.is_print:
                    str_out = self.message_struct_str(sub_statement.type.keyword, sub_statement.type.name)
                    self.file_write(file, ''.join([space, str_out]))
                    sub_statement.type.is_print = True
                    if sub_statement.type.statement:
                        sub_space = '%s   ' % space
                        self.output_statement(sub_statement.type.statement, file, sub_statement.type.definions,
                                              sub_space)
                    tail_str = '%s}' % space
                    if sub_statement.type.keyword == 'enum':
                        tail_str = '%s;' % tail_str
                # output tail of structure
                if tail_str != '':
                    self.file_write(file, '%s\n'% tail_str)
                # output statement
                # case do not need output outside
                if sub_statement.name != '' and sub_statement.parent.keyword != 'oneof':
                    str_line = self.message_statement_str(sub_statement)
                    if str_line:
                        self.file_write(file, ''.join([space, str_line]))

        self.output_definions(definions, file, space)
        return True

    # output definions
    def output_definions(self, definions, file, space=''):
        if not definions:
            return True
        sorted_definions = list(definions.values())
        sorted_definions.sort(key=attrgetter('pos.line'))
        unsort_definions = []
        if type(sorted_definions) == list and sorted_definions != []:
            for tmp in sorted_definions:
                if tmp.pos.line == 0:
                    unsort_definions.append(tmp)
            if unsort_definions:
                unsort_definions.sort(key=attrgetter('yang_node_order_num'))

                for tmp in unsort_definions:
                    sorted_definions.remove(tmp)
                    sorted_definions.append(tmp)
        # output the root definions fist
        if self.proto_file.i_root_elements:
            root_definions = []
            for i in range(len(sorted_definions)-1, -1, -1):
                tmp = sorted_definions[i]
                if tmp.name in self.proto_file.i_root_elements:
                    root_definions.insert(0, tmp)
                    sorted_definions.pop(i)

            if root_definions:
                sorted_definions = root_definions + sorted_definions
        for definion in sorted_definions:
            if definion.is_print:
                continue
            if definion.is_top:
                space = ''
            tail_str = ''
            # output definions
            if definion.keyword in hpproto.proto_proto.KEYWORD:
                str = self.message_struct_str(definion.keyword, definion.name)
                self.file_write(file, ''.join([space, str]))
                definion.is_print = True
                # output sub statement
                if definion.statement:
                    sub_space = '%s   ' % space
                    self.output_statement(definion.statement, file, definion.definions, sub_space)
                if definion.name == 'Empty':
                    tail_str = '}'
                else:
                    tail_str = '%s}' % space
                if definion.keyword == 'enum':
                    tail_str = '%s;' % tail_str
            # output tail of definions
            if tail_str != '':
                self.file_write(file, '%s\n' % tail_str)

        return True

    # edit profile for test
    def edit_profile(self, proto_file):
        self.proto_file.definions['XQoS4QueueResPreAlarmCancelTrap'].pos.line = 0
        self.proto_file.definions['HqosSQApplyPirFailAlarmTrap'].pos.line = 0
        return True

    def first_letter_upper(self, name):
        # 当definion为'_24GHz'时，split('_')后传入的name为空，会产生异常
        strs = ''
        try:
            strs = ''.join([name[0].upper(), name[1:]])
        except:
            pass

        return strs

    def first_attr_upper(self, name):
        if name[0].isupper():
            return True
        return False

    def find_and_delete_invalid_definions(self, statements, definions):
        type_names = []
        statements_names = [stat.name for stat in statements]
        # delete old_proto same_name_node
        del_stat_dict = {}
        cap_statements_names = [stat_name.replace('_', '').upper() for stat_name in statements_names]
        from collections import defaultdict
        del_stats = []
        for java_keyword_name in java_keyword_names:
            if java_keyword_name in cap_statements_names:
                del_stats.append(statements[cap_statements_names.index(java_keyword_name)])
                logging.info('remove node %s, because it is java key word'
                             % statements[cap_statements_names.index(java_keyword_name)].name)
        d = defaultdict(list)
        for k, va in [(v, i) for i, v in enumerate(cap_statements_names)]:
            d[k].append(va)
        # oldproto为人工书写的，遇到特殊字符转成了驼峰格式，与目前工具转换逻辑不一致，所以取工具转换节点名
        # 目前通过下划线个数来判断，个数多的就是工具转换的，目前仅支持同一个父节点下出现2个，认为匹配成功
        for values in d.values():
            if len(values) == 2:
                if statements_names[values[0]].count('_') > statements_names[values[1]].count('_'):
                    del_stat_dict[values[0]] = values[1]
                else:
                    del_stat_dict[values[1]] = values[0]

        for new_index in del_stat_dict.keys():
            old_stat = statements[del_stat_dict[new_index]]
            new_stat = statements[new_index]
            new_stat.num = old_stat.num
            del_stats.append(old_stat)
            logging.info("remove node %s, because it is same with node %s", str(old_stat.name), str(new_stat.name))
        del_stats = set(del_stats)
        for stat in del_stats:
            statements.remove(stat)

        for stat in statements:
            if isinstance(stat.type, hpproto.proto_proto.DefinionObj):
                if stat.type.statement:
                    self.find_and_delete_invalid_definions(stat.type.statement, stat.type.definions)

                if stat.yang_node_name != '' or stat.type.pos.line != 0:
                    type_names.append(stat.type.name)

        if len(definions) > 0:
            del_keys = []
            for definion_name in definions.keys():
                # deal with empty oneof
                if isinstance(definions[definion_name], hpproto.proto_proto.DefinionObj):
                    if definions[definion_name].keyword == 'oneof' and not definions[definion_name].statement:
                        del_keys.append(definion_name)
                        continue
                if definion_name not in type_names and definion_name not in del_keys:
                    del_keys.append(definion_name)
                elif definion_name.replace('_', '').upper() in java_keyword_names:
                    del_keys.append(definion_name)

            for del_key in del_keys:
                logging.info('delete invalid definion:%s' % del_key)
                definions.pop(del_key)

    def delete_invalid_definions(self, definions):
        for definion in definions.values():
            self.find_and_delete_invalid_definions(definion.statement, definion.definions)

    def output_proto_file(self, filename=None):
        if not filename:
            #filename = os.path.join(self.out_directory, '%s.proto' % self.module_name)
            filename = self.proto_file.ref
        logging.info(
            "==============================START OUPUT PROTO %s===================================" % filename)
        with open(filename, "w", encoding="utf-8") as file:
            self.output_heads(file)
            self.delete_invalid_definions(self.proto_file.definions)
            self.sort_definions(self.proto_file.definions)
            if self.proto_file.definions:
                for proto_file_definion in self.proto_file.definions.values():
                    del_same_node_in_proto(proto_file_definion)
            self.output_definions(self.proto_file.definions, file)
            self.output_annotations_end(file, self.proto_file.i_annotations)
        return True