# 参考目标
A personal daily intel pipeline that fetches data, lets LLM analyze it, and pushes concise briefings to me.

## 可以借鉴的项目
1. 可以借鉴这个项目 `https://github.com/justlovemaki/CloudFlare-AI-Insight-Daily` 中的依赖FOLO这个数据源，可以首先像素级复制这个项目的数据搜集和处理流程
2. 未来可以加入更多的数据源比如`https://github.com/ourongxing/newsnow` 以及消化数据方法 `https://github.com/sansan0/TrendRadar`


## 可能的仓库结构（可以修改如果你认为有必要）
``` bash
daily-insight/
  ├─ collectors/      # 各种数据源：GitHub Trending、HN、RSS、财经、龙虎榜等
  ├─ processors/      # 清洗 + 去重 + 结构化
  ├─ llm/             # prompt 模板、调用封装、多模型适配
  ├─ renderers/       # 输出到 Markdown、HTML、Notion、Telegram、邮件等
  ├─ scheduler/       # cron / GitHub Actions / 自建 scheduler
  ├─ configs/         # 每日报告配置：频道、权重、过滤规则
  └─ README.md        # 项目介绍、架构图、使用说明
```

## 要求
1. 主要编程语言用python，项目和包要用uv来管理
2. 环境变量用python dotenv
3. LLM provider用OPENAI兼容的和GEMINI API
4. 测试要覆盖全面
