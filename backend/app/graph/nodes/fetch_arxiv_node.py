import arxiv
import time
import random
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

    # 创建一个客户端对象，设置延迟时间以避免限速
    client = arxiv.Client(
        delay_seconds=5.0,  # 更长的延迟
        num_retries=5        # 更多重试
    )

    # 抓取论文功能实现
    total_attempts = 0
    max_total_attempts = 100  # 最大总尝试次数

    while len(existing_ids) < 50 and total_attempts < max_total_attempts:
        total_attempts += 1

        # 轮询每个关键词
        for query in current_queries:
            if len(existing_ids) >= 50:
                break

            # 随机延迟，避免固定模式
            if total_attempts > 1:
                time.sleep(random.uniform(2, 8))

            # 每次尝试减少结果数量，避免触发限速
            max_results = min(3, 50 - len(existing_ids))

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            try:
                # 抓取未重复的论文
                query_results = []
                results_count = 0

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
                        query_results.append(paper)
                        existing_ids.add(result.entry_id)
                        results_count += 1

                        # 如果已经达到目标数量，停止这次搜索
                        if len(existing_ids) >= 50:
                            break

                new_found_papers.extend(query_results)

                if results_count > 0:
                    status_msg = f"正在抓取关键词: {', '.join(current_queries)} | 第{total_attempts}次尝试找到{results_count}篇论文，当前共{len(existing_ids)}篇"
                else:
                    # 如果没有找到论文，增加延迟时间
                    status_msg = f"正在抓取关键词: {', '.join(current_queries)} | 第{total_attempts}次尝试未找到论文，增加延迟等待"
                    time.sleep(10)
                    continue

            except arxiv.HTTPError as e:
                # 尝试获取状态码，不同版本的 arxiv 库可能使用不同的属性名
                status_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)
                if status_code == 429:
                    # 被限速，等待更长时间
                    wait_time = 30 + random.randint(0, 20)
                    status_msg = f"遇到限速(HTTP 429)，等待 {wait_time} 秒后继续 | 第{total_attempts}次尝试"
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = f"抓取关键词 {query} 失败: HTTP {status_code}" if status_code else f"抓取关键词 {query} 失败: {str(e)}"
                    return {"error_log": [error_msg]}
            except Exception as e:
                # 抛出并记录异常
                return {"error_log": [f"抓取关键词 {query} 失败: {str(e)}"]}

        # 如果一轮循环后没有新增论文，尝试更换搜索策略
        if total_attempts % 3 == 0 and len(new_found_papers) > 0:
            # 尝试使用更简单的关键词
            simple_queries = ["learning", "network", "graph"]
            for simple_query in simple_queries:
                if len(existing_ids) >= 50:
                    break

                search = arxiv.Search(
                    query=simple_query,
                    max_results=3,
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )

                try:
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

                    if len(existing_ids) > len([p for p in new_found_papers if p['arxiv_id'] in [e['arxiv_id'] for e in state.get("raw_papers", [])]]):
                        status_msg += f" | 使用简单关键词'{simple_query}'新增论文"

                except Exception:
                    continue

    # 返回更新后的状态
    total_new_papers = len([p for p in new_found_papers if p['arxiv_id'] not in [e['arxiv_id'] for e in state.get("raw_papers", [])]])

    if total_new_papers > 0:
        status_msg = f"{status_msg} | 抓取完成，新增{total_new_papers}篇论文，当前共{len(existing_ids)}篇论文"
    else:
        status_msg = f"{status_msg} | 抓取完成，但未找到新论文，当前共{len(existing_ids)}篇论文"

    return {
        "raw_papers": new_found_papers,
        "current_status": f"{status_msg} | 抓取成功，当前共有 {len(existing_ids)} 篇论文",
        "iteration_count": state.get("iteration_count", 0) + 1
    }

