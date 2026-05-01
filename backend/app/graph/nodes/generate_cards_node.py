import instructor
from openai import OpenAI
from app.graph.state import ResearchState, PaperCard, LLMConfig

# 生成论文卡片节点
def generate_cards_node(state: ResearchState):
    """
    LLM 解析生成论文卡片节点：利用 Pydantic 模型强制结构化输出
    """
    # 找出已抓取但尚未生成卡片的论文
    processed_titles = {c.title for c in state.get("paper_cards", [])}
    to_process = [p for p in state["raw_papers"] if p['title'] not in processed_titles]

    # 如果没有需要处理的论文，直接更新状态返回
    if not to_process:
        return {
            "current_status": "所有论文已完成结构化解析",
            "paper_cards": [] 
        }

    # 初始化客户端
    client = instructor.from_openai(OpenAI(
        base_url=LLMConfig.BASE_URL,
        api_key=LLMConfig.API_KEY
    ))

    new_cards = []
    
    # 分批处理论文
    batch = to_process[:5] 
    remaining_count = len(to_process) - len(batch)
    
    for paper in batch:
        try:
            # 利用 instructor 强制要求 LLM 输出符合 PaperCard 定义的 JSON 格式
            card = client.chat.completions.create(
                model=LLMConfig.MODEL_NAME,
                response_model=PaperCard,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个资深科研助手。请严格根据提供的标题和摘要提取核心信息。"
                            "除论文元数据外，所有输出请使用中文。"
                            "论文元数据包括：title、作者名、arXiv ID、数据集/基准名称、模型专有名词，"
                            "这些内容保持原文，不要翻译。"
                        ),
                    },
                    {"role": "user", "content": f"标题: {paper['title']}\n摘要: {paper['summary']}"}
                ]
            )
            new_cards.append(card)
        except Exception as e:
            # 抛出并记录异常
            return {"error_log": [f"解析论文《{paper['title']}》失败: {str(e)}"]}

    return {
        "paper_cards": new_cards,
        "current_status": f"正在解析论文... 本次新增 {len(new_cards)} 篇，剩余 {remaining_count} 篇待处理"
    }