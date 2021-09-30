#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright: (c) Huawei Technologies Co., Ltd. 2021. All rights reserved.


import collections
import re
import sys
from hpproto.proto_proto import AnnotationObj
from hpproto.proto_proto import MessageObj
from hpproto.proto_proto import DefinionObj
from hpproto.proto_proto import RpcObj
from hpproto.proto_proto import ProtoFile
from . import syntax
import logging
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/'+'..'))
from pyang import error

Proto_Base_Type = ['bytes','bool','string','int32','int64','uint32','uint64',
            'double','float','sint32','sint64','fixed32','sfixed32','fixed64','sfixed64', 'Decimal64']
Complex_Type =['enum','message','service','oneof']
Describe_Attr = ['repeated','optional','required','singular']
YANG_NODE_NAME_IN_PROTO_IDENTITY = 'json_name'


class ProtoTokenizer(ProtoFile):
    def __init__(self, text, ref, errors):
        super(ProtoTokenizer, self).__init__(ref, 'proto2')
        self.lines = collections.deque(text.splitlines(True))
        self.buf = ''
        self.offset = 0
        """Position on line.  Used to remove leading whitespace from strings."""
        self.errors = errors
        self.max_line = len(text.split('\n'))

    def readline(self):
        if len(self.lines) == 0:
            return
        self.buf = self.lines.popleft()
        self.pos.line += 1
        self.offset = 0

    def set_buf(self, pos):
        self.buf = self.buf[pos:]
        self.offset += pos

    def skip(self):
        buflen_before = len(self.buf)
        while True:
            self.buf = self.buf.lstrip()
            if self.buf:
                self.offset += (buflen_before - len(self.buf))
                break
            else:
                if len(self.lines) == 0:
                    return
                self.readline()
                buflen_before = len(self.buf)
        if self.buf[0] == '/':
            if self.buf[1] == '/':
                annotation = AnnotationObj(self.ref, self.buf, self.pos.line)
                self.i_annotations.append(annotation)
                if len(self.lines) == 0:
                    return
                self.readline()
                return self.skip()
            elif self.buf[1] == '*':
                anotation = ''
                line = self.pos.line
                anotation += self.buf
                i = self.buf.find('*/')
                while i == -1:
                    self.readline()
                    if len(self.lines) == 0:
                        return
                    anotation = ''.join([anotation, self.buf])
                    i = self.buf.find('*/')
                self.set_buf(i + 2)
                if self.pos.line < self.max_line:
                    annotation = AnnotationObj(self.ref, anotation, line)
                    self.i_annotations.append(annotation)
            return self.skip()

    def _parse_statement_type(self, args, definions):
        if args in Proto_Base_Type:
            type = args
        elif args in definions.keys():
            type = definions[args]
        else:
            error.err_add(self.errors, self.pos,
                          'SYNTAX_ERROR', 'illegal stmt: %s' % self.buf)
            raise error.Abort

        return type

    def parse_json_name(self, proto_str):
        yang_node_name = ''

        # 匹配old proto中[*]，将[*]当成json_name
        pattern_module = re.compile(r'(\[[\s\S]*\])')
        m = pattern_module.findall(proto_str.strip())
        if m:
            yang_node_name = m[0]
        return yang_node_name

    def get_proto_num_and_name(self, parent):
        proto_nums = []
        proto_names = []
        for stat in parent.statement:
            proto_nums.append(int(stat.num))
            proto_names.append(stat.name)
        return proto_nums, proto_names

    def validate_proto_num(self, proto_nums, node):
        max_num = -1
        if proto_nums:
            max_num = max(proto_nums)

        try:
            node_num = int(node.num)
            if node_num <= max_num:
                logging.warning('proto node:%s which num:%d less than before proto num in %s:%d'
                                % (node.name, node_num, self.pos.ref, self.pos.line))
        except:
            error.err_add(self.errors, self.pos,
                          'SYNTAX_ERROR', 'illegal proto num: %s' % node.num)
            raise error.Abort

    def validate_proto_name(self, proto_names, name):
        if name in proto_names:
            error.err_add(self.errors, self.pos,
                          'SYNTAX_ERROR', 'duplicate proto name: %s' % name)
            raise error.Abort

    def match_statement_content(self, proto_str):
        pattern_module = re.compile(r'(.*)\s*=\s*(\w*)\s*\[')
        match_content = pattern_module.findall(proto_str.strip())
        if match_content:
            return match_content
        else:
            pattern_module = re.compile(r'(.*)\s*=\s*(\w*)\s*;')
            return pattern_module.findall(proto_str.strip())

    def parse_augment(self, stmt):
        augment_file_name = os.path.basename(self.pos.ref).split('.')[0]
        if augment_file_name.endswith('_aug'):
            stmt.augmented = 1

    def parse_statement_content(self, parent):
        self.skip()
        if len(self.lines) == 0:
            return None
        if parent is None:
            parent = self
        split_strs = self.buf.split('//')
        proto_str = split_strs[0]
        proto_annotations = []
        if len(split_strs) > 1:
            proto_annotations = split_strs[1:]
        m = self.match_statement_content(proto_str)
        if m:
            arg = m[0][0].split()
            num = m[0][1]
            if not re.match(r'\d', num):
                error.err_add(self.errors, self.pos,
                              'SYNTAX_ERROR', 'illegal stmt: %s' % self.buf)
                raise error.Abort
            stmt = MessageObj(self.ref)
            stmt.num = num
            # enum
            if len(arg) == 1:
                stmt.scope = 'simple'
                stmt.name = arg[0]
            # string name
            elif len(arg) == 2:
                stmt.scope = 'simple'
                stmt.name = arg[1]
                if parent.keyword == 'oneof':
                    stmt.type = self._parse_statement_type(arg[0], parent.parent.definions)
                else:
                    stmt.type = self._parse_statement_type(arg[0], parent.definions)
            # repeated *** ***
            elif len(arg) == 3:
                if arg[0] not in Describe_Attr:
                    error.err_add(self.errors, self.pos,
                                  'SYNTAX_ERROR', 'illegal stmt: %s' % self.buf)
                    raise error.Abort
                stmt.scope = arg[0]
                stmt.type = self._parse_statement_type(arg[1], parent.definions)
                stmt.name = arg[2]
            else:
                error.err_add(self.errors, self.pos,
                              'SYNTAX_ERROR', 'illegal stmt: %s' % self.buf)
                raise error.Abort

            stmt.yang_node_name = self.parse_json_name(proto_str)
            stmt.proto_annotations = proto_annotations
            if parent:
                stmt.proto_xpath = '%s/%s' % (parent.proto_xpath, stmt.name)
            else:
                stmt.proto_xpath = '/%s' % stmt.name
            self.set_buf(len(self.buf.split(';')[0]))

            proto_nums, proto_names = self.get_proto_num_and_name(parent)
            self.validate_proto_num(proto_nums, stmt)
            self.validate_proto_name(proto_names, stmt.name)
            self.parse_augment(stmt)

            return stmt

        return None

    def get_keyword(self):
        r = syntax.re_keyword.match(self.buf)
        if r:
            self.set_buf(r.end())
            if not (self.buf[0] in (' ', ';', '{') or
                    self.buf[0:1] == '//' or self.buf[0:1] == '/*'):
                error.err_add(self.errors, self.pos,
                              'SYNTAX_ERROR', 'expected separator appear, but got: %s"..."' % self.buf[:6])
                raise error.Abort
            if r.group(2):
                return (r.group(2), r.group(3))
            else:
                return r.group(3)
        else:
            error.err_add(self.errors, self.pos,
                          'SYNTAX_ERROR', 'illegal keyword appear: ' + self.buf)
            raise error.Abort

    def peek(self):
        self.skip()
        return self.buf[0]

    def get_string(self, need_quote=False):
        """ret: string"""
        self.skip()

        if self.buf[0] in (';', '{', '}'):
            error.err_add(self.errors, self.pos,
                          'EXPECTED_ARGUMENT', self.buf[0])
            raise error.Abort
        while self.buf[0] in ('=', ' '):
            self.set_buf(1)
        if self.buf[0] in ('"', "'"):
            find_str = self.buf[0]
            buf_strs = []
            cur_pos = self.offset
            index = 1
            while True:
                buflen = len(self.buf)
                start_pos = index
                while index < buflen:
                    if self.buf[index] == find_str:
                        buf_strs.append(self.buf[start_pos:index])
                        self.set_buf(index + 1)
                        self.skip()
                        return ''.join(buf_strs)
                    index = index + 1
                buf_strs.append(self.buf[start_pos:index])
                self.readline()
                index = 0
                if find_str == '"':
                    buflen = len(self.buf)
                    while (index < buflen and self.buf[index] == '' and
                                   index <= cur_pos):
                        index = index + 1
                    if index == buflen:
                        index = 0
        elif need_quote:
            error.err_add(self.errors, self.pos, 'EXPECTED_QUOTED_STRING', ())
            raise error.Abort
        else:
            buflen = len(self.buf)
            index = 0
            while index < buflen:
                if (self.buf[index] in (';', '{', '}') or
                        self.buf[index:index + 2] == '//' or self.buf[index:index + 2] == '/*' or
                        self.buf[index:index + 2] == '*/'):
                    res = self.buf[:index]
                    self.set_buf(index)
                    return res
                index = index + 1

