# KnowledgeGraph — 从文本构建知识图谱

本目录是从 **fibergpt** 项目中抽离的**独立子项目**，只做一件事：把 `graphrag/input/` 下的 `.txt` / `.md` 语料，通过 **Microsoft GraphRAG** 流水线抽实体与关系，生成 **GraphML**、**parquet** 等产物，便于后续可视化或问答。

**nanobot**：内置技能 **`knowledge-graph`** 与工具 **`knowledge_graph_pipeline`**（文献 → 写入 `graphrag/input/` → 调用 `build_kg.py`）。若 nanobot 从 **本仓库 `nanobot/`** 以可编辑方式安装，一般**无需**配置路径；否则请设置 **`FIBERBOT_ROOT`** 或传入 **`repo_root`**。

---

## 目录结构

```
KnowledgeGraph/
├── README.md                 # 本说明
├── requirements.txt          # Python 依赖
├── build_kg.py               # 一键构建（index + 过滤 + enrich）
├── fix_tiktoken.py           # 离线环境 tiktoken 修复（GraphRAG 依赖）
├── run_graphrag_with_fix.py  # 调用 GraphRAG CLI（先加载 fix_tiktoken）
├── filter_graph.py           # 过滤图谱中的噪声节点
├── enrich_graphml.py         # 用 entities/relationships 为 GraphML 补全描述
├── scripts/
│   └── stat_extraction.py    # 可选：统计 chunk / 节点数量
└── graphrag/                 # GraphRAG 工程根（--root 指向这里）
    ├── settings.yaml         # 模型、路径、分块、提示词等（默认与 nanobot Qwen/DashScope 对齐）
    ├── prompts/              # 抽取图、摘要、检索等提示词（中文为主）
    ├── input/                # 【你放语料的地方】.txt / .md
    ├── output/               # 构建产物（运行后生成，已 .gitignore）
    ├── cache/                # 缓存（已 .gitignore）
    └── logs/                 # 日志（已 .gitignore）
```

---

## 环境准备

1. **Python** `>= 3.10, < 3.14`（与 nanobot 一致时可用同一 conda 环境，避免混用系统 Python。）

2. **激活 conda 环境并安装依赖**  
   GraphRAG 与本目录脚本应在**你已安装 nanobot / graphrag 的 conda 环境**中运行，例如：

   ```bash
   conda activate <你的 nanobot 环境名>
   cd KnowledgeGraph
   pip install -r requirements.txt
   ```

   若 `graphrag` 已在该环境中装好，可只根据报错补装 `pandas`、`networkx`、`lxml` 等。

3. **Qwen / DashScope（默认，与 nanobot 一致）**  
   `settings.yaml` 已按 **阿里云百炼 OpenAI 兼容模式** 配置（与 nanobot 文档中 `providers.dashscope`、`apiBase: https://dashscope.aliyuncs.com/compatible-mode/v1` 一致）：

   - 对话：`qwen-plus`（可改为 `qwen-turbo`、`qwen-max` 等）
   - 向量：`text-embedding-v3`（LanceDB `vector_size` 已设为 1024，与默认维度一致）
   - 在 **Windows 系统环境变量** 中设置 **`DASHSCOPE_API_KEY`**（与 nanobot / DashScope 使用同一变量名）。`settings.yaml` 通过 `${DASHSCOPE_API_KEY}` 读取。
   - **nanobot**：可在 `~/.nanobot/config.json` 的 `providers.dashscope` 里**删除 `apiKey` 或留空**——当前版本会在密钥为空时**自动使用**系统环境变量 `DASHSCOPE_API_KEY`，这样 config 里不再出现明文 key。

4. **若改用本地 vLLM（Qwen）**  
   将 `default_chat_model` 的 `api_base` 改为 `http://127.0.0.1:8000/v1`，`api_key` 为 `dummy`，`model` 改为 vLLM 注册的名称；向量可继续用 DashScope，或单独改 `default_embedding_model`。

5. **tiktoken**  
   GraphRAG 需要 `cl100k_base` 编码文件；若离线，请将 `cl100k_base.tiktoken` 放到 `~/.cache/tiktoken/`，或使用本仓库的 `fix_tiktoken.py`（由 `build_kg.py` / `run_graphrag_with_fix.py` 通过 `GRAPHRAG_PRELOAD` 预加载）。

