#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright: (c) Huawei Technologies Co., Ltd. 2021. All rights reserved.
"""Description of PROTO syntax."""

import re

### Regular expressions - constraints on arguments

# keywords and identifiers
identifier = r"[_A-Za-z][._\-A-Za-z0-9]*"
keyword = '((' + identifier + '):)?(' + identifier + ')'
comment = '(/\*([^*]|[\r\n\s]|(\*+([^*/]|[\r\n\s])))*\*+/)|(//.*)|(/\*.*)'
num = r'0-9'

re_keyword = re.compile(keyword)
re_comment = re.compile(comment)