import json
import pandas as pd
import matplotlib.pyplot as plt
from mdutils.mdutils import MdUtils
from collections import Counter


plt.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def load_data(file_path="structured_news.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # 展开 importance_signals
    signals_df = pd.json_normalize(df["importance_signals"])
    df = pd.concat([df.drop(columns=["importance_signals"]), signals_df], axis=1)

    return df


def generate_plots(df):

    plots = {}

    plt.figure()
    df["category"].value_counts().plot(kind="bar")
    plt.title("分类分布")
    plt.xlabel("类别")
    plt.ylabel("数量")
    path1 = "category_dist.png"
    plt.savefig(path1)
    plt.close()
    plots["category"] = path1


    plt.figure()
    df["sentiment"].value_counts().plot(kind="bar")
    plt.title("情绪分布")
    plt.xlabel("情绪类型")
    plt.ylabel("数量")
    path2 = "sentiment_dist.png"
    plt.savefig(path2)
    plt.close()
    plots["sentiment"] = path2


    plt.figure()
    df["importance_score"].value_counts().sort_index().plot(kind="bar")
    plt.title("重要性评分分布")
    plt.xlabel("评分")
    plt.ylabel("数量")
    path3 = "importance_dist.png"
    plt.savefig(path3)
    plt.close()
    plots["importance"] = path3

    return plots

def build_overview(df):
    total = len(df)
    high = (df["importance_score"] >= 4).sum()
    top_ratio = df["is_top_company"].mean()

    return [
        f"总新闻数：{total}",
        f"高重要性事件：{high}（{high/total:.2%}）",
        f"头部公司占比：{top_ratio:.2%}"
    ]

def get_top_events(df, top_n=5):

    df_sorted = df.sort_values(
        by=["importance_score", "is_top_company"],
        ascending=False
    ).head(top_n)

    lines = []
    for _, row in df_sorted.iterrows():
        lines.append(
            f"{row['title']}（评分:{row['importance_score']}，类别:{row['category']}）"
        )

    return lines

def build_category_summary(df):

    lines = []
    for cat, group in df.groupby("category"):

        top_event = group.sort_values(
            by="importance_score", ascending=False
        ).iloc[0]["title"]

        lines.append(
            f"{cat}：{len(group)}条，代表事件：{top_event}"
        )

    return lines

def build_tech_trend(df):

    all_tags = []
    for tags in df["tech_tags"]:
        if isinstance(tags, list):
            all_tags.extend(tags)

    counter = Counter(all_tags)
    top_tags = counter.most_common(5)

    return [f"{tag}（{count}次）" for tag, count in top_tags]

def build_risk_opportunity(df):

    risk = []
    opp = []

    # 风险：负面情绪
    if (df["sentiment"] == "负面").mean() > 0.2:
        risk.append("负面舆情上升")

    # 机会：高重要性多
    if (df["importance_score"] >= 4).mean() > 0.3:
        opp.append("高价值事件频繁出现")

    # 技术机会
    if "Agent" in str(df["tech_tags"].values):
        opp.append("Agent方向持续升温")

    if not risk:
        risk.append("暂无明显风险")

    if not opp:
        opp.append("暂无明显机会")

    return risk, opp

def generate_markdown(df, plots):

    md = MdUtils(file_name="analysis_report", title="AI行业分析报告")
    md.new_header(level=1, title="AI行业分析报告")
    # ===== 概览 =====
    md.new_header(level=2, title="一、总体概览")
    md.new_list(build_overview(df))

    # ===== 热点 =====
    md.new_header(level=2, title="二、今日热点")
    md.new_list(get_top_events(df))

    # ===== 分类 =====
    md.new_header(level=2, title="三、分类分析")
    md.new_list(build_category_summary(df))

    # ===== 技术趋势 =====
    md.new_header(level=2, title="四、技术趋势")
    md.new_list(build_tech_trend(df))

    # ===== 图表 =====
    md.new_header(level=2, title="五、数据可视化")

    print(plots)
    md.new_paragraph("分类分布")
    md.new_paragraph(f"![]({plots['category']})")

    md.new_paragraph("情绪分布")
    md.new_paragraph(f"![]({plots['sentiment']})")

    md.new_paragraph("重要性分布")
    md.new_paragraph(f"![]({plots['importance']})")

    # ===== 风险 =====
    md.new_header(level=2, title="六、风险与机会")

    risk, opp = build_risk_opportunity(df)

    md.new_paragraph("风险：")
    md.new_list(risk)

    md.new_paragraph("机会：")
    md.new_list(opp)

    md.create_md_file()

df = load_data("structured_news.json")
plots = generate_plots(df)
generate_markdown(df, plots)
print("✅ 报告生成完成（Markdown + 图表）")