---

## 使用流程

1. **配置密钥与模型**  
   默认走 DashScope：确保本机已配置 **系统环境变量 `DASHSCOPE_API_KEY`**（设置后需**重新打开**终端，IDE 有时也需重启）。  
   如需换模型或本地 vLLM，编辑 `graphrag/settings.yaml` 顶部注释与 `models` 段。

2. **放入语料**  
   将 `.txt` 或 `.md` 文件放入 `graphrag/input/`（可删除示例 `sample.txt` 后替换为你的文档）。

3. **执行构建**（先 `conda activate` 到上述环境）

   在**仓库根目录**或任意目录均可（脚本会定位自身路径）：

   ```bash
   python KnowledgeGraph/build_kg.py
   ```

   Windows（CMD / PowerShell）同理：

   ```bat
   python KnowledgeGraph\build_kg.py
   ```

   若不用一键脚本，可在 `KnowledgeGraph` 目录下手动执行：

   ```bash
   export PYTHONPATH="$(pwd):${PYTHONPATH}"
   export GRAPHRAG_PRELOAD="import fix_tiktoken"
   python3 run_graphrag_with_fix.py index --root "$(pwd)/graphrag" --config "$(pwd)/graphrag/settings.yaml"
   python3 filter_graph.py graphrag/output/graph.graphml graphrag/output/graph_filtered.graphml
   python3 enrich_graphml.py graphrag/output/graph_filtered.graphml graphrag/output/graph_filtered_enriched.graphml
   ```

   Windows 下把 `python3` 换成 `python` 即可。

   `build_kg.py` 会依次执行：

   - `graphrag index`：分块、嵌入、**从文本抽取实体与关系**、生成图快照等  
   - `filter_graph.py`：生成 `graph_filtered.graphml`  
   - `enrich_graphml.py`：生成带节点描述的 `graph_filtered_enriched.graphml`（需 `entities.parquet` 已存在）

4. **主要产物**（均在 `graphrag/output/`）

   - `graph.graphml` / `graph_filtered.graphml`：知识图谱  
   - `entities.parquet`、`relationships.parquet`：实体与关系表  
   - `documents.parquet`、`text_units.parquet` 等：中间与检索数据  
   - `lancedb/`：向量库（若启用）

5. **可选统计**

   ```bash
   python3 scripts/stat_extraction.py graphrag/output
   ```

---

## 构建流程有多长？为什么会觉得「太久」？

`build_kg.py` 本身只有 **三步**：`graphrag index` → `filter_graph.py` → `enrich_graphml.py`。真正耗时的是 **第一步**。

### GraphRAG `index` 在做什么（简化理解）

在 `graphrag/settings.yaml` 配置下，一次完整索引大致包括：

| 阶段 | 主要工作 | 耗时来源 |
|------|----------|----------|
| 分块 / 读入 | 按 `chunks.size`（默认 450 字符）切分语料 | 语料越长 → chunk 越多 |
| 文本嵌入 | 对每个 text unit 调向量 API（百炼 embedding） | chunk 数 × 批大小（`embed_text.batch_size`，百炼多为 10） |
| 抽取图 | 每块调 **对话模型** 抽实体/关系（`extract_graph`，可 `max_gleanings` 多轮） | **LLM 调用次数多** |
| **描述汇总** | 对**每个实体、每条边**再调 LLM 把多条描述压成一条（`summarize_descriptions`） | **≈ 实体数 + 关系数 次调用**（日志里常见 `Summarize … progress: x/N`，N 可达数千） |
| 社区 / 嵌入图等 | Leiden 聚类、可选 UMAP、社区摘要等 | 社区多时仍有大量 LLM 调用；本仓库可将 `community_reports.enabled` 设为 `false` 以减轻一部分负担 |

因此：**不是脚本「步骤写多了」**，而是 **GraphRAG 索引 = 大量远程 API（嵌入 + 对话）**，语料稍多或图谱稍密，总时间就会到 **数十分钟甚至更久**；若外层工具（如 nanobot）设了 **1200s 超时**，还会出现「子进程其实还在跑但被杀死」的现象。

### 想缩短构建时间，可以怎么做（按影响从大到小）

