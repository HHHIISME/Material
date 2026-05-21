#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行 GraphRAG 的包装脚本
在运行 GraphRAG 之前先应用 tiktoken 修复
"""

import sys
import os

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 导入并应用 tiktoken 修复
import fix_tiktoken

# DashScope 兼容 embedding：LiteLLM 在 encoding_format=None 时仍会传参，服务端只接受 float/base64
def _patch_litellm_embedding_encoding_format() -> None:
    import litellm

    def _fix_kwargs(kwargs: dict) -> dict:
        api_base = (kwargs.get("api_base") or "") or ""
        if "dashscope" in api_base.lower() and kwargs.get("encoding_format") is None:
            kwargs = {**kwargs, "encoding_format": "float"}
        return kwargs

    _orig_emb = litellm.embedding
    _orig_aemb = litellm.aembedding

    def embedding(*args, **kwargs):
        kwargs = _fix_kwargs(kwargs)
        return _orig_emb(*args, **kwargs)

    async def aembedding(*args, **kwargs):
        kwargs = _fix_kwargs(kwargs)
        return await _orig_aemb(*args, **kwargs)

    litellm.embedding = embedding
    litellm.aembedding = aembedding


_patch_litellm_embedding_encoding_format()


def _patch_graphrag_create_final_text_units_for_parquet() -> None:
    """GraphRAG groupby .agg(unique) 在部分 pandas/pyarrow 版本下会得到 ndarray/Arrow 类型，
    写入 parquet 时报 ArrowInvalid。将 list 列规范为 list[str] 后再落盘。"""
    import pandas as pd
    from graphrag.index.workflows import create_final_text_units as cftu_mod

    _orig = cftu_mod.create_final_text_units

    def _to_plain_str_list(val):
        if val is None:
            return []
        try:
            if isinstance(val, float) and pd.isna(val):
                return []
        except TypeError:
            pass
        if isinstance(val, (list, tuple)):
            return [str(x) for x in val]
        if hasattr(val, "tolist"):
            try:
                raw = val.tolist()
            except Exception:
                raw = val
            if isinstance(raw, list):
                return [str(x) for x in raw]
            return [str(raw)]
        try:
            if pd.isna(val):
                return []
        except (TypeError, ValueError):
            pass
        if isinstance(val, str):
            return [val]
        if hasattr(val, "__iter__") and not isinstance(val, (str, bytes)):
            return [str(x) for x in list(val)]
        return [str(val)]

    def _normalize(df):
        if df is None or getattr(df, "empty", True):
            return df
        out = df.copy()
        for col in ("document_ids", "entity_ids", "relationship_ids", "covariate_ids"):
            if col in out.columns:
                out[col] = out[col].apply(_to_plain_str_list)
        return out

    def _wrapped(*args, **kwargs):
        return _normalize(_orig(*args, **kwargs))

    cftu_mod.create_final_text_units = _wrapped


def _patch_summarize_descriptions_fast_mode() -> None:
    """可选：在「多条描述需合并」时跳过 LLM，改为拼接或取首条（有损，但大幅缩短索引时间）。

    环境变量 ``GRAPHRAG_SUMMARIZE_FAST``：
    - 未设置 / ``0`` / ``false``：保持 GraphRAG 默认（多条描述时调 LLM 汇总）。
    - ``first``：只保留第一条描述（按抽取顺序，不排序）。
    - ``join``：将多条描述排序后用换行拼接，再按长度截断（不调用 LLM）。

    说明：官方实现在 ``len(descriptions)==1`` 时已不调用 LLM；慢主要来自跨 chunk 的同名实体积累了多条描述。
    """
    mode = (os.environ.get("GRAPHRAG_SUMMARIZE_FAST") or "").strip().lower()
    if not mode or mode in ("0", "false", "off", "no"):
        return

    from graphrag.index.operations.summarize_descriptions.description_summary_extractor import (
        SummarizeExtractor,
        SummarizationResult,
    )

    _orig = SummarizeExtractor.__call__

    async def _fast_call(self, id, descriptions):  # type: ignore[no-untyped-def]
        if not descriptions:
            return await _orig(self, id, descriptions)
        if len(descriptions) == 1:
            return await _orig(self, id, descriptions)
        if mode == "first":
            text = descriptions[0]
        elif mode in ("join", "concat", "truncate", "1"):
            text = "\n".join(sorted(descriptions))
            cap = max(self._max_summary_length * 8, 2000)
            if len(text) > cap:
                text = text[:cap] + "…"
        else:
            return await _orig(self, id, descriptions)
        hard = self._max_summary_length * 12
        if len(text) > hard:
            text = text[:hard] + "…"
        return SummarizationResult(id=id, description=text)

    SummarizeExtractor.__call__ = _fast_call  # type: ignore[method-assign]


# 运行 GraphRAG CLI（需在已安装 graphrag 的 Python 中运行，例如 nanobot 的 conda 环境）
try:
    from graphrag.cli.main import app
except ImportError as e:
    print(
        "未找到 graphrag 包。请先激活已安装 GraphRAG 的 Python 环境后再运行本脚本。\n"
        "例如（conda）：conda activate <你的 nanobot 环境名>\n"
        "然后在该环境中执行：pip install -r requirements.txt（若尚未安装依赖）\n",
        file=sys.stderr,
    )
    raise SystemExit(1) from e

_patch_graphrag_create_final_text_units_for_parquet()
_patch_summarize_descriptions_fast_mode()

if __name__ == '__main__':
    sys.exit(app())

