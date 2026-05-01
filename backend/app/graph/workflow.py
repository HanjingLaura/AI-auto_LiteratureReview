from langgraph.graph import StateGraph, END
from app.graph.state import ResearchState
from app.graph.nodes.fetch_arxiv_node import fetch_arxiv_node
from app.graph.nodes.generate_cards_node import generate_cards_node
from app.graph.nodes.cluster_analysis_node import cluster_analysis_node
from app.graph.nodes.weekly_survey_generator_node import weekly_survey_generator_node

# 检查是否还有未处理的 raw_papers
def should_continue_parsing(state: ResearchState):
    processed_titles = {c.title for c in state.get("paper_cards", [])}
    to_process = [p for p in state["raw_papers"] if p['title'] not in processed_titles]
    
    if len(to_process) > 0:
        return "continue"
    return "analyze"

# 构建工作流
workflow = StateGraph(ResearchState)

# 添加节点
workflow.add_node("fetch_papers", fetch_arxiv_node)
workflow.add_node("generate_cards", generate_cards_node)
workflow.add_node("cluster_analysis", cluster_analysis_node)
workflow.add_node("generate_survey", weekly_survey_generator_node)

# 设置入口
workflow.set_entry_point("fetch_papers")

# 设置边
workflow.add_edge("fetch_papers", "generate_cards")

# 条件循环：直到所有抓取的论文都生成了卡片再进入聚类
workflow.add_conditional_edges(
    "generate_cards",
    should_continue_parsing,
    {
        "continue": "generate_cards",
        "analyze": "cluster_analysis"
    }
)

workflow.add_edge("cluster_analysis", "generate_survey")
workflow.add_edge("generate_survey", END)

# 编译应用
app = workflow.compile()