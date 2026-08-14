"""Task Definitions for the Real-World Evaluation Suite (10 Tasks)."""

from __future__ import annotations

from typing import Dict, List

from core.evaluation.models import EvaluationTaskSpec


def get_all_evaluation_tasks() -> List[EvaluationTaskSpec]:
    """Return all 10 Real-World Evaluation Suite task specifications."""
    return [
        EvaluationTaskSpec(
            task_id="task_01",
            task_number=1,
            title="AI Industry Research",
            domain="Artificial Intelligence / Frontier Models",
            prompt=(
                "Conduct a comprehensive research report on the latest frontier AI models released during the last 12 months. "
                "Compare OpenAI, Anthropic, Google DeepMind, Meta, xAI, Alibaba, and DeepSeek. Include benchmark comparisons, "
                "context windows, pricing (if public), strengths, weaknesses, multimodal capabilities, coding performance, "
                "reasoning ability, and enterprise adoption. Generate tables, charts, citations, and conclude which model is best "
                "for coding, research, education, and enterprise use."
            ),
            tested_capabilities=[
                "Search",
                "Browser",
                "Research",
                "Verification",
                "Reflection",
                "Report generation",
            ],
            expected_sections=[
                "Executive Summary",
                "Comparative Benchmark Table",
                "Pricing & Context Windows",
                "Strengths & Weaknesses Matrix",
                "Coding & Mathematical Reasoning Analysis",
                "Enterprise Adoption & Multimodal Landscape",
                "Strategic Recommendations",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_01_ai_industry_research.md",
        ),
        EvaluationTaskSpec(
            task_id="task_02",
            task_number=2,
            title="Company Analysis – NVIDIA",
            domain="Financial & Semiconductor Analysis",
            prompt=(
                "Analyze NVIDIA as if you were preparing an investment research report. Collect the latest quarterly financial results, "
                "AI product announcements, Blackwell architecture updates, major partnerships, competitors, market share, stock performance, "
                "risks, and analyst opinions. Summarize future opportunities and risks with evidence."
            ),
            tested_capabilities=[
                "Financial research",
                "News aggregation",
                "Trend analysis",
                "Multi-source verification",
            ],
            expected_sections=[
                "Executive Investment Briefing",
                "Financial Performance & Segment Revenue",
                "Blackwell Architecture (B200 / GB200 NVL72) & AI Ecosystem",
                "Strategic Enterprise Partnerships",
                "Competitive Landscape (AMD MI300X, Custom ASICs)",
                "Risk Factors & Supply Chain Vulnerabilities",
                "Analyst Consensus & 3-Year Outlook",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_02_nvidia_company_analysis.md",
        ),
        EvaluationTaskSpec(
            task_id="task_03",
            task_number=3,
            title="Medical Literature Review – Alzheimer's Disease",
            domain="Biomedical & Clinical Research",
            prompt=(
                "Prepare an evidence-based literature review on Alzheimer's disease treatments published during the last five years. "
                "Compare FDA-approved drugs, experimental therapies, clinical trial outcomes, limitations, and future research directions. "
                "Every medical claim must include supporting references."
            ),
            tested_capabilities=[
                "Scientific research",
                "Citation quality",
                "Contradiction handling",
            ],
            expected_sections=[
                "Clinical Overview & Therapeutic Unmet Need",
                "FDA-Approved Anti-Amyloid Therapies (Lecanemab, Donanemab)",
                "Experimental Therapies & Emerging Targets (Tau, Neuroinflammation, GLP-1)",
                "Comparative Trial Efficacy & ARIA Safety Table",
                "Limitations of the Amyloid Hypothesis & Clinical Controversies",
                "Future Research & Biomarker Diagnostic Directions",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_03_alzheimers_literature_review.md",
        ),
        EvaluationTaskSpec(
            task_id="task_04",
            task_number=4,
            title="Programming Ecosystem – FastAPI Comparison",
            domain="Software Engineering & Web Frameworks",
            prompt=(
                "Research the complete ecosystem around FastAPI. Compare it with Django, Flask, Spring Boot, and ASP.NET Core. "
                "Analyze performance benchmarks, scalability, deployment strategies, security practices, community adoption, GitHub activity, "
                "and enterprise usage. Recommend the best framework for startups, enterprises, and AI systems."
            ),
            tested_capabilities=[
                "Documentation retrieval",
                "GitHub analysis",
                "Technical reasoning",
            ],
            expected_sections=[
                "Ecosystem Architecture & Async ASGI Foundation",
                "Comprehensive Multi-Framework Comparison Table",
                "Throughput & P99 Latency Performance Benchmarks",
                "Scalability & Containerized Deployment Strategies",
                "Security Architecture & Authentication Best Practices",
                "GitHub Activity & Community Adoption Analysis",
                "Architectural Recommendations by Organizational Scale",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_04_fastapi_ecosystem_comparison.md",
        ),
        EvaluationTaskSpec(
            task_id="task_05",
            task_number=5,
            title="Cybersecurity Investigation – Ransomware Attacks",
            domain="Cybersecurity & Threat Intelligence",
            prompt=(
                "Investigate the most significant ransomware attacks reported during the past year. Explain attack vectors, affected "
                "organizations, financial impact, mitigation strategies, government responses, and lessons learned. Produce an executive "
                "report suitable for a Chief Information Security Officer."
            ),
            tested_capabilities=[
                "Timeline building",
                "Threat intelligence",
                "Evidence aggregation",
            ],
            expected_sections=[
                "Chief Information Security Officer (CISO) Executive Briefing",
                "Major Annual Ransomware Campaigns (Change Healthcare, CDK Global)",
                "Root Cause & Attack Vector Analysis",
                "Financial Impact, Extortion Dynamics & Recovery Cost",
                "Zero-Trust Mitigation & Ransomware Defense Matrix",
                "Government Interventions & Regulatory Directives",
                "Strategic Lessons Learned & CISO Action Plan",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_05_ransomware_cybersecurity_report.md",
        ),
        EvaluationTaskSpec(
            task_id="task_06",
            task_number=6,
            title="Climate & Energy Research – Renewable Energy Worldwide",
            domain="Energy & Climate Economics",
            prompt=(
                "Research the current state of renewable energy worldwide. Compare solar, wind, hydro, geothermal, and nuclear energy "
                "using the latest publicly available statistics. Analyze costs, efficiency, carbon emissions, government policies, "
                "and future projections. Recommend an optimal energy mix for developing countries."
            ),
            tested_capabilities=[
                "Statistical analysis",
                "Data visualization",
                "Multi-domain reasoning",
            ],
            expected_sections=[
                "Global Renewable Energy Transition Overview",
                "Comparative Generation Matrix (Solar, Wind, Hydro, Geothermal, Nuclear)",
                "Levelized Cost of Energy (LCOE) & Efficiency Curves",
                "Lifecycle Carbon Emissions & Grid Interconnection Analysis",
                "Government Subsidies & International Climate Policies",
                "Optimal Energy Mix Blueprint for Developing Economies",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_06_global_renewable_energy_research.md",
        ),
        EvaluationTaskSpec(
            task_id="task_07",
            task_number=7,
            title="Software Engineering Analysis – Kubernetes Architecture",
            domain="Cloud Native Architecture & Systems Engineering",
            prompt=(
                "Analyze the architecture of the Kubernetes project using its official documentation and source repository. Explain major "
                "components, scheduling, networking, storage, security, scalability, and deployment workflow. Generate diagrams and "
                "identify common misconceptions."
            ),
            tested_capabilities=[
                "Documentation analysis",
                "Code understanding",
                "Technical explanation",
            ],
            expected_sections=[
                "Architectural Overview & Control Plane / Node Topology",
                "Core Components Breakdown (API Server, Etcd, Scheduler, Kubelet)",
                "Pod Scheduling Lifecycle & Taint/Toleration Mechanics",
                "Container Networking Interface (CNI) & Service Mesh Layer",
                "Container Storage Interface (CSI) & Persistent Volumes",
                "Kubernetes Security Best Practices & RBAC Architecture",
                "Mermaid Deployment Workflow Diagram",
                "Common Operational Misconceptions & Anti-Patterns",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_07_kubernetes_architecture_analysis.md",
        ),
        EvaluationTaskSpec(
            task_id="task_08",
            task_number=8,
            title="Market Intelligence – Global Electric Vehicle Market",
            domain="Automotive Industry & Battery Technology",
            prompt=(
                "Compare the global electric vehicle market. Analyze Tesla, BYD, Rivian, Lucid, Hyundai, Volkswagen, and Toyota using "
                "production numbers, sales growth, battery technologies, charging ecosystems, government incentives, and future roadmaps. "
                "Recommend which companies are best positioned over the next five years."
            ),
            tested_capabilities=[
                "Business analysis",
                "Current data retrieval",
                "Comparative reasoning",
            ],
            expected_sections=[
                "Global EV Market Penetration & Production Trends",
                "Comprehensive Automaker Benchmark Matrix (Tesla, BYD, Rivian, etc.)",
                "Battery Chemistry Innovation (LFP, NMC, Solid-State Roadmaps)",
                "Charging Ecosystem Dynamics (NACS Standardization vs. CCS)",
                "Government Incentives, Subsidies & Tariff Analysis",
                "5-Year Competitive Forecast & Leadership Winners",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_08_global_ev_market_intelligence.md",
        ),
        EvaluationTaskSpec(
            task_id="task_09",
            task_number=9,
            title="Academic Research – Survey of RAG Systems",
            domain="Information Retrieval & Large Language Models",
            prompt=(
                "Prepare a survey of Retrieval-Augmented Generation (RAG) systems published during the last three years. Compare architectures, "
                "embedding models, vector databases, retrieval strategies, evaluation benchmarks, production challenges, and future research "
                "directions. Include diagrams and citations."
            ),
            tested_capabilities=[
                "Academic research",
                "Knowledge synthesis",
                "Technical writing",
            ],
            expected_sections=[
                "Evolution of RAG Architectures (Naive, Advanced, Modular, GraphRAG)",
                "Embedding Models & Vector Database Comparative Analysis",
                "Retrieval Strategies (Semantic Chunking, Hybrid Search, Re-Ranking)",
                "Evaluation Benchmarks & Metrics (RAGAS, TruLens, Answer Relevance)",
                "Production Engineering Challenges & Latency Optimization",
                "Mermaid GraphRAG & Hybrid Retrieval Workflow Diagram",
                "Future Academic Research Directions",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_09_rag_systems_academic_survey.md",
        ),
        EvaluationTaskSpec(
            task_id="task_10",
            task_number=10,
            title="Future Technology Report – Quantum Computing",
            domain="Quantum Hardware & Theoretical Computer Science",
            prompt=(
                "Produce a strategic report on quantum computing. Cover major hardware approaches, leading companies, current achievements, "
                "engineering challenges, software ecosystems, commercialization prospects, government investments, and realistic timelines. "
                "Separate established facts from expert predictions and clearly identify areas of uncertainty."
            ),
            tested_capabilities=[
                "Long-form research",
                "Distinguishing evidence from speculation",
                "Executive reporting",
            ],
            expected_sections=[
                "Strategic Executive Overview & Qubit Scaling Trajectories",
                "Hardware Modality Analysis (Superconducting, Trapped Ion, Neutral Atom, Photonic)",
                "Leading Commercial Players (IBM, Google, Quantinuum, IonQ, QuEra)",
                "Error Correction & Logical Qubit Breakthroughs",
                "Software Compilers & Quantum SDKs (Qiskit, Cirq, TKET)",
                "Evidence Verification Table: Established Facts vs. Expert Predictions",
                "Commercialization Timelines & Near-Term Use Cases",
                "Contradiction & Reflection Log",
                "References & Citations",
            ],
            output_filename="task_10_quantum_computing_strategic_report.md",
        ),
    ]
