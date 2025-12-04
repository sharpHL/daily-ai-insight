# 文档整合清理方案

## 📋 当前根目录文档分析

### 必须保留（3个）
```
✅ README.md (1.9K)              # 项目主说明
✅ CHANGELOG.md (1.4K)           # 变更日志
✅ ENV_VARS.md (1.7K)            # 环境变量配置
```

### 可整合/移动（5个，共 48KB）

重构技术文档：
```
⚠️  CALLBACK_PATTERN.md (13K)           # Callback 模式详解
⚠️  MIGRATION_GUIDE.md (6.4K)           # 迁移指南
⚠️  MIXED_LIST_HANDLING.md (10K)        # 混合列表处理
⚠️  MIXED_SOURCES_GUIDE.md (7.4K)       # 混合源指南
⚠️  SOURCE_SPECIFIC_PROCESSING.md (11K) # 源特定处理
```

**问题**：
1. 内容有重叠（都在讲混合源和 callback 模式）
2. 根目录太多技术细节文档
3. 用户第一眼看到太多 md 文件

---

## 🎯 整合方案（推荐）

### 方案 A：创建统一的开发者指南（推荐）⭐

**创建目录结构**：
```
docs/
├── guides/
│   ├── DEVELOPER_GUIDE.md        # 整合所有技术文档
│   └── API_REFERENCE.md          # API 参考（可选）
└── refactoring/                  # 已有的归档
```

**整合步骤**：
1. 创建 `docs/guides/DEVELOPER_GUIDE.md`
2. 整合内容为统一章节：
   - 第1章：快速开始（从 README 移过来）
   - 第2章：Callback 模式（CALLBACK_PATTERN.md）
   - 第3章：混合源处理（整合 MIXED_* 3个文档）
   - 第4章：迁移指南（MIGRATION_GUIDE.md）
   - 第5章：高级用法（SOURCE_SPECIFIC_PROCESSING.md）
3. 删除根目录的 5 个文档
4. README.md 精简为项目概览 + 快速开始

**优点**：
- 根目录只保留必要文档（3个）
- 技术细节统一在 docs/guides/
- 内容去重，更连贯
- 用户友好的文档结构

---

### 方案 B：移动到 docs/guides/（保守）

**目录结构**：
```
docs/
├── guides/
│   ├── callback-pattern.md
│   ├── migration-guide.md
│   ├── mixed-sources.md
│   └── advanced-processing.md
└── refactoring/
```

**步骤**：
1. 创建 `docs/guides/` 目录
2. 移动文件并重命名（小写 + 连字符）
3. 合并重复内容：
   - MIXED_LIST_HANDLING.md + MIXED_SOURCES_GUIDE.md → mixed-sources.md
   - CALLBACK_PATTERN.md → callback-pattern.md
   - MIGRATION_GUIDE.md → migration-guide.md
   - SOURCE_SPECIFIC_PROCESSING.md → advanced-processing.md

**优点**：
- 简单，改动少
- 保留文档独立性

**缺点**：
- 仍有内容重复
- 文档分散

---

### 方案 C：归档到 docs/refactoring/（最简单）

**步骤**：
```bash
mv CALLBACK_PATTERN.md \
   MIXED_LIST_HANDLING.md \
   MIXED_SOURCES_GUIDE.md \
   SOURCE_SPECIFIC_PROCESSING.md \
   docs/refactoring/

# 保留 MIGRATION_GUIDE.md（用户需要）
```

**优点**：
- 最快速
- 保留所有内容

**缺点**：
- 归档意味着"过时"，但内容还有用

---

## 📝 推荐执行方案（方案 A）

### 第 1 步：创建开发者指南骨架

```bash
mkdir -p docs/guides
```

创建 `docs/guides/DEVELOPER_GUIDE.md`：
```markdown
# 开发者指南

## 目录
1. [快速开始](#快速开始)
2. [Collector 系统](#collector-系统)
3. [Callback 模式详解](#callback-模式详解)
4. [混合源处理](#混合源处理)
5. [从旧版本迁移](#从旧版本迁移)
6. [高级用法](#高级用法)

## 快速开始
（从 README 提取核心内容）

## Collector 系统
（介绍 factory、preset、create_from_preset）

## Callback 模式详解
（整合 CALLBACK_PATTERN.md）

## 混合源处理
（整合 MIXED_LIST_HANDLING.md + MIXED_SOURCES_GUIDE.md）

## 从旧版本迁移
（整合 MIGRATION_GUIDE.md）

## 高级用法
（整合 SOURCE_SPECIFIC_PROCESSING.md）
```

