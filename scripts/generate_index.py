#!/usr/bin/env python3
"""Generate index.html for GitHub Pages with links to all daily reports."""

import os
from datetime import datetime
from pathlib import Path


def generate_index():
    """Generate index.html listing all daily reports."""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Find all daily report files
    reports = sorted(docs_dir.glob("ai_daily_*.html"), reverse=True)

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 日报归档</title>
    <style>
        :root {
            --bg: #1a1a2e;
            --card-bg: #16213e;
            --text: #eee;
            --text-dim: #888;
            --accent: #e94560;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 40px 20px;
            max-width: 600px;
            margin: 0 auto;
        }
        h1 {
            color: var(--accent);
            margin-bottom: 10px;
        }
        .subtitle {
            color: var(--text-dim);
            margin-bottom: 30px;
        }
        .report-list {
            list-style: none;
        }
        .report-list li {
            background: var(--card-bg);
            border-radius: 8px;
            margin-bottom: 10px;
            transition: transform 0.2s;
        }
        .report-list li:hover {
            transform: translateX(5px);
        }
        .report-list a {
            display: block;
            padding: 15px 20px;
            color: var(--text);
            text-decoration: none;
        }
        .report-list a:hover {
            color: var(--accent);
        }
        .date {
            font-size: 18px;
            font-weight: 600;
        }
        .meta {
            font-size: 12px;
            color: var(--text-dim);
            margin-top: 5px;
        }
        .empty {
            color: var(--text-dim);
            text-align: center;
            padding: 40px;
        }
    </style>
</head>
<body>
    <h1>🤖 AI 日报归档</h1>
    <p class="subtitle">每日 AI 动态，为算法工程师定制</p>

    <ul class="report-list">
'''

    if reports:
        for report in reports[:30]:  # Show last 30 reports
            # Extract date from filename
            filename = report.name
            date_str = filename.replace("ai_daily_", "").replace(".html", "")

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%Y年%m月%d日")
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
            except ValueError:
                display_date = date_str
                weekday = ""

            html += f'''        <li>
            <a href="{filename}">
                <div class="date">{display_date} {weekday}</div>
                <div class="meta">点击查看详情 →</div>
            </a>
        </li>
'''
    else:
        html += '''        <li class="empty">暂无日报，请等待自动生成</li>
'''

    html += f'''    </ul>

    <p style="text-align: center; color: var(--text-dim); margin-top: 40px; font-size: 12px;">
        自动更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC
    </p>
</body>
</html>'''

    index_path = docs_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"Generated {index_path}")


if __name__ == "__main__":
    generate_index()
