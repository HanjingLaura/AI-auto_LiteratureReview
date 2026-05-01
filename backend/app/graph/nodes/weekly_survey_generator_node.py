import instructor
from openai import OpenAI
from datetime import datetime
from app.graph.state import ResearchState, LLMConfig

def weekly_survey_generator_node(state: ResearchState):
    """
    生成每周综述节点：按照四个维度生成综述报告
    """
    taxonomy = state.get("taxonomy_md", "暂无分类数据")
    csv_data = state.get("comparison_table_csv", "暂无对比数据")
    analysis_summary = state.get("analysis_summary", "")
    cards = state.get("paper_cards", [])

    # 初始化客户端
    client = instructor.from_openai(OpenAI(
        base_url=LLMConfig.BASE_URL,
        api_key=LLMConfig.API_KEY
    ))

    try:
        # LLM 生成趋势分析与原创见解
        insight_response = client.chat.completions.create(
            model=LLMConfig.MODEL_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": "你是一位拥有前瞻性视野的首席科学家，擅长从琐碎的研究中发现宏观趋势和尚未解决的深层矛盾。"
                },
                {
                    "role": "user", 
                    "content": f"""基于以下论文分析总结：
                    {analysis_summary}
                    
                    请完成以下两项深度分析：
                    1. 研究趋势分析：总结当前技术演进的路径（从 A 到 B 的转变）。
                    2. 研究空白与未来方向：找出当前文献中被忽视的角落，并提出至少两个具有挑战性的原创研究设想。
                    
                    要求：观点深刻，避免套话，体现学术前沿性。"""
                }
            ]
        )
        insights = insight_response.choices[0].message.content

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
        rows = csv_data.strip().split('\n')[1:6]
        for row in rows:
            # CSV 转 MD 表格
            final_report += "| " + " | ".join(row.split(',')) + " |\n"

        final_report += f"""
                        ---

                        ## 3. 研究趋势分析 (Research Trends)
                        {insights.split('2.')[0] if '2.' in insights else insights}

                        ---

                        ## 4. 研究空白与未来方向 (Gaps & Future Directions)
                        > **核心原创观点**
                        {insights.split('2.')[1] if '2.' in insights else "（详见下文趋势推演）"}

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