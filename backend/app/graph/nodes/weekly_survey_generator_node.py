import csv
import io
from openai import OpenAI
from datetime import datetime
from app.graph.state import ResearchState, LLMConfig


def _escape_markdown_cell(value: str) -> str:
    text = (value or "").replace("\n", " ").replace("\r", " ")
    return text.replace("|", "\\|")

def weekly_survey_generator_node(state: ResearchState):
    """
    生成每周综述节点：按照四个维度生成综述报告
    """
    taxonomy = state.get("taxonomy_md", "暂无分类数据")
    csv_data = state.get("comparison_table_csv", "暂无对比数据")
    cards = state.get("paper_cards", [])

    try:
        # 基于分类体系、对比表和卡片直接生成综述，不再依赖中间 summary 字段
        client = OpenAI(
            base_url=LLMConfig.BASE_URL,
            api_key=LLMConfig.API_KEY
        )

        insight_response = client.chat.completions.create(
            model=LLMConfig.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位严谨的文献综述撰写者，擅长从分类体系、方法对比和论文卡片中提炼趋势、空白与未来方向。"
                        "除论文元数据外，所有输出必须使用中文。"
                        "论文元数据（如论文标题、作者名、arXiv ID、数据集名、模型专有名词）保持原文，不要翻译。"
                    )
                },
                {
                    "role": "user",
                    "content": f"""请基于以下三部分材料撰写综述中的‘研究趋势分析’与‘研究空白与未来方向’两部分：

1. 分类体系（Taxonomy）
{taxonomy}

2. 方法对比表（CSV）
{csv_data}

3. 论文卡片摘要
{cards}

要求：
0. 除论文元数据外，全文使用中文；论文元数据保持原文不翻译。
1. 先总结当前研究路线的总体演进趋势，明确从什么到什么的变化。
2. 再指出至少两个明确的研究空白，并提出具有可执行性的原创方向。
3. 风格要像正式课程作业中的学术综述，避免空泛套话。
4. 输出内容请按‘趋势分析’和‘未来方向’两个小节组织。"""
                }
            ]
        )
        insights = insight_response.choices[0].message.content or ""

        # 组装最终 Markdown
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        final_report = f"""# 学术综述报告：领域前沿与自动化分析

**生成日期**: {current_date}
**收录样本数**: {len(cards)} 篇

---

## 1. 分类体系 (Taxonomy)
> 对应要求：通过聚类分析构建的技术版图
{taxonomy}

---

## 2. 方法对比表 (Methodology Comparison)
> 对应要求：涵盖复杂度、场景、数据驱动属性等核心维度
> 详细 CSV 数据已同步导出至本地文件夹

| 论文标题 | 核心方法 | 复杂度 | 适用场景 | 优缺点 | 数据驱动 |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        # 使用标准 CSV 解析，避免字段中逗号/引号导致列错位
        parsed_rows = list(csv.reader(io.StringIO((csv_data or "").strip())))
        data_rows = parsed_rows[1:6] if len(parsed_rows) > 1 else []
        for row in data_rows:
            cells = list(row[:6])
            if len(cells) < 6:
                cells.extend([""] * (6 - len(cells)))
            safe_cells = [_escape_markdown_cell(c) for c in cells]
            final_report += "| " + " | ".join(safe_cells) + " |\n"

        final_report += f"""
---

## 3. 研究趋势分析 (Research Trends)
{insights.split('未来方向')[0] if '未来方向' in insights else insights}

---

## 4. 研究空白与未来方向 (Gaps & Future Directions)
> **核心原创观点**
{insights.split('未来方向')[-1] if '未来方向' in insights else "（详见上文趋势推演）"}

---

## 附录：本周解析卡片详情 (Appendix)
"""
        for card in cards[:5]:
            final_report += f"- **[{card.innovation_type}]** {card.title} | 核心思路: {card.key_idea}\n"

        return {
            "weekly_digest": final_report,
            "current_status": "综述报告生成完毕！"
        }

    except Exception as e:
        return {"error_log": [f"报告生成异常: {str(e)}"]}