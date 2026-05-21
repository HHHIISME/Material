#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 tiktoken 离线加载问题
强制使用本地缓存的编码文件
"""

import os
import sys

# 在导入 tiktoken 之前设置环境变量
os.environ['TIKTOKEN_CACHE_DIR'] = os.path.expanduser('~/.cache/tiktoken')

# 导入 tiktoken 并 patch 加载函数
import tiktoken
from tiktoken import load

# 保存原始函数
_original_read_file_cached = load.read_file_cached
_original_load_tiktoken_bpe = load.load_tiktoken_bpe

# 本地文件路径
CACHE_DIR = os.path.expanduser('~/.cache/tiktoken')
CL100K_BASE_PATH = os.path.join(CACHE_DIR, 'cl100k_base.tiktoken')

def patched_read_file_cached(blobpath: str, expected_hash: str | None = None) -> bytes:
    """Patch read_file_cached 以使用本地文件"""
    # 如果是 cl100k_base 的 URL，使用本地文件
    if 'cl100k_base' in blobpath and os.path.exists(CL100K_BASE_PATH):
        print(f"[tiktoken] 使用本地文件: {CL100K_BASE_PATH}")
        with open(CL100K_BASE_PATH, 'rb') as f:
            return f.read()
    
    # 否则使用原始函数
    try:
        return _original_read_file_cached(blobpath, expected_hash)
    except Exception as e:
        # 如果下载失败且是 cl100k_base，尝试使用本地文件
        if 'cl100k_base' in blobpath and os.path.exists(CL100K_BASE_PATH):
            print(f"[tiktoken] 下载失败，使用本地文件: {CL100K_BASE_PATH}")
            with open(CL100K_BASE_PATH, 'rb') as f:
                return f.read()
        raise

# 应用 patch
load.read_file_cached = patched_read_file_cached

# 如果是作为 PYTHONSTARTUP 脚本运行，不执行测试代码
if __name__ == '__main__':
    try:
        enc = tiktoken.get_encoding('cl100k_base')
        print('[OK] tiktoken 编码加载成功（使用本地文件）')
        test_text = 'Hello, world!'
        tokens = enc.encode(test_text)
        print(f'[OK] 测试编码成功: "{test_text}" -> {len(tokens)} tokens')
    except Exception as e:
        print(f'✗ 失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

