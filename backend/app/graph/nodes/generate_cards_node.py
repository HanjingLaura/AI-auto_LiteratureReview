import instructor
from openai import OpenAI
from app.graph.state import ResearchState, PaperCard
from dotenv import load_dotenv
import os

load_dotenv()  
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

def generate_cards_node(state: ResearchState):
    """
    LLM 解析生成论文卡片节点：利用 Pydantic 模型强制结构化输出
    """
    # 找出还没处理过的论文
    processed_titles = {c.title for c in state.get("paper_cards", [])}
    to_process = [p for p in state["raw_papers"] if p['title'] not in processed_titles]

    if not to_process:
        return {"current_status": "所有抓取的论文已解析完成"}

    # 初始化客户端，配置LLM
    client = instructor.from_openai(OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    ))

    new_cards = []
    
    # 遍历解析
    for paper in to_process[:3]:
        try:
            # response_model 直接传入你的 PaperCard 类
            card = client.chat.completions.create(
                model="qwen-plus",
                response_model=PaperCard,
                messages=[
                    {"role": "system", "content": "你是一个严谨的科研助手。请根据标题和摘要提取核心信息。"},
                    {"role": "user", "content": f"标题: {paper['title']}\n摘要: {paper['summary']}"}
                ]
            )
            new_cards.append(card)
        except Exception as e:
            # 抛出并记录异常
            state["error_log"].append(f"解析论文《{paper['title']}》时出错: {str(e)}")

    return {
        "paper_cards": new_cards,
        "current_status": f"深度解析完成，本次生成了 {len(new_cards)} 张研究卡片"
    }