from typing import Annotated,TypedDict,List,Optional
from pydantic import BaseModel, Field
import operator

# 论文元数据State定义
class PaperMetadata(TypedDict):
    title:str
    authors:List[str]
    summary:str
    arxiv_id: str
    published: str
    pdf_url: str
    
# 论文卡片State定义
class PaperCard(BaseModel):
    title: str = Field(..., description="论文标题")
    problem: str = Field(..., description="论文解决的核心问题")
    key_idea: str = Field(..., description="最核心的创新思路")
    method: str = Field(..., description="具体实现方法或算法")
    dataset_or_scenario: str = Field(..., description="实验数据集或应用场景")
    metrics: str = Field(..., description="评价指标及数值")
    results_summary: str = Field(..., description="实验结果简要总结")
    innovation_type: str = Field(..., description="创新类型（如架构创新、算法改进等）")
    limitations: str = Field(..., description="论文提到的局限性")
    best_fit_category: str = Field(..., description="适合的细分领域分类")
    confidence_level: float = Field(..., description="提取准确性信心评分(0-1)")
    
# Graph核心State定义
class ResearchState(TypedDict):
    queries: List[str] # 搜索关键词列表
    raw_papers: Annotated[List[PaperMetadata], operator.add] # 原始论文
    paper_cards: Annotated[List[PaperCard], operator.add] # 论文卡片
    taxonomy: dict # 分类体系
    comparison_table: str # 对比表格
    report: str # 综述总结
    iteration_count: int # 循环计数
    current_status: str # 进度追踪
    error_log: Annotated[List[str], operator.add] # 错误日志