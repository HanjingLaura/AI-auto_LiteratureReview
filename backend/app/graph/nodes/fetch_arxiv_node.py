import arxiv
from datetime import datetime,timedelta
from app.graph.state import ResearchState,PaperMetadata

# 抓取论文节点
def fetch_arxiv_node(state:ResearchState):
    """
    抓取节点：负责根据关键词去 arXiv 获取数据
    """
    # 当前抓取的关键词
    current_queries = state.get("queries", [])
    status_msg = f"正在抓取关键词: {', '.join(current_queries)}"
    
    # 根据arxiv_id论文去重
    existing_ids = {p['arxiv_id'] for p in state.get("raw_papers", [])}
    new_found_papers = []
    
    # 创建一个客户端对象
    client = arxiv.Client()
    
    # 抓取论文功能实现
    for query in current_queries:
        search = arxiv.Search(
            query=query,
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        try:
            # 抓取未重复的论文
            for result in client.results(search):
                if result.entry_id not in existing_ids:
                    paper: PaperMetadata = {
                        "title": result.title,
                        "authors": [a.name for a in result.authors],
                        "summary": result.summary.replace('\n', ' '),
                        "arxiv_id": result.entry_id,
                        "published": result.published.strftime("%Y-%m-%d"),
                        "pdf_url": result.pdf_url
                    }
                    new_found_papers.append(paper)
                    existing_ids.add(result.entry_id)
        except Exception as e:
            # 抛出并记录异常
            return {"error_log": [f"抓取关键词 {query} 失败: {str(e)}"]}
    
    # 返回更新后的状态
    return {
        "raw_papers": new_found_papers,
        "current_status": f"{status_msg} | 抓取成功，当前共有 {len(existing_ids)} 篇论文",
        "iteration_count": state.get("iteration_count", 0) + 1
    }