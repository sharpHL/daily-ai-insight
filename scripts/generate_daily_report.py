#!/usr/bin/env python3
"""
Generate a personalized daily AI report based on user profile.

Features:
- Profile-based filtering and scoring
- Topic-based classification
- Priority scoring (必读/推荐/了解)
- Interactive HTML with inline feedback buttons
- Continuous learning from feedback

Usage:
    python scripts/generate_daily_report.py [input_file] [--html|--md]
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

# Default paths
PROFILE_PATH = Path("configs/profile.yaml")
FEEDBACK_PATH = Path("configs/feedback.yaml")


def load_profile() -> dict[str, Any]:
    """Load user profile configuration."""
    if not PROFILE_PATH.exists():
        print(f"Warning: {PROFILE_PATH} not found, using defaults")
        return get_default_profile()

    with open(PROFILE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_feedback() -> dict[str, Any]:
    """Load feedback for learning."""
    if not FEEDBACK_PATH.exists():
        return {"learned_preferences": {}, "feedback_log": []}

    with open(FEEDBACK_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_default_profile() -> dict[str, Any]:
    """Return default profile if none exists."""
    return {
        "identity": {"primary_role": "AI工程师"},
        "interests": {
            "must_track": ["LLM", "AI Agent", "开源工具"],
            "want_track": ["论文", "效率"],
            "nice_to_have": [],
        },
        "filters": {
            "skip_keywords": ["广告", "抽奖"],
            "skip_patterns": [],
            "trusted_sources": [],
        },
        "consumption": {
            "daily_item_count": {"must_read": 5, "recommended": 15, "fyi": 10},
            "preferred_depth": "summary_with_context",
            "action_oriented": True,
            "explain_relevance": True,
        },
        "scoring": {
            "thresholds": {"must_read": 80, "recommended": 50, "fyi": 30},
        },
    }


def parse_folo_updates(content: str) -> list[dict[str, Any]]:
    """Parse folo_updates.md into structured items."""
    items = []
    sections = re.split(r'\n---\n', content)

    current_source = ""
    for section in sections:
        section = section.strip()
        if not section:
            continue

        source_match = re.match(r'^## (.+)$', section, re.MULTILINE)
        if source_match:
            current_source = source_match.group(1)
            section = re.sub(r'^## .+\n', '', section).strip()

        title_match = re.search(r'### \[([^\]]*)\]\(([^)]+)\)', section)
        if not title_match:
            continue

        title = title_match.group(1).strip()
        url = title_match.group(2).strip()

        date_match = re.search(r'\*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\*', section)
        date = date_match.group(1) if date_match else ""

        content_text = ""
        if date_match:
            content_start = date_match.end()
            content_text = section[content_start:].strip()
            content_text = re.sub(r'\.\.\.$', '', content_text).strip()

        if title or content_text:
            items.append({
                "title": title[:200] if title else content_text[:100],
                "url": url,
                "date": date,
                "content": content_text[:800],
                "source": current_source,
            })

    return items


def build_classification_prompt(profile: dict, feedback: dict) -> str:
    """Build LLM prompt based on user profile."""
    identity = profile.get("identity", {})
    interests = profile.get("interests", {})
    filters = profile.get("filters", {})
    consumption = profile.get("consumption", {})
    learned = feedback.get("learned_preferences", {})

    must_track = interests.get("must_track", [])
    want_track = interests.get("want_track", [])
    skip_patterns = filters.get("skip_patterns", [])
    trusted = filters.get("trusted_sources", [])

    additional_interests = learned.get("additional_interests", [])
    additional_filters = learned.get("additional_filters", [])
    keyword_adjustments = learned.get("keyword_adjustments", {})

    prompt_parts = [
        f"你是一位专业的 AI 内容分析师，为【{identity.get('primary_role', 'AI工程师')}】筛选和分类信息。",
        "",
        "## 用户画像",
        f"- 角色：{identity.get('primary_role', '')}",
        f"- 次要兴趣：{', '.join(identity.get('secondary_roles', []))}",
        f"- 技术栈：{', '.join(identity.get('tech_stack', []))}",
        "",
        "## 内容偏好",
        "",
        "### 🔥 必看内容（评分+30）：",
    ]

    for item in must_track + additional_interests:
        prompt_parts.append(f"- {item}")

    prompt_parts.extend([
        "",
        "### ⭐ 感兴趣内容（评分+15）：",
    ])
    for item in want_track:
        prompt_parts.append(f"- {item}")

    prompt_parts.extend([
        "",
        "### ❌ 需要过滤的内容（直接跳过）：",
    ])
    for item in skip_patterns + additional_filters:
        prompt_parts.append(f"- {item}")

    if trusted:
        prompt_parts.extend([
            "",
            f"### 可信来源（评分+10）：{', '.join(trusted)}",
        ])

    if keyword_adjustments:
        prompt_parts.extend([
            "",
            "### 关键词权重调整（从历史反馈学习）：",
        ])
        for kw, adj in keyword_adjustments.items():
            sign = "+" if adj > 0 else ""
            prompt_parts.append(f"- {kw}: {sign}{adj}")

    if consumption.get("action_oriented"):
        prompt_parts.extend([
            "",
            "### 特别关注「可立即行动」的内容：",
            "- 新发布的工具/API/SDK（可以立即试用）",
            "- 具体的代码示例或教程",
            "- 最佳实践和经验分享",
        ])

    return "\n".join(prompt_parts)


async def classify_and_score_items(
    items: list[dict[str, Any]],
    profile: dict,
    feedback: dict
) -> list[dict[str, Any]]:
    """Use LLM to classify items based on user profile."""
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    model = genai.GenerativeModel("gemini-2.0-flash")

    profile_context = build_classification_prompt(profile, feedback)

    batch_size = 20
    all_results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print(f"  Processing batch {i // batch_size + 1}/{(len(items) + batch_size - 1) // batch_size}...")

        batch_data = []
        for idx, item in enumerate(batch):
            batch_data.append({
                "idx": idx,
                "title": item["title"][:100],
                "content": item["content"][:400],
                "source": item.get("source", ""),
            })

        prompt = f"""{profile_context}

