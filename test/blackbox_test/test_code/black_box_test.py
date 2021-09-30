#Copyright (C) 2021. Huawei Technologies Co., Ltd. All rights reserved.

#This program is free software; you can redistribute it and/or modify
#it under the terms of the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#Apache License, Version 2.0 for more details.

from __future__ import unicode_literals
# -*- coding=UTF-8 -*-

import os
import sys
from pathlib import Path

sys.path.append(".")
import unittest
from black_box_check_func import *


def test_trans_yang_proto(cur_path, src_path, yang_path=None, yang_dependencies=None,src_proto=None,log_path=None,expect_proto=None):
    # file_type_list = [file for file in os.listdir(cur_path)]
    p = CheckOutFile()
    # for file_type in file_type_list:
    if yang_path is None:
        yang_path = os.path.join(cur_path,'yang')
    if yang_dependencies is None:
        yang_dependencies = os.path.join(cur_path,'yang_dependencies')
    if src_proto is None:
        src_proto = os.path.join(cur_path,'src_proto')
    if log_path is None:
        log_path = os.path.join(cur_path,'logs')
    if expect_proto is None:
        expect_proto = os.path.join(cur_path,'expect_proto')
    proto_path = os.path.join(cur_path,'proto')
    cmd_list = ['python ', os.path.abspath(src_path) + '/translate_yang2proto.py -Y ', yang_path, ' -O ',
                proto_path, ' -L ', log_path]
    if os.path.exists(yang_dependencies) :
        cmd_list = cmd_list + [' -D ', yang_dependencies]
    if os.path.exists(src_proto):
        cmd_list = cmd_list + [' -S ', src_proto]
    cmd = ''.join(cmd_list)
    print(cmd)
    os.system(cmd)
    testcase = unittest.TestCase()
    testcase.assertEqual(True, p.check_out_path(expect_proto, proto_path))


class TestYangProtoNormalFunction(unittest.TestCase):
    def setUp(self):
        print("run before every test_case")

    def tearDown(self):
        print("run after every test_case")

    def test_Yang_Translate_Proto_module_single(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'normal_generate_proto',
                                'test-single-module',"test_single_module_aaa")
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path,yang_path=os.path.join(cur_path,'yang','huawei-aaa.yang'))

    def test_Yang_Translate_Proto_module_all(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'normal_generate_proto',
                                'test-all-module','test-all-module')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


class TestProtoYangTranslate(unittest.TestCase):
    def setUp(self):
        print("run before every test_case")

    def tearDown(self):
        print("run after every test_case")

    def test_Proto_Yang_Normal_translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'old_proto_yang_translate', 'test_normal_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)

    def test_Yang_Nodes_Change_Order(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'old_proto_yang_translate',
                                'test_yang_nodes_change_order')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


    def test_Proto_Yang_Node_inerst_middle(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'old_proto_yang_translate',
                                'test_yang_nodes_insert_middle')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)




class TestYangTranslateConvertRules(unittest.TestCase):
    def setUp(self):
        print("run before every test_case")

    def tearDown(self):
        print("run after every test_case")

    def test_Yang_Type_Translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_yang_type_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


    def test_Yang_Keyword_Translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_yang_keyword_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


    def test_Proto_Yang_Support_augment(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_support_augment', 'test_proto_yang_support_augment')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


    def test_Yang_Support_augment(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_support_augment', 'test_yang_support_augment')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path)


    def test_Name_Container_Translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_translate_name_rules', 'test_name_container_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path,module='huawei-aaa')
    def test_Name_Enum_Translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_translate_name_rules', 'test_name_enum_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path, module='huawei-aaa')

    def test_Name_leaf_translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_translate_name_rules', 'test_name_leaf_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path, module='huawei-aaa')
    def test_Name_list_translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_translate_name_rules', 'test_name_list_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path, module='huawei-aaa')

    def test_Name_Repeated_Translate(self):
        print("run test_case  test_Yang_Translate_Proto_Normal_Function..")
        cur_path = os.path.join('..', 'black_box', 'yang_proto', 'yang_translate_proto_convert_rules',
                                'test_translate_name_rules', 'test_name_repeated_translate')
        src_path = os.path.join('../../..', 'src')
        test_trans_yang_proto(cur_path, src_path, module='huawei-aaa')


if __name__ == '__main__':
    unittest.main()