1. **控制输入规模**：更少文献篇数、更短语料、检索时降低 `max_per_keyword_per_year`（nanobot 侧）。  
2. **减少 chunk 数量**：适度 **增大** `chunks.size`（例如 600–900），或略减小 `overlap`（会略损连贯性，需自行权衡）。  
3. **减轻抽取强度**：将 `extract_graph.max_gleanings` 从 `2` 改为 **`1`**（少一轮 gleaning，调用减半量级相关）。  
4. **提高并发**：在百炼配额允许下，适当 **增大** `models.*.concurrent_requests`（默认 4，可试 8，视限流而定）。  
5. **换更快/更便宜的对话模型做索引**：例如将构建用的 `default_chat_model.model` 改为 `qwen-turbo`（质量略降，速度通常更好）。  
6. **关掉非必需步骤**（若你使用的 GraphRAG 版本支持）：例如 `umap.enabled: false` 可省本地降维；`community_reports.enabled: false` 本仓库已示例关闭。  
7. **仅延长等待，不减少工作**：把 nanobot 的 `knowledge_graph_timeout_seconds` 调到 **3600** 或更高，避免误杀长任务。

> **说明**：「实体/关系描述汇总」是 GraphRAG 保证检索质量的重要环节，**不能简单删掉一步就等价替代**；要明显变快，本质上是 **少抽、少块、少实体/边** 或 **更高并发/更快模型**。

---

## 与主项目 fibergpt 的关系

- **原路径**：主仓库中曾使用 `fibergpt/graphrag/`、`run_graphrag_vllm.sh`、`filter_graph.py`、`enrich_graphml.py` 等。  
- **本目录**：复制并精简为**仅与图谱构建相关的文件**，便于单独维护或迁移到其他项目。  
- 主项目中的可视化（如 `visualize_3d.html`）、问答服务（`serve_visualize.py`）等**未包含在本目录**；需要时可自行把 `graphrag/output/*.graphml` 接到你的可视化工具。

---

## 常见问题

- **`ModuleNotFoundError: No module named 'graphrag'`**  
  说明当前终端用的不是装有 graphrag 的 Python。请先 `conda activate <nanobot 环境名>`，再在同一终端里执行 `python KnowledgeGraph/build_kg.py` 或 `python run_graphrag_with_fix.py`。

- **认证失败 / 未读到 `DASHSCOPE_API_KEY`**  
  确认已在「系统环境变量」中设置该变量，并**重新打开 CMD / PowerShell**（从菜单启动的 IDE 若读不到新变量，需重启 IDE）。

- **Embedding 报错 `encoding_format` only support with [float, base64]**（百炼 / DashScope）  
  `run_graphrag_with_fix.py` 已对 LiteLLM 做补丁：在 `api_base` 含 `dashscope` 时把 `encoding_format` 设为 `float`。请始终通过 `build_kg.py` 或 `run_graphrag_with_fix.py` 调用 GraphRAG，不要直接 `graphrag index`。

- **`create_final_text_units` 写 parquet 报 `ArrowInvalid` / `entity_ids`**（pandas 2.x + PyArrow）  
  同一脚本内已 monkeypatch `create_final_text_units`，将 `document_ids` / `entity_ids` 等列规范为普通 `list[str]` 再落盘。

- **Embedding 报 `batch size ... should not be larger than 10`**（百炼 text-embedding）  
  `settings.yaml` 里 `embed_text.batch_size` 已设为 **10**（不要超过服务端限制）。

- **CMD 下 GBK 与 Unicode**  
  `filter_graph.py` / `enrich_graphml.py` 的成功提示已改为 `[OK]`，避免在默认 GBK 控制台打印 `✓` 报错。

- **构建很慢 / 失败**  
  检查 DashScope 配额与网络；若改用本地 vLLM，再检查服务是否可达、显存与 `max_input_tokens` / chunk 大小是否匹配。

- **只想改抽取领域**  
  编辑 `graphrag/prompts/extract_graph_chinese.txt` 与 `settings.yaml` 里的 `entity_types`、`extract_graph.prompt`。

- **输出目录为空**  
  确认 `graphrag/input/` 下至少有一个匹配 `file_pattern` 的文件，且 `settings.yaml` 中 `input.base_dir` 为 `input`（相对 `graphrag` 根目录）。

---

## 许可证

与主项目 fibergpt 保持一致；GraphRAG 本身遵循其上游许可证。
