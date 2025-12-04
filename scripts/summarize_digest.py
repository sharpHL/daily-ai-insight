#!/usr/bin/env python3
"""
Generate a quick-scan summary from the detailed folo_digest.md.

This script reads the full digest and creates a condensed version
optimized for rapid comprehension.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


async def summarize_with_llm(content: str) -> str:
    """Use LLM to generate executive summary."""
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""你是一位 AI 领域资深分析师，正在为一位算法工程师/AI爱好者整理过去半个月的 AI 动态摘要。

以下是收集到的内容（已按类别分组）：

{content[:80000]}

请生成一份【快速浏览摘要】，要求：

1. **Executive Summary（执行摘要）**：3-5句话总结这半个月 AI 领域最重要的趋势和变化

2. **本周期重要事件 TOP 10**：
   - 列出最值得关注的10条内容
   - 每条格式：`[类别] 标题 - 一句话说明为什么重要`
   - 按重要性排序

3. **趋势洞察**：
   - 当前热点：哪些话题/技术被频繁讨论
   - 新兴方向：有哪些新出现的值得关注的技术/工具
   - 实用工具推荐：对算法工程师最有实用价值的工具/库/资源

4. **值得深入阅读**：
   - 推荐3-5篇最值得花时间阅读的内容
   - 简要说明推荐理由

5. **Quick Wins（快速行动建议）**：
   - 2-3个可以立即尝试的工具/技术

输出格式要求：
- 使用中文
- 使用 Markdown 格式
- 简洁精炼，重点突出
- 每个 section 不超过 200 字
"""

    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text


async def main():
    """Main entry point."""
    digest_path = Path("folo_digest.md")

    if not digest_path.exists():
        print("Error: folo_digest.md not found. Run fetch_folo_list.py first.")
        return

    print("Reading digest...")
    content = digest_path.read_text(encoding="utf-8")

    print("Generating summary with LLM...")
    summary = await summarize_with_llm(content)

    # Create output
    output = f"""# Folo 快速摘要 - {datetime.now().strftime("%Y-%m-%d")}

> 基于过去半个月 (15天) 的 AI 动态生成
> 原始内容: {len(content)} 字符, 精简后供快速浏览

---

{summary}

---

*完整内容请查看 [folo_digest.md](./folo_digest.md)*
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

    output_path = Path("folo_summary.md")
    output_path.write_text(output, encoding="utf-8")

    print(f"\nSummary saved to: {output_path.absolute()}")
    print("\n" + "=" * 50)
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
