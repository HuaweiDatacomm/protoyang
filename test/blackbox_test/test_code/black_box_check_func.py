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
import sys
import os
import re
import shutil
import binascii
import time
import linecache

init_file_name = '_.gitkeep'


class ReplacePath():
    def __init__(self):
        pass

    @staticmethod
    def replace_str_slash(string):
        """ function:replace '\' to '/'.
            linux path is '/';
            windows path is '\';
            we should make them same to compare.

            Args:
                string: string or string list.

            Returns:
                none.

            Raises:
                none.
        """
        if type(string) is list:
            new_str = [s_str.replace('\\', '/') for s_str in string]
        elif type(string) is str:
            new_str = string.replace('\\', '/')
        else:
            return string
        return new_str


class CheckOutFile(object):
    def __init__(self):
        pass

    def compare_file_crc(self, expect_file, real_file):
        """ function:compare file crc.

            Args:
                except_file: file1.
                real_file: file2.

            Returns:
                True/False
                if two files is same, return True;else return True

            Raises:
                none.
        """
        crc32_file1 = self.get_file_crc_num(expect_file)
        crc32_file2 = self.get_file_crc_num(real_file)
        if crc32_file1 == crc32_file2:
            return True
        print('BLACK_BOX_ERROR: file %s is diff with expect !'% real_file)
        return False

    @staticmethod
    def get_file_crc_num(file):
        """ function:get file crc.

            Args:
                file: file path.

            Returns:
                crc value.

            Raises:
                none.
        """
        # reads = open(file, encoding="UTF-8")
        # read_str = reads.read()
        # reads.close()
        def get_lineno(file):
            for lineno in range(5, 20):
                line = linecache.getline(file, lineno)
                if line.find("package") != -1:
                    return lineno
        lineno = get_lineno(file)
        read = linecache.getlines(file)[int(lineno):]

        read_str = ''.join(read)
        crc32 = (binascii.crc32(bytes(read_str, 'utf-8'))) & 0xffffffff
        return crc32

    @staticmethod
    def special_rule_deal(except_error_list):
        """ function:deal all logs error with all special rules.

            Args:
                except_error_list: error list.
            Returns:
                new except_error_list
            Raises:
                none.
        """
        def replace_except_to_real(error_list):
            replace_error_list = [error.replace('except_output', 'actual_output')
                                  for error in error_list]
            return replace_error_list

        def occur_twice_in_diff_white_files(error_list):
            occur_error_list = []
            for error in error_list:
                index = error.find('occured twice')
                if index != -1:
                    error = error[0:index] + 'occured twice'
                occur_error_list.append(error)
            return occur_error_list

        def delete_traceback(error_list):
            for error in error_list:
                if error.find('most recent call last') != -1:
                    error_list.remove(error)
            return error_list

        new_error_list = replace_except_to_real(except_error_list)
        new_error_list = occur_twice_in_diff_white_files(new_error_list)
        new_error_list = delete_traceback(new_error_list)

        return new_error_list

    def check_out_path(self, except_out_put_path, real_out_put_path):
        """ function:check all files crc between two different path.
                    both of them could have child folder.

            Args:
                except_out_put_path: path1.
                real_out_put_path: path2.
            Returns:
                True/False
                if two path file is same, return True;else return True
            Raises:
                none.
        """
        for file in os.listdir(except_out_put_path):
            if os.path.isdir(os.path.join(except_out_put_path, file)):
                if not self.check_out_path(os.path.join(except_out_put_path, file),
                                           os.path.join(real_out_put_path, file)):
                    print('false1')
                    return False
            elif file in os.listdir(real_out_put_path):
                if not self.compare_file_crc(
                    os.path.join(except_out_put_path, file),
                        os.path.join(real_out_put_path, file)):
                    print('2')
                    return False
            elif file == init_file_name:
                continue
            else:
                print('BLACK_BOX_ERROR: file %s missing which expected to be out!' % file)
                print('3')
                return False
        return True

    def check_out_yang_proto_log(self, except_out_log, real_out_log):
        """ function:check all files crc between two different path.
                    both of them could have child folder.

            Args:
                except_out_put_path: path1.
                real_out_put_path: path2.
            Returns:
                True/False
                if two path file is same, return True;else return True
            Raises:
                none.
        """

        def parse_error_and_exit(filename):
            handle = None
            try:
                handle = open(filename, encoding="utf-8")
                error_context = handle.read()
                find_re = re.compile(r"ERROR\S*:(.+?)\n", re.DOTALL)
                error_list = find_re.findall(error_context)
                p = ReplacePath()
                new_error_list = p.replace_str_slash(error_list)
                new_error_list = self.special_rule_deal(new_error_list)
                return new_error_list
            except Exception:
                print('BLACK_BOX_ERROR: can not open log file ',filename)
                return []
            finally:
                if handle is not None:
                    handle.close()

        except_error_list = parse_error_and_exit(except_out_log)

        real_error_list = parse_error_and_exit(real_out_log)
        if len(except_error_list) != len(real_error_list):
            print('BLACK_BOX_ERROR: log file error num is differ between except ', real_out_log)
            return False

        for error in except_error_list:
            error = error.replace('except_output','actual_output')
            if error not in real_error_list:
                print('BLACK_BOX_ERROR: log file %s error %s is differ between except ' % (real_out_log , error))
                return False
        return True

    def check_all_log_files(self, except_out_log_path, real_out_log_path):
        """ function:check all logs error between two different path.
                    both of them could have child folder.

            Args:
                except_out_put_path: path1.
                real_out_put_path: path2.
            Returns:
                True/False
                if two path log error is same, return True;else return True
            Raises:
                none.
        """
        for file in os.listdir(except_out_log_path):
            if file == init_file_name:
                continue
            except_out_log = os.path.join(except_out_log_path, file)
            real_out_log = os.path.join(real_out_log_path, file)
            if os.path.isfile(os.path.join(except_out_log_path, file)) and 'log' in file:
                if not self.check_out_yang_proto_log(except_out_log, real_out_log):
                    return False
            else:
                if not self.check_all_log_files(except_out_log, real_out_log):
                    return False
        return True


class CreateActualOutputPath(object):
    def __init__(self):
        pass

    def create_output_path(self, input_path, output_path):
        """ function:create same structure from except .
                    both of them could have child folder.

            Args:
                input_path: path1.
                output_path: path2.
            Returns:
                none.
            Raises:
                none.
        """
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        for file in os.listdir(input_path):
            if os.path.isdir(os.path.join(input_path, file)):
                child_output_path = os.path.join(output_path, file)
                child_input_path = os.path.join(input_path, file)
                if os.path.isdir(child_output_path):
                    shutil.rmtree(child_output_path)
                    time.sleep(2)
                os.mkdir(child_output_path)
                self.create_output_path(child_input_path,
                                        child_output_path)
            else:
                continue

# if __name__ == '__main__':
#     p = CheckOutFile()
#     # p.get_file_crc_num('D:\work\code\white_code\test\black_test\protoyang\black_box\yang_proto\yang_translate_proto\normal_generate_proto\module-aaa\output\file')
#     cache = linecache.getlines(r'D:\work\code\white_code\test\black_test\protoyang\black_box\yang_proto\yang_translate_proto\normal_generate_proto\module-aaa\output\file\huawei-aaa.proto')[10:]
#     print(''.join(cache))
