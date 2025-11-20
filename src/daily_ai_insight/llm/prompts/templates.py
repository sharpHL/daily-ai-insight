"""Prompt templates for LLM analysis."""

ANALYSIS_PROMPT = """You are a professional AI industry analyst. Please analyze the following content collected today and generate an in-depth insight report.

## Today's Content Data

{content}

## Analysis Tasks

Please complete the following analysis tasks:

1. **Key Points Extraction**: Identify 3-5 most important information points
2. **Technology Trend Analysis**: Analyze current technology development trends and directions
3. **Impact Assessment**: Evaluate the potential impact of this information on the industry and technology development
4. **Professional Commentary**: Provide your professional insights and commentary
5. **Action Recommendations**: Provide actionable recommendations or areas worth attention

## Output Requirements

Please return the analysis results in JSON format:

```json
{
  "executive_summary": "Executive summary within 100 words",
  "key_points": [
    {
      "title": "Key point title",
      "description": "Key point description",
      "importance": "high/medium/low"
    }
  ],
  "trend_analysis": {
    "current_trends": ["trend 1", "trend 2"],
    "emerging_topics": ["emerging topic 1", "emerging topic 2"],
    "declining_topics": ["declining topic 1"]
  },
  "impact_assessment": "Impact assessment description",
  "professional_insights": "Professional insights and commentary",
  "recommendations": [
    {
      "action": "Recommended action",
      "reason": "Reason for recommendation",
      "priority": "high/medium/low"
    }
  ],
  "notable_sources": [
    {
      "title": "Article title worth reading in-depth",
      "url": "Article URL",
      "reason": "Reason for recommendation"
    }
  ]
}
```

Please ensure the analysis is comprehensive, professional, and provides valuable insights.
"""

REPORT_GENERATION_PROMPT = """Based on the following AI industry analysis insights, generate a professional daily report.

## Analysis Data

{insights}

## Report Requirements

Please generate a well-structured, content-rich daily report that includes:

1. **Compelling Title**: Reflecting today's most important information
2. **Executive Summary**: Core summary within 150 words
3. **Key Information**: Categorized display of important information
4. **In-depth Analysis**: Technology trends and impact analysis
5. **Recommended Reading**: Curated 3-5 must-read pieces
6. **Tomorrow's Outlook**: Predictions based on today's information

## Output Format

Please generate a Markdown format report using the following structure:

# [Report Title]

## 📅 Date: {date}

## 📋 Executive Summary

[Summary content]

## 🔥 Today's Highlights

### Technology Breakthroughs
- [Point 1]
- [Point 2]

### Open Source Updates
- [Point 1]
- [Point 2]

### Research Progress
- [Point 1]
- [Point 2]

## 📊 Trend Analysis

[Detailed analysis]

## 📚 Recommended Reading

1. **[Title]** - [Brief description]
   - Link: [URL]
   - Reason: [Reason]

## 🔮 Tomorrow's Outlook

[Predictions and recommendations based on today's information]

---
*Report generated at: {timestamp}*
"""

SUMMARY_PROMPT = """Please generate a concise summary for the following content:

{content}

Requirements:
- Summary length: 50-100 words
- Retain key information
- Professional and fluent language

Output the summary text only.
"""

CATEGORIZATION_PROMPT = """Please categorize the following content:

{content}

Available categories:
- technology
- opensource
- research
- business
- product
- industry
- other

Please return the most appropriate category name.
"""

FILTER_PROMPT = """Please determine if the following content is worth including in the AI industry daily report:

{content}

Evaluation criteria:
1. Relevance: Is it related to AI, machine learning, data science, etc.
2. Importance: Does it have industry influence or technical value
3. Timeliness: Is it fresh information or an update
4. Quality: Does the content have depth and value

Please return in JSON format:
{
  "include": true/false,
  "reason": "Reason for the decision",
  "relevance_score": 0-10
}
"""