### 第 2 步：精简 README.md

```markdown
# Daily AI Insight

AI 资讯聚合工具。

## 快速开始
（保留最基本的安装和使用）

## 文档
- [开发者指南](docs/guides/DEVELOPER_GUIDE.md) - 完整开发文档
- [环境变量配置](ENV_VARS.md) - 配置说明
- [更新日志](CHANGELOG.md) - 版本历史

## 功能特性
（简要列表）

## License
MIT
```

### 第 3 步：清理根目录

```bash
# 删除已整合的文档
rm CALLBACK_PATTERN.md \
   MIGRATION_GUIDE.md \
   MIXED_LIST_HANDLING.md \
   MIXED_SOURCES_GUIDE.md \
   SOURCE_SPECIFIC_PROCESSING.md
```

---

## 📊 清理效果对比

### 清理前（根目录）
```
README.md                        1.9K
CHANGELOG.md                     1.4K
ENV_VARS.md                      1.7K
CALLBACK_PATTERN.md              13K  ⬅️ 技术细节
MIGRATION_GUIDE.md               6.4K ⬅️ 技术细节
MIXED_LIST_HANDLING.md           10K  ⬅️ 技术细节
MIXED_SOURCES_GUIDE.md           7.4K ⬅️ 技术细节
SOURCE_SPECIFIC_PROCESSING.md    11K  ⬅️ 技术细节
─────────────────────────────────────
总计: 8 个文件，52.8K
```

### 清理后（根目录）
```
README.md                        ~1K  ✅ 精简
CHANGELOG.md                     1.4K ✅
ENV_VARS.md                      1.7K ✅
─────────────────────────────────────
总计: 3 个文件，4.1K

docs/guides/DEVELOPER_GUIDE.md   ~45K ✅ 统一整合
```

**改进**：
- 根目录文件数：8 → 3 (-62%)
- 根目录大小：52.8K → 4.1K (-92%)
- 用户友好度：⬆️⬆️⬆️
- 内容组织性：⬆️⬆️⬆️

---

## 🚀 快速执行命令

### 选择方案 A（推荐）：
```bash
# 第 1 步：创建目录和统一指南
mkdir -p docs/guides

# 第 2 步：手动创建 DEVELOPER_GUIDE.md（整合内容）
# （需要人工整合内容）

# 第 3 步：清理根目录
rm CALLBACK_PATTERN.md \
   MIGRATION_GUIDE.md \
   MIXED_LIST_HANDLING.md \
   MIXED_SOURCES_GUIDE.md \
   SOURCE_SPECIFIC_PROCESSING.md

echo "✅ 文档整合完成！"
```

### 选择方案 C（快速）：
```bash
# 全部移到归档
mv CALLBACK_PATTERN.md \
   MIXED_LIST_HANDLING.md \
   MIXED_SOURCES_GUIDE.md \
   SOURCE_SPECIFIC_PROCESSING.md \
   docs/refactoring/

# MIGRATION_GUIDE.md 保留或移到 docs/guides/
mkdir -p docs/guides
mv MIGRATION_GUIDE.md docs/guides/

echo "✅ 文档归档完成！"
```

---

## ⚖️ 方案选择建议

| 方案 | 工作量 | 效果 | 推荐度 |
|------|--------|------|--------|
| A - 统一指南 | 高（需整合内容）| 最佳 | ⭐⭐⭐⭐⭐ |
| B - 分散移动 | 中 | 良好 | ⭐⭐⭐ |
| C - 快速归档 | 低 | 一般 | ⭐⭐ |

**推荐**：如果有时间，选择方案 A；如果想快速清理，选择方案 C。

---

## ✅ 下一步行动

1. **决定方案**：A、B 或 C
2. **执行清理**：按照对应方案执行
3. **更新 README**：添加文档链接
4. **Git 提交**：
   ```bash
   git add -A
   git commit -m "docs: consolidate technical documentation into guides/"
   ```

---

**创建时间**: 2025-11-25
**目的**: 保持项目根目录简洁、文档组织清晰
