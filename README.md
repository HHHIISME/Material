# 材料学院智能学习平台

> 基于大语言模型的材料科学智能问答与知识检索系统

## 🎯 项目简介

材料学院智能学习平台是一个面向材料科学与工程学科的智能问答系统，具备以下核心功能：

- 🤖 **智能问答** - 基于知识库的精准问答
- 🖼️ **图片检索** - 文本搜图、上下文图片推荐
- 📊 **PPT生成** - 智能生成教学/汇报PPT
- 📚 **知识库管理** - 教材、文献、论文的知识入库

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL + Milvus (向量库) + Redis
- **LLM**: 智谱 GLM-4
- **文档处理**: PyMuPDF, python-docx
- **对象存储**: MinIO

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand

### 基础设施
- **容器化**: Docker + Docker Compose
- **向量检索**: Milvus

## 🚀 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd Material

# 启动所有服务
docker compose up -d

# 访问
# 前端: http://localhost:5173
# API文档: http://localhost:8000/docs
```

详细开发指南请查看 [开发指南](docs/开发指南.md)

## 📖 文档

- [PRD 文档](prd.md)
- [技术需求文档](技术需求.md)
- [任务清单](任务清单.md)

## 📁 项目结构

```
Material/
├── backend/          # 后端服务
├── frontend/         # 前端服务
├── docker/           # Docker 配置
├── docs/             # 文档
├── data/             # 数据目录
└── docker-compose.yml
```

## 📝 开发状态

当前阶段: **项目初始化**

详见 [任务清单](任务清单.md)

## 📜 License

MIT License
