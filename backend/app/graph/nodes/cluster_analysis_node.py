import csv
import io
import json
import re
from openai import OpenAI
from app.graph.state import ResearchState, LLMConfig


def _extract_json_object(text: str) -> str:
    if not text:
        return ""
    # 尝试提取最后一个 JSON 对象块
    start = text.rfind('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return ""
    candidate = text[start:end+1]
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        # 逐步向前寻找可能的开头
        for i in range(start, -1, -1):
            if text[i] == '{':
                candidate = text[i:end+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue
    return ""


def _normalize_non_metadata_text(text: str) -> str:
    """对非元数据文本做保底中文化替换。"""
    normalized = text or ""
    replacements = {
        "Pros:": "优点：",
        "Cons:": "缺点：",
        "Pros": "优点",
        "Cons": "缺点",
        "Advantages": "优点",
        "Disadvantages": "缺点",
        "Low-to-Medium": "中低",
        "Medium-to-High": "中高",
        "High": "高",
        "Medium": "中",
        "Low": "低",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def _normalize_boolean_zh(value: str) -> str:
    val = (value or "").strip().lower()
    if val in {"yes", "y", "true", "1", "是"}:
        return "是"
    if val in {"no", "n", "false", "0", "否"}:
        return "否"
    return value


def _normalize_complexity_zh(value: str) -> str:
    raw = (value or "").strip()
    lower = raw.lower()
    # 先处理区间表达
    if re.search(r"low\s*[-/]?\s*to\s*[-/]?\s*medium", lower):
        return "中低"
    if re.search(r"medium\s*[-/]?\s*to\s*[-/]?\s*high", lower):
        return "中高"
    if lower == "high":
        return "高"
    if lower == "medium":
        return "中"
    if lower == "low":
        return "低"
    return _normalize_non_metadata_text(raw)


def _normalize_comparison_csv(csv_text: str) -> str:
    """标准化 CSV：保持元数据原文，对非元数据字段做中文化保底处理。"""
    if not csv_text or not csv_text.strip():
        return "Title,Method,Complexity,Scenarios,Pros_and_Cons,Is_Data_Driven"

    reader = csv.reader(io.StringIO(csv_text.strip()))
    rows = list(reader)
    if not rows:
        return "Title,Method,Complexity,Scenarios,Pros_and_Cons,Is_Data_Driven"

    header = [
        "Title",
        "Method",
        "Complexity",
        "Scenarios",
        "Pros_and_Cons",
        "Is_Data_Driven",
    ]

    normalized_rows = [header]
    data_rows = rows[1:] if len(rows) > 1 else []
    for row in data_rows:
        cells = list(row[:6])
        if len(cells) < 6:
            cells.extend([""] * (6 - len(cells)))

        # Title 视为元数据，保持原文
        title = cells[0]
        method = _normalize_non_metadata_text(cells[1])
        complexity = _normalize_complexity_zh(cells[2])
        scenarios = _normalize_non_metadata_text(cells[3])
        pros_cons = _normalize_non_metadata_text(cells[4])
        is_data_driven = _normalize_boolean_zh(cells[5])

        normalized_rows.append([title, method, complexity, scenarios, pros_cons, is_data_driven])

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerows(normalized_rows)
    return out.getvalue().strip()

# 聚类分析节点
def cluster_analysis_node(state: ResearchState):
    """
    聚类分析节点：
    1. 生成分类体系 (taxonomy_md)
    2. 生成方法对比表 (comparison_table_csv)
    """
    cards = state.get("paper_cards", [])
    
    # 如果没有卡片则跳过分析
    if not cards:
        return {
            "current_status": "聚类分析跳过：未发现已解析的论文卡片",
            "taxonomy_md": "暂无数据",
            "comparison_table_csv": "Title,Method,Complexity,Scenarios,Pros_and_Cons,Is_Data_Driven"
        }

    # 提取对比素材
    analysis_context = []
    for c in cards:
        analysis_context.append({
            "title": c.title,
            "method": c.method,
            "key_idea": c.key_idea,
            "complexity_hint": f"Metrics: {c.metrics}, Method: {c.method}", 
            "scenario": c.dataset_or_scenario,
            "limitations": c.limitations
        })

    # 初始化客户端
    client = OpenAI(
        base_url=LLMConfig.BASE_URL,
        api_key=LLMConfig.API_KEY
    )

    try:
        # 调用 LLM 进行跨论文的横向对比与纵向聚类
        response = client.chat.completions.create(
            model=LLMConfig.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """你是一位精通文献综述的学术专家。请根据提供的论文数据完成：

                                1. 构建 Taxonomy：归纳 3-5 个核心研究方向，使用 Markdown 标题级联。
                                2. 构建方法对比表 (CSV)：
                                - Title: 论文标题
                                - Method: 核心算法/方法
                                - Complexity: 分析复杂度或计算开销 (如 O(n^2), High, Low)
                                - Scenarios: 适用场景 (如 移动端, 大规模集群, 医疗等)
                                - Pros_and_Cons: 优缺点总结
                                - Is_Data_Driven: 是否数据驱动 (填 是/否)

                                全局语言要求：
                                - 除论文元数据外，所有说明文字均使用中文输出。
                                - 论文元数据（如论文标题、作者名、arXiv ID、数据集名、模型专有名词）保持原文，不要翻译。
                                - 对比表中 Complexity、Scenarios、Pros_and_Cons 的解释文本必须使用中文。

                                请在最终输出中只返回一个 JSON 对象，包含 taxonomy_markdown 和 comparison_csv 两个字段，不要添加多余文本。"""
                },
                {
                    "role": "user",
                    "content": f"以下是 {len(cards)} 篇论文的精炼数据，请进行聚类与对比分析：\n{analysis_context}"
                }
            ]
        )

        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and getattr(choice.message, 'content', None):
                content = choice.message.content
            elif getattr(choice, 'content', None):
                content = choice.content
            else:
                content = ""
        elif isinstance(response, dict):
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            content = ""

        if not content:
            raise ValueError('LLM 未返回文本内容')

        json_text = _extract_json_object(content)
        if not json_text:
            raise ValueError(f'无法解析 LLM 输出 JSON，原始内容：{content[:1000]}')

        parsed = json.loads(json_text)
        taxonomy_md = parsed.get('taxonomy_markdown', '').strip()
        comparison_csv = parsed.get('comparison_csv', '').strip()
        if not taxonomy_md and not comparison_csv:
            raise ValueError(f'LLM 返回 JSON 但字段为空，原始内容：{content[:1000]}')

        normalized_csv = _normalize_comparison_csv(comparison_csv)
        return {
            "taxonomy_md": taxonomy_md,
            "comparison_table_csv": normalized_csv,
            "current_status": f"分类体系与方法对比表已生成，共分析 {len(cards)} 篇论文"
        }

    except Exception as e:
        # 抛出并记录异常
        return {
            "error_log": [f"cluster_analysis_node 运行出错: {str(e)}"],
            "current_status": "聚类分析节点执行异常"
        }