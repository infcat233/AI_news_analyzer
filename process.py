import json
# import time
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('ANTHROPIC_AUTH_TOKEN'),
    base_url="https://api.deepseek.com"
)

# 调用LLM
def call_llm_with_json(prompt):
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": "你是一个严谨的信息处理助手，只输出JSON"},
            {"role": "user", "content": prompt}
        ],
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )

    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return text 

# 字符串转json
def safe_json_load(text):
    try:
        return json.loads(text)
    except:
        print("⚠️ JSON解析失败，尝试修复")

        fix_prompt = f"请将以下内容修复为合法JSON：\n{text}"

        fixed = call_llm_with_json(fix_prompt)
        fixed = fixed.replace("```json", "").replace("```", "").strip()

        return json.loads(fixed)

# 翻译
def translate(news):
    prompt = f"""
如果以下内容是英文，请翻译为中文；如果已经是中文，直接返回：

标题：{news['title']}
正文：{news['content']}

输出JSON：
{{
  "title": "",
  "content": ""
}}
只输出JSON
"""
    # print(prompt)
    text = call_llm_with_json(prompt)
    # print(text)
    return safe_json_load(text)

# 提取基础信息
def extract_basic(news):
    prompt = f"""
请从以下新闻中提取基础信息：

标题：{news['title']}
正文：{news['content']}

提取：
- entities（公司/机构）
- tech_tags（如LLM、多模态等）
- keywords（3-5个关键词）

只输出JSON：
{{
  "entities": [],
  "tech_tags": [],
  "keywords": []
}}
"""

    text = call_llm_with_json(prompt)
    return safe_json_load(text)

# 分类与判断
def classify(news, basic):
    prompt = f"""
请根据以下AI新闻进行结构化分析：

新闻内容：
{news['content']}

已知实体：
{basic.get('entities', [])}

【任务】

请输出：

- category（技术/产品/投资/政策/行业）
- event_type（发布/融资/开源/合作/政策/研究）


【输出格式】

{{
  "category": "",
  "event_type": "",
}}


要求：
1. 所有字段必须有值
2. 只输出JSON
"""

    text = call_llm_with_json(prompt)
    return safe_json_load(text)

TOP_COMPANIES = [
    # 🇺🇸 
    "OpenAI", "Google", "DeepMind", "Microsoft", "Meta", "Amazon", "NVIDIA",

    # 🇨🇳 
    "百度", "阿里巴巴", "腾讯", "字节跳动", "华为",

]

def extract_signals(news, basic):
    prompt = f"""
请根据以下AI新闻进行结构化分析：

新闻内容：
{news['content']}

已知实体：
{basic.get('entities', [])}

【判断规则（只能输出0或1）】

1. is_top_company：
是否涉及头部公司（OpenAI, Google, Microsoft, Meta, Amazon 等）

2. is_major_event：
是否为重大事件（模型发布 / 技术突破 / 政策）

3. is_wide_impact：
是否影响多个公司或整个行业

4. is_analysis：
是否是分析、评论、总结类内容

【输出格式】
{{
    "signals": {{
        "is_top_company": 0,
        "is_major_event": 0,
        "is_wide_impact": 0,
        "is_analysis": 0
    }},
}}

要求：
1. 所有字段必须有值
2. 只输出JSON

"""
    text = call_llm_with_json(prompt)
    # print(text)
    return safe_json_load(text)

# 分类与判断
# def classify(news, basic):
#     prompt = f"""
# 请根据以下AI新闻进行结构化分析：

# 新闻内容：
# {news['content']}

# 已知实体：
# {basic.get('entities', [])}

# 【任务】

# 请输出：

# - category（技术/产品/投资/政策/行业）
# - event_type（发布/融资/开源/合作/政策/研究）
# - sentiment（正面/中性/风险）

# 【输出格式】

# {{
  
#   "category": "",
#   "event_type": "",
#   "sentiment": ""
# }}


# 要求：
# 1. 所有字段必须有值
# 2. 只输出JSON
# """
#     text = call_llm_with_json(prompt)
#     return safe_json_load(text)

def fix_signals(signals, entities):

    signals.setdefault("is_top_company", 0)
    signals.setdefault("is_major_event", 0)
    signals.setdefault("is_wide_impact", 0)
    signals.setdefault("is_analysis", 0)

    for k in signals:
        try:
            signals[k] = int(signals[k])
        except:
            signals[k] = 0

    for k in signals:
        signals[k] = 1 if signals[k] else 0
    
    if any(e in TOP_COMPANIES for e in entities):
        signals["is_top_company"] = 1
    return signals