## 待分类内容

{json.dumps(batch_data, ensure_ascii=False, indent=2)}

## 分类任务

对每条内容进行评估，返回 JSON 数组：

```json
[
  {{
    "idx": 序号,
    "score": 0-100,
    "topic": "LLM进展|AI Agent|工具资源|研究论文|行业动态|效率提升|其他",
    "summary": "一句话中文摘要(25字内)",
    "tags": ["标签1", "标签2"],
    "relevance_reason": "为什么对该用户重要(15字内)",
    "actionable": true/false,
    "skip": false
  }}
]
```

评分参考：
- 90-100: 必读（直接影响工作/重大突破）
- 70-89: 强烈推荐
- 50-69: 推荐
- 30-49: 了解即可
- 0-29: 跳过

只返回 JSON 数组，不要其他内容。"""

        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            results = json.loads(response.text)

            if isinstance(results, dict) and "items" in results:
                results = results["items"]
            elif not isinstance(results, list):
                results = [results]

            for result in results:
                idx = result.get("idx", 0)
                if 0 <= idx < len(batch):
                    batch[idx]["score"] = result.get("score", 50)
                    batch[idx]["topic"] = result.get("topic", "其他")
                    batch[idx]["summary"] = result.get("summary", "")
                    batch[idx]["tags"] = result.get("tags", [])
                    batch[idx]["relevance_reason"] = result.get("relevance_reason", "")
                    batch[idx]["actionable"] = result.get("actionable", False)
                    batch[idx]["skip"] = result.get("skip", False)

            all_results.extend(batch)

        except Exception as e:
            print(f"    Error in batch: {e}")
            for item in batch:
                item["score"] = 40
                item["topic"] = "其他"
                item["summary"] = item["title"][:25]
                item["tags"] = []
                item["skip"] = False
            all_results.extend(batch)

        await asyncio.sleep(0.5)

    return all_results


def generate_html_report(
    items: list[dict[str, Any]],
    profile: dict,
    date_str: str = ""
) -> str:
    """Generate interactive HTML report with inline feedback."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    consumption = profile.get("consumption", {})
    thresholds = profile.get("scoring", {}).get("thresholds", {})
    limits = consumption.get("daily_item_count", {})

    items = [item for item in items if not item.get("skip", False)]

    must_read_threshold = thresholds.get("must_read", 80)
    recommended_threshold = thresholds.get("recommended", 50)
    fyi_threshold = thresholds.get("fyi", 30)

    must_read = [i for i in items if i.get("score", 0) >= must_read_threshold]
    recommended = [i for i in items if recommended_threshold <= i.get("score", 0) < must_read_threshold]
    fyi = [i for i in items if fyi_threshold <= i.get("score", 0) < recommended_threshold]

    must_read.sort(key=lambda x: -x.get("score", 0))
    recommended.sort(key=lambda x: -x.get("score", 0))
    fyi.sort(key=lambda x: -x.get("score", 0))

    must_read = must_read[:limits.get("must_read", 5)]
    recommended = recommended[:limits.get("recommended", 15)]
    fyi = fyi[:limits.get("fyi", 10)]

    all_items = must_read + recommended + fyi
    by_topic: dict[str, list] = {}
    for item in all_items:
        topic = item.get("topic", "其他")
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(item)

    identity = profile.get("identity", {})
    role = identity.get("primary_role", "AI工程师")

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 日报 - {date_str}</title>
    <style>
        :root {{
            --bg: #1a1a2e;
            --card-bg: #16213e;
            --text: #eee;
            --text-dim: #888;
            --accent: #e94560;
            --accent-green: #00d26a;
            --accent-yellow: #ffc107;
            --accent-blue: #0f3460;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{ color: var(--accent); margin-bottom: 10px; }}
        .stats {{
            color: var(--text-dim);
            margin-bottom: 30px;
            padding: 15px;
            background: var(--card-bg);
            border-radius: 8px;
        }}
        .stats span {{ margin-right: 15px; }}
        .topic {{ margin-bottom: 30px; }}
        .topic h2 {{
            color: var(--accent);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 5px;
            margin-bottom: 15px;
        }}
        .item {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            border-left: 4px solid var(--accent-blue);
            transition: all 0.2s;
        }}
        .item:hover {{ transform: translateX(5px); }}
        .item.must-read {{ border-left-color: var(--accent); }}
        .item.recommended {{ border-left-color: var(--accent-yellow); }}
        .item.fyi {{ border-left-color: var(--text-dim); }}
        .item.liked {{ background: rgba(0, 210, 106, 0.1); }}
        .item.disliked {{ opacity: 0.4; }}
        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }}
        .item-title {{
            font-size: 16px;
            font-weight: 600;
            flex: 1;
        }}
        .item-title a {{
            color: var(--text);
            text-decoration: none;
        }}
        .item-title a:hover {{ color: var(--accent); }}
        .item-meta {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .score {{
            background: var(--accent-blue);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .tag {{
            background: rgba(255,255,255,0.1);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            color: var(--text-dim);
        }}
        .actionable {{ color: var(--accent-green); }}
        .summary {{
            color: var(--text-dim);
            font-size: 14px;
            margin: 8px 0;
        }}
        .relevance {{
            font-size: 12px;
            color: var(--accent-yellow);
            margin-top: 5px;
        }}
        .feedback {{
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }}
        .feedback button {{
            background: transparent;
            border: 1px solid var(--text-dim);
            color: var(--text-dim);
            padding: 4px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .feedback button:hover {{
            border-color: var(--text);
            color: var(--text);
        }}
        .feedback button.active-like {{
            background: var(--accent-green);
            border-color: var(--accent-green);
            color: #fff;
        }}
        .feedback button.active-dislike {{
            background: var(--accent);
            border-color: var(--accent);
            color: #fff;
        }}
        .export-section {{
            margin-top: 40px;
            padding: 20px;
            background: var(--card-bg);
            border-radius: 8px;
        }}
        .export-section h3 {{ margin-bottom: 15px; }}
        .export-section button {{
            background: var(--accent);
            border: none;
            color: #fff;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }}
        .export-section button:hover {{ opacity: 0.9; }}
        #feedback-output {{
            margin-top: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
            display: none;
        }}
    </style>
</head>
<body>
    <h1>🤖 AI 日报 - {date_str}</h1>
    <div class="stats">
        <span>为【{role}】定制</span>
        <span>🔥 必读 {len(must_read)}</span>
        <span>⭐ 推荐 {len(recommended)}</span>
        <span>📌 了解 {len(fyi)}</span>
        <span style="float:right">点击 👍/👎 即时反馈</span>
    </div>
'''

    topic_order = ["LLM进展", "AI Agent", "工具资源", "研究论文", "效率提升", "行业动态", "其他"]
    item_id = 0

    for topic in topic_order:
        if topic not in by_topic:
            continue

        topic_items = by_topic[topic]
        if not topic_items:
            continue

        html += f'    <div class="topic">\n'
        html += f'        <h2>{topic}</h2>\n'

        for item in topic_items:
            score = item.get("score", 0)
            if score >= must_read_threshold:
                priority_class = "must-read"
            elif score >= recommended_threshold:
                priority_class = "recommended"
            else:
                priority_class = "fyi"

            title = item.get("title", "")[:80]
            # Escape HTML in title
            title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            url = item.get("url", "#")
            summary = item.get("summary", "")
            tags = item.get("tags", [])
            relevance = item.get("relevance_reason", "")
            actionable = item.get("actionable", False)

            tags_html = "".join([f'<span class="tag">{t}</span>' for t in tags[:3]])
            actionable_html = '<span class="actionable">🚀 可行动</span>' if actionable else ""

            # Escape title for data attribute
            title_escaped = title[:50].replace('"', '\\"')

            html += f'''        <div class="item {priority_class}" data-id="{item_id}" data-title="{title_escaped}">
            <div class="item-header">
                <div class="item-title">
                    <a href="{url}" target="_blank">{title}</a>
                </div>
                <div class="item-meta">
                    <span class="score">{score}分</span>
                    {actionable_html}
                </div>
            </div>
            <div class="summary">{summary}</div>
            <div>{tags_html}</div>
            <div class="relevance">💡 {relevance}</div>
            <div class="feedback">
                <button onclick="feedback({item_id}, 'like', this)">👍 想看更多</button>
                <button onclick="feedback({item_id}, 'dislike', this)">👎 不感兴趣</button>
            </div>
        </div>
'''
            item_id += 1

        html += '    </div>\n'

    # Get feedback API URL from environment
    feedback_api = os.getenv("FEEDBACK_API_URL", "")

    html += f'''
    <div class="export-section">
        <h3>📤 保存反馈</h3>
        <p style="color: var(--text-dim); margin-bottom: 15px;">
            反馈会自动保存，用于优化下次日报推荐
        </p>
        <button onclick="saveFeedback()" id="save-btn">💾 保存反馈</button>
        <button onclick="clearFeedback()">🗑️ 清除反馈</button>
        <div id="feedback-status" style="margin-top: 15px; display: none;"></div>
    </div>

    <script>
        const FEEDBACK_API = "{feedback_api}";
        const REPORT_DATE = "{date_str}";
        const feedbackData = {{}};

        function feedback(id, type, btn) {{
            const item = document.querySelector(`[data-id="${{id}}"]`);
            const title = item.dataset.title;

            item.classList.remove('liked', 'disliked');
            item.querySelectorAll('.feedback button').forEach(b => {{
                b.classList.remove('active-like', 'active-dislike');
            }});

            if (type === 'like') {{
                item.classList.add('liked');
                btn.classList.add('active-like');
                feedbackData[id] = {{ action: 'want_more', title: title }};
            }} else if (type === 'dislike') {{
                item.classList.add('disliked');
                btn.classList.add('active-dislike');
                feedbackData[id] = {{ action: 'not_interested', title: title }};
            }}

            localStorage.setItem('ai_daily_feedback_' + REPORT_DATE, JSON.stringify(feedbackData));
            updateSaveButton();
        }}

        function updateSaveButton() {{
            const count = Object.keys(feedbackData).length;
            const btn = document.getElementById('save-btn');
            btn.textContent = count > 0 ? `💾 保存反馈 (${{count}} 条)` : '💾 保存反馈';
        }}

        async function saveFeedback() {{
            const items = Object.values(feedbackData);
            if (items.length === 0) {{
                showStatus('没有反馈数据', 'warning');
                return;
            }}

            // If no API configured, show local save message
            if (!FEEDBACK_API) {{
                showStatus('✅ 已保存到本地（下次访问时恢复）', 'success');
                return;
            }}

            showStatus('正在保存...', 'info');

            try {{
                const response = await fetch(FEEDBACK_API + '/feedback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        date: REPORT_DATE,
                        items: items
                    }})
                }});

                const result = await response.json();

                if (result.success) {{
                    showStatus(`✅ 已保存 ${{result.count}} 条反馈`, 'success');
                }} else {{
                    throw new Error(result.error || 'Unknown error');
                }}
            }} catch (error) {{
                console.error('Save feedback error:', error);
                showStatus('保存失败，已存到本地: ' + error.message, 'warning');
            }}
        }}

        function showStatus(message, type) {{
            const status = document.getElementById('feedback-status');
            status.textContent = message;
            status.style.display = 'block';
            status.style.padding = '10px';
            status.style.borderRadius = '4px';

            if (type === 'success') {{
                status.style.background = 'rgba(0, 210, 106, 0.2)';
                status.style.color = '#00d26a';
            }} else if (type === 'warning') {{
                status.style.background = 'rgba(255, 193, 7, 0.2)';
                status.style.color = '#ffc107';
            }} else {{
                status.style.background = 'rgba(15, 52, 96, 0.5)';
                status.style.color = '#eee';
            }}
        }}

        function clearFeedback() {{
            Object.keys(feedbackData).forEach(k => delete feedbackData[k]);
            localStorage.removeItem('ai_daily_feedback_' + REPORT_DATE);
            document.querySelectorAll('.item').forEach(item => {{
                item.classList.remove('liked', 'disliked');
                item.querySelectorAll('.feedback button').forEach(b => {{
                    b.classList.remove('active-like', 'active-dislike');
                }});
            }});
            updateSaveButton();
            document.getElementById('feedback-status').style.display = 'none';
        }}

        // Restore saved feedback
        const saved = localStorage.getItem('ai_daily_feedback_' + REPORT_DATE);
        if (saved) {{
            const parsed = JSON.parse(saved);
            Object.assign(feedbackData, parsed);
            Object.entries(parsed).forEach(([id, data]) => {{
                const item = document.querySelector(`[data-id="${{id}}"]`);
                if (item) {{
                    if (data.action === 'want_more') {{
                        item.classList.add('liked');
                    }} else if (data.action === 'not_interested') {{
                        item.classList.add('disliked');
                    }}
                }}
            }});
            updateSaveButton();
        }}
    </script>
