#!/usr/bin/env python3
"""一键构建：GraphRAG index → filter_graph → enrich_graphml。
在任意当前目录执行均可，例如（仓库根目录）：
  python KnowledgeGraph/build_kg.py
需先 conda activate 到已安装 graphrag 的环境。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_optional_env_file(path: Path) -> None:
    """KEY=VALUE 行写入进程环境（仅当键尚未设置）。无 python-dotenv 依赖。"""
    if not path.is_file():
        return
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, _, val = s.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ[key] = val


def _apply_fast_build_defaults(graphrag_root: Path) -> None:
    """一键缩短索引：描述多路合并改为拼接（见 run_graphrag_with_fix._patch_summarize_descriptions_fast_mode）。"""
    flag = (os.environ.get("FIBERBOT_GRAPHRAG_FAST_BUILD") or "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return
    os.environ.setdefault("GRAPHRAG_SUMMARIZE_FAST", "join")
    print(
        "[build_kg] FIBERBOT_GRAPHRAG_FAST_BUILD 已启用：GRAPHRAG_SUMMARIZE_FAST=join（描述合并跳过 LLM，有损但更快）",
        file=sys.stderr,
    )


def main() -> int:
    os.chdir(SCRIPT_DIR)
    sep = os.pathsep
    os.environ["PYTHONPATH"] = str(SCRIPT_DIR) + sep + os.environ.get("PYTHONPATH", "")
    os.environ["GRAPHRAG_PRELOAD"] = "import fix_tiktoken"
    if not os.environ.get("TIKTOKEN_CACHE_DIR"):
        os.environ["TIKTOKEN_CACHE_DIR"] = str(Path.home() / ".cache" / "tiktoken")

    py = sys.executable
    graphrag_root = SCRIPT_DIR / "graphrag"
    # 可选：graphrag/.env 放 DASHSCOPE_API_KEY、GRAPHRAG_SUMMARIZE_FAST 等（勿提交密钥）
    _load_optional_env_file(graphrag_root / ".env")
    _apply_fast_build_defaults(graphrag_root)
    config_yaml = graphrag_root / "settings.yaml"
    out = graphrag_root / "output"

    print("=" * 42)
    print("KnowledgeGraph 构建（GraphRAG index）")
    print(f"输入目录: {SCRIPT_DIR / 'graphrag' / 'input'}")
    print(f"输出目录: {out}")
    print("=" * 42)

    # GraphRAG CLI flags vary by version:
    # - Older versions support: index --root <dir> --config <yaml>
    # - Newer versions may reject --config and only accept --root
    cmd_with_config = [
        py,
        str(SCRIPT_DIR / "run_graphrag_with_fix.py"),
        "index",
        "--root",
        str(graphrag_root),
        "--config",
        str(config_yaml),
    ]
    r = subprocess.run(cmd_with_config, cwd=SCRIPT_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        combined = f"{r.stdout or ''}\n{r.stderr or ''}"
        if "No such option: --config" in combined:
            print("[build_kg] Detected GraphRAG CLI without --config support; retrying with --root only.")
            cmd_root_only = [
                py,
                str(SCRIPT_DIR / "run_graphrag_with_fix.py"),
                "index",
                "--root",
                str(graphrag_root),
            ]
            r = subprocess.run(cmd_root_only, cwd=SCRIPT_DIR)
        else:
            # Preserve original output for debugging when not a flag-compat issue.
            if r.stdout:
                print(r.stdout)
            if r.stderr:
                print(r.stderr, file=sys.stderr)
    if r.returncode != 0:
        return r.returncode

    graphml = out / "graph.graphml"
    if not graphml.is_file():
        print("未生成 graph.graphml，请检查上方报错。", file=sys.stderr)
        return 1

    print()
    print("=" * 42)
    print("过滤图谱（去除噪声节点）")
    print("=" * 42)
    r = subprocess.run(
        [
            py,
            str(SCRIPT_DIR / "filter_graph.py"),
            str(out / "graph.graphml"),
            str(out / "graph_filtered.graphml"),
        ],
        cwd=SCRIPT_DIR,
    )
    if r.returncode != 0:
        return r.returncode

    print()
    print("=" * 42)
    print("为 GraphML 附加实体/关系描述（需 entities.parquet）")
    print("=" * 42)
    entities = out / "entities.parquet"
    if entities.is_file():
        r = subprocess.run(
            [
                py,
                str(SCRIPT_DIR / "enrich_graphml.py"),
                str(out / "graph_filtered.graphml"),
                str(out / "graph_filtered_enriched.graphml"),
            ],
            cwd=SCRIPT_DIR,
        )
        if r.returncode != 0:
            return r.returncode
        print("已生成: graphrag/output/graph_filtered_enriched.graphml")
    else:
        print("跳过 enrich：未找到 entities.parquet")

    print()
    print("=" * 42)
    print("完成。主要产物见 graphrag/output/")
    print("=" * 42)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