def compute_importance_score(signals):
    score = 1  # base

    if signals["is_analysis"]:
        if signals["is_top_company"]:
            score += 1
        if signals["is_wide_impact"]:
            score += 1
        return min(score, 3)

    if signals["is_wide_impact"]:
        score += 2

    if signals["is_top_company"]:
        score += 1

    if signals["is_major_event"]:
        score += 1

    return min(score, 5)

def extract_sentiment(news_text):

    prompt = f"""
请判断以下AI新闻的情绪倾向：

新闻：
{news_text}

【情绪判定标准】

关键：
- 分析类、论文类 → 多数情况为“中性”
- 普通新闻（无明显突破）→ 不应判为正面

正面：
- 明确技术突破 / 行业级影响

中性：
- 分析 / 评论 / 论文
- 无明显价值提升的新闻

负面：
- 风险 / 争议 / 失败

如果不确定 → 中性

【要求】

必须输出以下之一：
- 正面
- 中性
- 负面

只输出JSON：

{{"sentiment": "正面/中性/负面"}}
"""

    text = call_llm_with_json(prompt)
    result = safe_json_load(text)
    sentiment = result.get("sentiment", "中性")
    if sentiment not in ["正面", "中性", "负面"]:
        sentiment = "中性"

    return sentiment

def generate_analysis(news):
    prompt = f"""
请生成：

1. summary（一句话总结）
2. impact（1-2句影响分析）

新闻内容：
{news['content']}

要求：
- 使用中文
- 简洁

输出JSON：
{{
  "summary": "",
  "impact": ""
}}
"""

    text = call_llm_with_json(prompt)
    return safe_json_load(text)

def validate_result(data):
    valid_categories = ["技术", "产品", "投资", "政策", "行业"]
    valid_sentiment = ["正面", "中性", "风险"]

    if data.get("category") not in valid_categories:
        data["category"] = "行业"

    if data.get("sentiment") not in valid_sentiment:
        data["sentiment"] = "中性"

    score = data.get("importance_score", 3)
    if not isinstance(score, int) or score < 1 or score > 5:
        data["importance_score"] = 3

    if not isinstance(data.get("entities"), list):
        data["entities"] = []

    if not isinstance(data.get("keywords"), list):
        data["keywords"] = []

    data["entities"] = list(set(data["entities"]))
    data["keywords"] = list(set(data["keywords"]))

    return data

def process(news):
    news_cn = translate(news)
    # print("news_cn =", news_cn)
    news_basic = extract_basic(news_cn)
    # print("news_basic =", news_basic)
    news_meta = classify(news_cn, news_basic)
    # print("news_meta =", news_meta)
    # breakdown = validate_breakdown(news_meta.get("importance_breakdown", {}))
    # news_importance_score = compute_importance_score(breakdown)
    # print(news_importance_score)
    # signals = fix_signals(news_meta.get("signals", {}), news_basic.get('entities', []))
    raw_signals = extract_signals(news_cn, news_basic).get('signals')
    # print(raw_signals)
    signals = fix_signals(raw_signals, news_basic.get('entities', []))
    score = compute_importance_score(signals)
    # print(raw_signals)
    # print(signals)
    # print(score)
    sentiment = extract_sentiment(news_cn)
    # print(sentiment)
    news_analysis = generate_analysis(news_cn)
    result = {
        "id": news["id"],
        "title": news_cn["title"],
        "summary": news_analysis.get("summary", ""),
        "category": news_meta.get("category", "行业"),
        "entities": news_basic.get("entities", []),
        "tech_tags": news_basic.get("tech_tags", []),
        "event_type": news_meta.get("event_type", ""),
        "sentiment": sentiment,
        "importance_score": score,
        "importance_signals": signals,
        "impact": news_analysis.get("impact", ""),
        "keywords": news_basic.get("keywords", [])
    }
    return validate_result(result)


with open("news.json", "r", encoding="utf-8") as f:
    news_list = json.load(f)

results = []

# process(news_list[4])
# print(process(news_list[4]))

for news in news_list:
    try:
        result = process(news)
        results.append(result)
        print(f"✅ 完成：{news['title']}")
    except Exception as e:
        print(f"❌ 失败：{news['title']}")
        print(e)

with open("structured_news.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n🎉 全部处理完成！")