class ProtoParser(object):
    def __init__(self):
        pass

    def parse(self, ctx, ref, text):
        self.ctx = ctx
        try:
            self.tokenizer = ProtoTokenizer(text, ref, ctx.errors)
            self._parse_head()
            while (self.tokenizer.pos.line < self.tokenizer.max_line-1):
                self._parse_statement(None, ref)
        except error.Abort:
            # 解析不含message的proto文件时，清除此时报错，返回已解析的内容
            if self.tokenizer.buf == '' and len(self.tokenizer.i_messages) == 0:
                ctx.errors.clear()
                return self.tokenizer
            else:
                error.err_add(self.ctx.errors, self.tokenizer.pos, 'ABO_ERROR', ())
                return None
        except error.Eof as e:
            error.err_add(self.ctx.errors, self.tokenizer.pos, 'EOF_ERROR', ())
            return None
        return self.tokenizer

    def get_public_import(self, arg):
        imports = arg.split(' ')
        public_import = ''

        # proto头含有public的import：import public "aaa.proto";
        # 参考https://developers.google.com/protocol-buffers/docs/proto3
        if len(imports) == 2 and imports[0] == 'public':
            proto_file_name = imports[1].strip('"')
            public_import = '%spublic %s' % (public_import, proto_file_name)
        return public_import

    def validate_import(self, import_proto):
        proto_strs = import_proto.split('.')
        if len(proto_strs) == 2 and proto_strs[1] == 'proto':
            return True
        else:
            return False

    def _parse_head(self):
        self.tokenizer.skip()
        if len(self.tokenizer.lines) == 0:
            return None
        temp_buf = ''
        while True:
            temp_buf = self.tokenizer.buf
            keywd = self.tokenizer.get_keyword()
            tok = self.tokenizer.peek()
            if tok == '{' or tok == ';':
                arg = None
            else:
                arg = self.tokenizer.get_string().rstrip()
            if keywd in Complex_Type:
                self.tokenizer.buf = temp_buf
                return
            if keywd == 'syntax':
                self.tokenizer.i_syntax = arg
                if tok == '=':
                    self.tokenizer.skip()
                    self.tokenizer.set_buf(1)
                else:
                    error.err_add(self.ctx.errors, self.tokenizer.pos, 'INCOMPLETE_STATEMENT',
                                  (keywd, tok))
                    raise error.Abort
            # 例：import "***";
            elif keywd == 'import':
                import_proto_str = self.get_public_import(arg)
                if import_proto_str == '':
                    import_proto_str = arg

                if not self.validate_import(import_proto_str):
                    error.err_add(self.ctx.errors, self.tokenizer.pos, 'INVALID_IMPORT',
                                  (keywd, import_proto_str))
                    return error.Abort

                self.tokenizer.i_imports.append(import_proto_str)
                self.tokenizer.skip()
                self.tokenizer.set_buf(1)
            elif keywd == 'package':
                self.tokenizer.i_package = arg
                self.tokenizer.skip()
                self.tokenizer.set_buf(1)
            # rpc *** (***) returns (***);
            self.tokenizer.skip()

    def _parse_statement(self, parent, ref):
        is_definion_result = self.tokenizer.parse_statement_content(parent)
        if len(self.tokenizer.lines) == 0:
            self.tokenizer.pos.line += 1
            return None
        if is_definion_result:
            if self.tokenizer.peek() == ';':
                self.tokenizer.skip()
                self.tokenizer.set_buf(1)
            if parent is not None:
                is_definion_result.parent = parent
                parent.statement.append(is_definion_result)
                if parent.keyword == 'oneof' and parent.parent:
                    parent.parent.statement.append(is_definion_result)
            else:
                is_definion_result.is_top = True
                self.tokenizer.i_messages.append(is_definion_result)
        else:
            keywd = self.tokenizer.get_keyword()
            tok = self.tokenizer.peek()
            if tok == '{' or tok == ';':
                arg = None
            else:
                arg = self.tokenizer.get_string().rstrip()            
            if keywd == 'rpc':
                self.tokenizer.skip()
                self.tokenizer.set_buf(1)
                parent.statement.append(self.translate_rpc(parent, keywd, arg, ref))
            else:
                # 例：enum *** {*};
                stmt = self.translate_definion_type(ref, parent, keywd, arg)
                tok = self.tokenizer.peek()
                if tok == '{':
                    self.tokenizer.skip()
                    self.tokenizer.set_buf(1)  # skip the '{'
                    while self.tokenizer.peek() != '}':
                        if self.tokenizer.peek() == ';':
                            self.tokenizer.skip()
                            self.tokenizer.set_buf(1)
                        stmt = self._parse_statement(stmt, ref)
                    if parent is None:
                        if stmt.keyword == 'service':
                            self.tokenizer.i_services.append(stmt)
                        else:
                            self.tokenizer.definions[arg] = stmt
                    else:
                        parent.definions[arg] = stmt
                    self.tokenizer.skip()
                    self.tokenizer.set_buf(1)  # skip the '}'
                elif tok == ';':
                    self.tokenizer.skip()
                    self.tokenizer.set_buf(1)  # skip the ';'
                else:
                    error.err_add(self.ctx.errors, self.tokenizer.pos, 'INCOMPLETE_STATEMENT',
                                  (keywd, tok))
                    raise error.Abort
        return parent

    def translate_message_stmt(self, ref, parent, keywd, arg):
        # 例：string *** = *;
        if keywd in Proto_Base_Type:
            stmt = self.translate_base_type(ref, parent, keywd, arg)

        # 例：repeated *** *** = *;
        elif keywd in Describe_Attr:
            stmt= self.translate_describe_type(ref, parent, keywd, arg)
        # 例：*** *** = *;
        else:
            stmt = self.translate_custom_type(ref, parent, keywd, arg)

        return stmt

    def translate_definion_type(self, ref, parent, keywd, arg):
        stmt = DefinionObj(ref)
        stmt.parent = parent
        stmt.keyword = keywd
        stmt.name = arg
        stmt.pos.line = self.tokenizer.pos.line
        if parent is None:
            stmt.is_top = True
            stmt.proto_xpath = '/%s' % arg
        else:
            stmt.proto_xpath = '%s/%s' % (parent.proto_xpath, arg)
        return stmt

    def translate_describe_type(self, ref, parent, keywd, arg):
        stmt = MessageObj(ref)
        stmt.parent = parent
        stmt.scope = keywd
        stmt.num = arg.split('=')[1].lstrip()
        arg_tmp = arg.split('=')[0].rstrip()
        if len(arg_tmp.split(' ')) != 1:
            stmt.type = arg_tmp.split(' ')[0]
            stmt.name = arg_tmp.split(' ')[1]
        else:
            stmt.name = arg_tmp
        if parent is None:
            stmt.is_top = True
        stmt.pos.line = self.tokenizer.pos.line
        return stmt

    def translate_custom_type(self, ref, parent, keywd, arg):
        stmt = MessageObj(ref)
        stmt.parent = parent
        stmt.scope = 'simple'
        # 例：*** *** = *;
        if '=' in arg:
            try:
                stmt.type = parent.definions[keywd]
            except:
                stmt.type = keywd
                error.err_add(self.ctx.errors, self.tokenizer.pos, 'TYPE NOT FOUND',
                              (keywd ))
                raise error.Abort
            stmt.num = arg.split('=')[1].lstrip()
            stmt.name = arg.split('=')[0].rstrip()
        else:
            #例： *** = *;
            stmt.num = arg
            stmt.name = keywd
        if parent is None:
            stmt.is_top = True
        stmt.pos.line = self.tokenizer.pos.line
        return stmt

    def translate_base_type(self, ref, parent, keywd, arg):
        stmt = MessageObj(ref)
        stmt.parent = parent
        stmt.type = keywd
        stmt.scope = 'simple'
        stmt.num = arg.split('=')[1].lstrip()
        stmt.name = arg.split('=')[0].rstrip()
        if parent is None:
            stmt.is_top = True
        stmt.pos.line = self.tokenizer.pos.line
        return stmt

    def translate_rpc(self, parent, keywd, arg, ref):
        stmt = RpcObj(ref)
        stmt.parent = parent
        stmt.keyword = keywd
        stmt.name = arg.split(' ')[0]
        stmt.Request = arg[len(arg.split('(')[0])+1:len(arg.split(')')[0])]
        Response = arg.split('returns')[1]
        stmt.Response = Response[len(Response.split('(')[0])+1:len(Response.split(')')[0])]
        if parent is None:
            stmt.is_top = True
        stmt.pos.line = self.tokenizer.pos.line
        return stmt