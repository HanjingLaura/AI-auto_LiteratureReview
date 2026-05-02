from typing import Annotated, List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator
import os
from dotenv import load_dotenv

# 统一加载环境变量
load_dotenv()

# 配置管理类
class LLMConfig:
    # 模型切换逻辑：读取环境变量
    USE_LOCAL = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    
    # 根据切换选择配置
    API_KEY = os.getenv("LOCAL_API_KEY") if USE_LOCAL else os.getenv("API_KEY")
    BASE_URL = os.getenv("LOCAL_BASE_URL") if USE_LOCAL else os.getenv("BASE_URL")
    
    # 模型名称切换
    MODEL_NAME = os.getenv("LOCAL_MODEL_NAME") if USE_LOCAL else os.getenv("MODEL_NAME")

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
    # 基础控制流
    queries: List[str] # 搜索关键词列表
    iteration_count: int # 循环计数
    current_status: str # 节点进度追踪文字描述
    error_log: Annotated[List[str], operator.add] # 错误日志

    # 数据资产
    raw_papers: Annotated[List[PaperMetadata], operator.add] # 原始论文列表
    paper_cards: Annotated[List[PaperCard], operator.add] # 格式化后的论文卡片列表

    # 聚类与对比分析产物
    taxonomy_md: str # 对应 taxonomy.md 的内容
    comparison_table_csv: str # 对应 comparison_table.csv 的内容

    # 最终产出综述摘要
    weekly_digest: str # 对应 weekly_digest.md 的内容