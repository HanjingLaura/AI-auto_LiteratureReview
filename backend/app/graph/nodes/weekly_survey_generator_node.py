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
    queries = state.get("queries",[])
    taxonomy = state.get("taxonomy_md", "暂无分类数据")
    csv_data = state.get("comparison_table_csv", "暂无对比数据")
    cards = state.get("paper_cards", [])

    def _clean_insights(text: str) -> str:
        if not text:
            return ""
        import re

        lines = [line.rstrip() for line in text.splitlines()]
        cleaned = []
        # drop heading-only lines, including markdown headings or bold headings
        heading_re = re.compile(
            r"^(研究趋势(分析)?|研究空白(与未来方向)?|未来方向|Research\s+Trends|Gaps\s*&\s*Future\s*Directions)$",
            re.IGNORECASE,
        )

        def _is_heading_only(raw: str) -> bool:
            if not raw:
                return True
            line = raw.strip()
            if line == "**":
                return True
            # strip markdown heading markers
            line = line.lstrip("#").strip()
            # strip bold markers
            if line.startswith("**") and line.endswith("**"):
                line = line.strip("*").strip()
            # remove leading numbering like '3.' or '4.'
            line = re.sub(r"^\d+\.?\s*", "", line).strip()
            return bool(heading_re.match(line))

        for line in lines:
            if not line:
                continue
            if _is_heading_only(line):
                continue
            cleaned.append(line.strip())
        return "\n".join(cleaned).strip()

    try:
        # 基于分类体系、对比表和卡片直接生成综述，不再依赖中间 summary 字段
        client = OpenAI(
            base_url=LLMConfig.BASE_URL,
            api_key=LLMConfig.API_KEY
        )

        # 调用一次 LLM 生成“研究趋势分析”小节
        trends_resp = client.chat.completions.create(
            model=LLMConfig.MODEL_NAME,
            temperature=0.2,
            max_tokens=800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位严谨的学术综述撰写者，擅长从分类体系、方法对比和论文卡片中提炼可验证的研究趋势与判断。"
                        "全部输出必须使用中文（但论文元数据如标题/作者/arXiv ID 等保留原文）。"
                    )
                },
                {
                    "role": "user",
                    "content": f"""任务：请仅生成“研究趋势分析（Research Trends）”小节的内容，要求返回 Markdown 格式的要点列表（1-5 条）。每条要点须包含两部分：
1) 要点（一句话总结该趋势）；
2) 支持证据（1-2 句，引用分类体系、方法对比表或论文卡片中的关键信息作为证据）。

输入资料：
1. 分类体系（Taxonomy）
{taxonomy}

2. 方法对比表（CSV）
{csv_data}

3. 论文卡片摘要（仅关键信息）
{cards}

约束：
- 只输出《研究趋势分析》小节内容，不要输出其它标题或解释性前言；
- 使用清晰的编号（1., 2., ...），每个编号下用短段落给出“要点”与“证据”；
- 风格学术且具体，避免空泛措辞；输出尽量简洁，便于直接拼接进最终报告。
注意：本小节将作为最终综述的第 3 部分（研究趋势分析），不要出现分类体系或方法对比表的标题。"""
                }
            ]
        )
        trends = trends_resp.choices[0].message.content or ""

        # 再次调用 LLM 生成“研究空白与未来方向”小节
        gaps_resp = client.chat.completions.create(
            model=LLMConfig.MODEL_NAME,
            temperature=0.2,
            max_tokens=1000,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一位面向工程与研究的综述作者，擅长提出可执行的研究方向与实验设计，并能将建议具体化为可验证的步骤。"
                        "所有输出使用中文，论文元数据保留原文。"
                    )
                },
                {
                    "role": "user",
                    "content": f"""任务：请仅生成“研究空白与未来方向（Gaps & Future Directions）”小节，要求识别并描述至少两个清晰的研究空白，并为每个空白提供：

- 问题陈述（1-2 句，明确限定研究问题）
- 建议技术路线要点（分项列出 3-5 个关键步骤或方法组件）
- 验证方案（推荐合适的数据集、评价指标与实验设计要点）

输入资料：
1. 分类体系（Taxonomy）
{taxonomy}

2. 方法对比表（CSV）
{csv_data}

3. 论文卡片摘要
{cards}

约束：
- 每个研究方向必须包含“原创观点”，不要复述已有工作；
- 每个研究方向请使用子标题或编号分开，并严格按照“问题陈述 / 技术路线要点 / 验证方案”结构输出；
- 输出尽量具体、具有可实施性，避免泛化建议；
- 不要输出额外的解释或总结段落，便于直接拼接进最终报告。
注意：本小节将作为最终综述的第 4 部分（研究空白与未来方向），必须体现原创观点。"""
                }
            ]
        )
        gaps = gaps_resp.choices[0].message.content or ""

        # 组装最终 Markdown
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        query_text = ", ".join([q for q in queries if q])
        final_report = f"""# 学术综述报告

    关键词: {query_text or "-"}
    生成日期: {current_date}
    收录样本数: {len(cards)} 篇

---

## 1. 分类体系 (Taxonomy)
{taxonomy}

---

## 2. 方法对比表 (Methodology Comparison)

| 论文标题 | 核心方法 | 复杂度 | 适用场景 | 优缺点 | 数据驱动 |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        # 使用标准 CSV 解析，避免字段中逗号/引号导致列错位
        parsed_rows = list(csv.reader(io.StringIO((csv_data or "").strip())))
        data_rows = parsed_rows[1:6] if len(parsed_rows) > 1 else []
        for row in data_rows:
            if len(row) > 6:
                tail = row[-1]
                is_data_driven = tail.strip().lower() in {"是", "否", "yes", "no", "true", "false", "1", "0"}
                if is_data_driven:
                    pros_cons = ", ".join(row[4:-1])
                    cells = list(row[:4]) + [pros_cons, tail]
                else:
                    cells = list(row[:5]) + [", ".join(row[5:])]
            elif len(row) == 6:
                cells = list(row)
            else:
                cells = list(row)
                if len(cells) < 6:
                    cells.extend([""] * (6 - len(cells)))
            safe_cells = [_escape_markdown_cell(c) for c in cells]
            final_report += "| " + " | ".join(safe_cells) + " |\n"

        final_report += f"""
---

## 3. 研究趋势分析 (Research Trends)
{_clean_insights(trends)}

---

## 4. 研究空白与未来方向 (Gaps & Future Directions)
{_clean_insights(gaps)}

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