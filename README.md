# AI行业新闻分析系统

本项目实现了一个基于大模型（Deepseek V4）构建的**AI行业新闻自动分析系统**，能从新闻中提取结构化的信息，并生成带可视化的分析报告（Markdown）。

## 特点
- 从非结构化新闻中提取结构化数据
- 使用 Deepseek V4 进行语义理解
- 可以生成可视化的图
- 可以生成 Markdown 的报告

## 结构化数据模型
参考例子
```json
{
    "id": 6,
    "title": "I/O大会开完，谷歌连搜索框都变智能体了",
    "summary": "谷歌全面转型智能体时代，发布Gemini 3.5系列模型并集成于搜索与Workspace，推出可7×24小时自主执行任务的AI智能体。",
    "category": "产品",
    "entities": [
      "Google"
    ],
    "tech_tags": [
      "LLM",
      "多模态",
      "智能体"
    ],
    "event_type": "发布",
    "sentiment": "正面",
    "importance_score": 5,
    "importance_signals": {
      "is_top_company": 1,
      "is_major_event": 1,
      "is_wide_impact": 1,
      "is_analysis": 0
    },
    "impact": "谷歌将AI智能体深度嵌入核心产品，有望重塑搜索与办公场景的人机协作模式，同时大幅降低多模态模型使用成本，加速产业竞争。",
    "keywords": [
      "Gemini 3.5",
      "谷歌I/O",
      "搜索AI",
      "Gemini Omni",
      "智能体"
    ]
  }
  ```

基于多个信号来决定事件的重要程度：

- 是否头部公司
- 是否重大事件
- 是否广泛影响
- 是否分析类

通过更严格的分类标准避免“全是正面”的问题。
