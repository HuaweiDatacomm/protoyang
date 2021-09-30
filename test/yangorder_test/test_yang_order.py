#Copyright (C) 2021. Huawei Technologies Co., Ltd. All rights reserved.

#This program is free software; you can redistribute it and/or modify
#it under the terms of the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#Apache License, Version 2.0 for more details.

import unittest
import sys
from translate_yang2proto import *
sys.path.append('src')

PATH = os.path.abspath(r'.')
YANG_PATH = os.path.join(PATH, r'yang')
EXPECT_RESULT_PATH = os.path.join(PATH, r'expect_result')
REAL_RESULT_PATH = os.path.join(PATH, r'real_result')
OLD_PROTO_PATH = os.path.join(PATH, r'oldProto')
FILE_TYPE = '.proto'
CMD_PATH = os.path.abspath(r'..\..\src')


def read_file(filename):
    fd = None
    text = ''
    try:
        fd = open(filename, "r", encoding="utf-8")
        text = fd.readlines()
    except Exception:
        print("can not open the file %s" % filename)
    finally:
        if fd is not None:
            fd.close()

    return text


def _remove_compiled_str(str):
    for line in str:
        if line.startswith('// compiled'):
            str.remove(line)
            break

    return str


def compare_proto(module):
    proto_file_name = module + FILE_TYPE
    real_proto_file = os.path.join(REAL_RESULT_PATH, proto_file_name)
    expect_proto_file = os.path.join(EXPECT_RESULT_PATH, proto_file_name)

    real_text = read_file(real_proto_file)
    expect_text = read_file(expect_proto_file)
    if real_text == '' or expect_text == '':
        return False

    # remove compiled info
    real_text = _remove_compiled_str(real_text)
    expect_text = _remove_compiled_str(expect_text)
    return real_text == expect_text


def get_log_errer_msg(log_content):
    error_msgs = []
    for line in log_content:
        line_list = line.strip().split(',')
        expect_str = line_list[2] + ','

        in_str = line_list[4].split(' ')

        error_str = in_str[0].split(':')[1]
        for i in range(1, len(in_str) - 1):
            error_str += ' ' + in_str[i]

        file_str = in_str[len(in_str) - 1]
        file_pos = file_str.rfind('\\')
        file_name = file_str[file_pos + 1:]

        expect_str += error_str + ' ' + file_name
        error_msgs.append(expect_str)
        print(expect_str)

    return error_msgs


def compare_log(module):
    expect_log_file = os.path.join(EXPECT_RESULT_PATH, 'convert_yang2proto_' + module + '.log')
    log_file = os.path.join(PATH, 'convert_yang2proto.log')
    real_log_fd = None
    expect_log_fd = None

    try:
        real_log_fd = open(log_file, 'r', encoding='utf-8')
        expect_log_fd = open(expect_log_file, 'r', encoding='utf-8')
        real_log_content = real_log_fd.readlines()
        expect_log_content = expect_log_fd.readlines()
        real_error_msgs = get_log_errer_msg(real_log_content)
        expect_error_msgs = get_log_errer_msg(expect_log_content)
        if real_error_msgs == expect_error_msgs:
            print('real_error_msgs == expect_error_msgs')
            return True
        else:
            print('real_error_msgs != expect_error_msgs')
            return False
    except Exception:
        print('can not open log:', log_file)
    finally:
        if real_log_fd is not None:
            real_log_fd.close()
        if expect_log_fd is not None:
            expect_log_fd.close()

    return False

def generate_real_proto_file(yang_path=None):
    cmdstr = os.path.join(CMD_PATH, 'translate_yang2proto.py')
    if not os.path.exists(REAL_RESULT_PATH):
        os.mkdir(REAL_RESULT_PATH)
    cmdstr = cmdstr + r' -Y ' + YANG_PATH  + ' -S ' + OLD_PROTO_PATH + ' -O ' + REAL_RESULT_PATH + \
        ' -D ' + PATH
    print('cmdstr:', cmdstr)
    os.system(cmdstr)


class TestTransYang2Proto(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('setUpClass')

    @classmethod
    def tearDownClass(cls):
        print('tearDownClass')

    #test the .proto nodes order of common yang file (except grouping/augment)
    def testCommonYangOrder(self):
        module = 'test-common'
        generate_real_proto_file(module)
        self.assertTrue(compare_proto(module))


    # test the .proto nodes order of  uses grouping
    def testUsesGroupingYangOrder(self):
        module = 'test-uses-grouping'
        generate_real_proto_file(module)
        self.assertTrue(compare_proto(module))

    # test the .proto nodes order of augment
    def testAugmentYangOrder(self):
        module = 'test-augment'
        base_module = 'test-augment-base'
        generate_real_proto_file(module)
        generate_real_proto_file(base_module)
        self.assertTrue(compare_proto(module))
        self.assertTrue(compare_proto(base_module))

    # test the .proto nodes order of yang file including old .proto
    def testOldProtoYangOrder(self):
        module = 'test-old-proto'
        generate_real_proto_file(module)
        self.assertTrue(compare_proto(module))

    # test the .proto nodes order of enumeration with all values
    def testAllEnumValue(self):
        module = 'test-all-enum-have-value'
        generate_real_proto_file(module)
        self.assertTrue(compare_proto(module))

    # test the .proto nodes order of enumeration with part values
    def testSomeEnumValue(self):
        module = 'test-some-enum-have-value'
        generate_real_proto_file(module)
        self.assertTrue(compare_proto(module))



if __name__ == '__main__':
    unittest.main()