</body>
</html>'''

    return html


def generate_markdown_report(
    items: list[dict[str, Any]],
    profile: dict,
    date_str: str = ""
) -> str:
    """Generate markdown report."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    consumption = profile.get("consumption", {})
    thresholds = profile.get("scoring", {}).get("thresholds", {})
    limits = consumption.get("daily_item_count", {})
    explain_relevance = consumption.get("explain_relevance", True)

    items = [item for item in items if not item.get("skip", False)]

    must_read_threshold = thresholds.get("must_read", 80)
    recommended_threshold = thresholds.get("recommended", 50)
    fyi_threshold = thresholds.get("fyi", 30)

    must_read = [i for i in items if i.get("score", 0) >= must_read_threshold]
    recommended = [i for i in items if recommended_threshold <= i.get("score", 0) < must_read_threshold]
    fyi = [i for i in items if fyi_threshold <= i.get("score", 0) < recommended_threshold]

    must_read.sort(key=lambda x: -x.get("score", 0))
    recommended.sort(key=lambda x: -x.get("score", 0))
    fyi.sort(key=lambda x: -x.get("score", 0))

    must_read = must_read[:limits.get("must_read", 5)]
    recommended = recommended[:limits.get("recommended", 15)]
    fyi = fyi[:limits.get("fyi", 10)]

    all_items = must_read + recommended + fyi
    by_topic: dict[str, list] = {}
    for item in all_items:
        topic = item.get("topic", "其他")
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(item)

    identity = profile.get("identity", {})
    role = identity.get("primary_role", "AI工程师")

    lines = [
        f"# AI 日报 - {date_str}",
        "",
        f"> 为【{role}】定制 | 共 {len(all_items)} 条精选内容",
        f"> 🔥 必读 {len(must_read)} | ⭐ 推荐 {len(recommended)} | 📌 了解 {len(fyi)}",
        "",
    ]

    if must_read:
        lines.append("## 今日必看")
        lines.append("")
        for item in must_read[:5]:
            score = item.get("score", 0)
            summary = item.get("summary") or item.get("title", "")[:30]
            actionable = "🚀" if item.get("actionable") else ""
            lines.append(f"- {actionable}**[{summary}]({item.get('url', '#')})** `{score}分`")
            if explain_relevance and item.get("relevance_reason"):
                lines.append(f"  > 💡 {item['relevance_reason']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    topic_order = ["LLM进展", "AI Agent", "工具资源", "研究论文", "效率提升", "行业动态", "其他"]
    for topic in topic_order:
        if topic not in by_topic:
            continue

        topic_items = by_topic[topic]
        if not topic_items:
            continue

        lines.append(f"## {topic}")
        lines.append("")

        for item in topic_items:
            score = item.get("score", 0)

            if score >= must_read_threshold:
                icon = "🔥"
            elif score >= recommended_threshold:
                icon = "⭐"
            else:
                icon = "📌"

            actionable = " 🚀" if item.get("actionable") else ""

            title = item.get("title", "")[:60]
            url = item.get("url", "#")
            summary = item.get("summary", "")
            tags = item.get("tags", [])

            lines.append(f"### {icon} [{title}]({url}){actionable}")
            lines.append("")

            if summary:
                lines.append(f"> {summary}")
                lines.append("")

            if explain_relevance and item.get("relevance_reason"):
                lines.append(f"💡 **相关性**: {item['relevance_reason']}")
                lines.append("")

            if tags:
                tag_str = " ".join([f"`{t}`" for t in tags[:4]])
                lines.append(f"{tag_str}")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


async def main():
    """Main entry point."""
    import sys

    input_file = "folo_updates.md"
    output_html = True

    for arg in sys.argv[1:]:
        if arg == "--md" or arg == "--markdown":
            output_html = False
        elif arg == "--html":
            output_html = True
        elif not arg.startswith("-"):
            input_file = arg

    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: {input_file} not found")
        return

    print("Loading profile and feedback...")
    profile = load_profile()
    feedback = load_feedback()

    print(f"Reading {input_file}...")
    content = input_path.read_text(encoding="utf-8")

    print("Parsing content...")
    items = parse_folo_updates(content)
    print(f"  Found {len(items)} items")

    if not items:
        print("No items found to process")
        return

    print("Classifying with personalized profile...")
    items = await classify_and_score_items(items, profile, feedback)

    date_match = re.search(r'Generated: (\d{4}-\d{2}-\d{2})', content)
    date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    print("Generating personalized report...")

    if output_html:
        report = generate_html_report(items, profile, date_str)
        output_path = Path(f"ai_daily_{date_str}.html")
    else:
        report = generate_markdown_report(items, profile, date_str)
        output_path = Path(f"ai_daily_{date_str}.md")

    output_path.write_text(report, encoding="utf-8")

    print(f"\nReport saved to: {output_path.absolute()}")

    thresholds = profile.get("scoring", {}).get("thresholds", {})
    must_read_th = thresholds.get("must_read", 80)
    rec_th = thresholds.get("recommended", 50)
    fyi_th = thresholds.get("fyi", 30)

    must_read = len([i for i in items if i.get("score", 0) >= must_read_th and not i.get("skip")])
    recommended = len([i for i in items if rec_th <= i.get("score", 0) < must_read_th and not i.get("skip")])
    fyi_count = len([i for i in items if fyi_th <= i.get("score", 0) < rec_th and not i.get("skip")])
    skipped = len([i for i in items if i.get("skip") or i.get("score", 0) < fyi_th])

    print(f"\n统计:")
    print(f"  🔥 必读: {must_read}")
    print(f"  ⭐ 推荐: {recommended}")
    print(f"  📌 了解: {fyi_count}")
    print(f"  跳过: {skipped}")

    if output_html:
        print(f"\n💡 在浏览器打开 {output_path} 即可阅读并反馈")


if __name__ == "__main__":
    asyncio.run(main())
