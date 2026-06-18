"""
커리큘럼 카탈로그 — 단일 소스 오브 트루스
chapter.py (학습 콘텐츠 생성) + progress.py (로드맵 API) 모두 여기서 import
각 챕터에 search_hints(arxiv_query, web_query)가 직접 내장되어 파이프라인이 챕터별 정밀 수집 가능.
"""

CURRICULUM_CATALOG: dict[str, dict] = {
    "rag": {
        "title": "RAG (검색 증강 생성)",
        "emoji": "🔍",
        "color": "#10B981",
        "description": "AI가 외부 지식을 검색해서 답하는 기술 — Naive부터 Graph RAG까지",
        "topic_names": ["RAG", "검색 증강 생성", "Retrieval Augmented Generation"],
        "kdc_class": "004",
        "collection_strategy": {
            "use_arxiv": True,
            "include_domains": ["arxiv.org", "huggingface.co", "langchain.com", "pinecone.io", "weaviate.io"],
            "rss_sources": [
                {"url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace"},
                {"url": "https://blog.langchain.dev/rss/", "name": "LangChain Blog"},
            ],
        },
        "chapters": [
            {
                "id": "rag-1",
                "title": "RAG는 왜 필요한가? — LLM의 한계와 검색의 결합",
                "description": "RAG가 왜 등장했는지 이해하고 Hallucination·Knowledge Cutoff 문제에서 검색이 어떤 역할을 하는지 설명할 수 있다",
                "level": "입문", "duration": "7분",
                "concepts": ["Hallucination", "Knowledge Cutoff", "Open-Domain QA", "Retrieval-then-Read"],
                "search_hints": {
                    "arxiv_query": "retrieval augmented generation knowledge intensive NLP Lewis 2020",
                    "web_query": "RAG retrieval augmented generation why needed LLM hallucination 2024"
                }
            },
            {
                "id": "rag-2",
                "title": "Dense Retrieval의 원리 — Bi-Encoder vs Cross-Encoder",
                "description": "Bi-Encoder와 Cross-Encoder의 속도·정확도 트레이드오프를 이해하고 검색 파이프라인에서 어떤 구조를 써야 할지 판단할 수 있다",
                "level": "기본", "duration": "9분",
                "concepts": ["Bi-Encoder", "Cross-Encoder", "SBERT", "FAISS", "HNSW", "IVF-PQ"],
                "search_hints": {
                    "arxiv_query": "dense passage retrieval bi-encoder cross-encoder reranker DPR Karpukhin 2020",
                    "web_query": "bi-encoder vs cross-encoder dense retrieval FAISS HNSW explained"
                }
            },
            {
                "id": "rag-3",
                "title": "Chunking이 검색 품질을 결정한다",
                "description": "Fixed-size vs Semantic chunking이 임베딩 벡터 및 검색 효율에 미치는 영향",
                "level": "기본", "duration": "8분",
                "concepts": ["Fixed-size Chunking", "Semantic Chunking", "Overlap", "Sentence-window", "Parent-child Retrieval"],
                "search_hints": {
                    "arxiv_query": "document chunking strategies retrieval augmented generation chunk size overlap 2024",
                    "web_query": "RAG chunking strategy semantic fixed size comparison best practices 2024"
                }
            },
            {
                "id": "rag-4",
                "title": "Query가 애매할 때 — HyDE와 Query Expansion",
                "description": "HyDE·Query2Doc의 원리를 이해하고 Zero-shot 검색 성능이 낮을 때 어떤 기법을 적용할지 판단할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["HyDE", "Query2Doc", "Query Expansion", "Pseudo Relevance Feedback", "Zero-shot Retrieval"],
                "search_hints": {
                    "arxiv_query": "HyDE hypothetical document embeddings zero-shot dense retrieval Gao 2022",
                    "web_query": "HyDE hypothetical document embeddings query expansion RAG 2024"
                }
            },
            {
                "id": "rag-5",
                "title": "Reranking으로 Top-K 정제하기",
                "description": "Cross-Encoder 재정렬 원리를 이해하고 BGE-Reranker vs Cohere Reranker 중 상황에 맞는 선택을 할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["Reranking", "BGE-Reranker", "Cohere Reranker", "MRR", "NDCG", "Reciprocal Rank Fusion"],
                "search_hints": {
                    "arxiv_query": "reranking cross-encoder retrieval augmented generation BGE reranker 2024",
                    "web_query": "RAG reranking cross-encoder BGE Cohere reranker comparison 2024"
                }
            },
            {
                "id": "rag-6",
                "title": "컨텍스트 노이즈 제거 — Lost in the Middle과 Context Compression",
                "description": "LLM이 컨텍스트 중간을 무시하는 원인을 이해하고 LLMLingua 등 압축 기법을 언제 적용할지 판단할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["Lost in the Middle", "Context Compression", "LLMLingua", "Selective Context", "Token Budget"],
                "search_hints": {
                    "arxiv_query": "lost in the middle long context LLM compression LLMLingua 2023 2024",
                    "web_query": "lost in the middle problem LLM context window RAG compression LLMLingua"
                }
            },
            {
                "id": "rag-7",
                "title": "Hybrid Search — BM25 + 벡터 검색의 결합",
                "description": "BM25와 Dense Retrieval의 약점을 이해하고 RRF로 결합했을 때 어떤 상황에서 더 강력한지 설명할 수 있다",
                "level": "중급", "duration": "8분",
                "concepts": ["BM25", "Hybrid Search", "RRF (Reciprocal Rank Fusion)", "Sparse-Dense Fusion", "Lexical Match"],
                "search_hints": {
                    "arxiv_query": "hybrid retrieval BM25 dense vector search reciprocal rank fusion 2024",
                    "web_query": "hybrid search BM25 vector retrieval RRF reciprocal rank fusion RAG"
                }
            },
            {
                "id": "rag-8",
                "title": "Self-RAG — 언제 검색하고 언제 멈출까?",
                "description": "Adaptive Retrieval의 대표 주자 Self-RAG: reflection 토큰으로 검색 필요성 판단",
                "level": "심화", "duration": "10분",
                "concepts": ["Self-RAG", "Adaptive Retrieval", "FLARE", "Reflection Token", "Critique Token"],
                "search_hints": {
                    "arxiv_query": "Self-RAG learning retrieve generate critique self-reflection Asai 2023",
                    "web_query": "Self-RAG adaptive retrieval FLARE iterative retrieval 2024"
                }
            },
            {
                "id": "rag-9",
                "title": "Graph RAG — 관계 기반 글로벌 검색",
                "description": "지식 그래프로 단순 유사도 검색이 놓치는 전역적 맥락을 추론하는 Microsoft GraphRAG",
                "level": "심화", "duration": "11분",
                "concepts": ["GraphRAG", "Knowledge Graph", "Entity Extraction", "Community Detection", "Global vs Local Query"],
                "search_hints": {
                    "arxiv_query": "Graph RAG knowledge graph query-focused summarization Microsoft Edge 2024",
                    "web_query": "Microsoft GraphRAG global local query knowledge graph vs vector RAG 2024"
                }
            },
            {
                "id": "rag-10",
                "title": "RAG 평가 — RAGAS로 환각·관련성 정량화",
                "description": "Faithfulness, Answer Relevance, Context Precision을 LLM-as-a-judge로 자동 측정",
                "level": "심화", "duration": "10분",
                "concepts": ["RAGAS", "Faithfulness", "Answer Relevance", "Context Precision", "LLM-as-a-judge", "TruLens"],
                "search_hints": {
                    "arxiv_query": "RAGAS retrieval augmented generation assessment evaluation framework 2023 2024",
                    "web_query": "RAGAS RAG evaluation faithfulness answer relevance context precision 2024"
                }
            },
        ],
    },
    "agent": {
        "title": "Agentic AI",
        "emoji": "🤖",
        "color": "#8B5CF6",
        "description": "스스로 계획하고, 도구를 쓰고, 협력하는 AI 에이전트 설계",
        "topic_names": ["Agentic AI", "AI Agent", "에이전트"],
        "kdc_class": "004",
        "collection_strategy": {
            "use_arxiv": True,
            "include_domains": ["arxiv.org", "anthropic.com", "openai.com", "huggingface.co", "langchain.com"],
            "rss_sources": [
                {"url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace"},
                {"url": "https://tldr.tech/ai/rss", "name": "TLDR AI"},
            ],
        },
        "chapters": [
            {
                "id": "agent-1",
                "title": "Agent란 무엇인가? — ReAct와 Plan-and-Execute의 차이",
                "description": "에이전트와 단순 챗봇의 구조적 차이를 이해하고 ReAct 루프가 어떻게 도구 호출과 추론을 결합하는지 설명할 수 있다",
                "level": "입문", "duration": "7분",
                "concepts": ["ReAct", "Plan-and-Execute", "Tool Use", "Observation-Action Loop", "Scratchpad"],
                "search_hints": {
                    "arxiv_query": "ReAct reasoning acting language model agent Yao 2022",
                    "web_query": "ReAct agent framework vs plan-and-execute LLM agent 2024"
                }
            },
            {
                "id": "agent-2",
                "title": "Function Calling의 내부 — Tool Spec 설계가 성능을 결정한다",
                "description": "Tool description 품질이 에이전트 정확도에 미치는 영향, JSON Schema 설계 원칙",
                "level": "기본", "duration": "8분",
                "concepts": ["Function Calling", "Tool Schema", "JSON Schema", "Tool Description Quality", "Parallel Tool Use"],
                "search_hints": {
                    "arxiv_query": "LLM function calling tool use API specification quality 2024",
                    "web_query": "LLM function calling tool schema design best practices parallel tool use"
                }
            },
            {
                "id": "agent-3",
                "title": "Agent 메모리 아키텍처 — 단기·장기·에피소딕 메모리",
                "description": "In-context·External·Episodic Memory의 차이를 이해하고 에이전트 목적에 맞는 메모리 구조를 선택할 수 있다",
                "level": "기본", "duration": "9분",
                "concepts": ["In-context Memory", "External Memory", "MemGPT", "Episodic Memory", "Memory Consolidation"],
                "search_hints": {
                    "arxiv_query": "MemGPT LLM long-term memory operating system agents 2023 2024",
                    "web_query": "LLM agent memory architecture short-term long-term episodic MemGPT 2024"
                }
            },
            {
                "id": "agent-4",
                "title": "Tree of Thought — AI가 여러 경로를 탐색하는 방법",
                "description": "ToT가 CoT와 어떻게 다른지 이해하고 복잡한 추론 태스크에 탐색 전략을 선택할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["Tree of Thought", "Chain of Thought", "MCTS", "BFS/DFS on Thought", "Self-Evaluation"],
                "search_hints": {
                    "arxiv_query": "Tree of Thoughts deliberate problem solving language model Yao 2023",
                    "web_query": "Tree of Thought vs Chain of Thought LLM reasoning planning 2024"
                }
            },
            {
                "id": "agent-5",
                "title": "Multi-Agent 시스템 — Supervisor 패턴과 Swarm",
                "description": "Supervisor vs Swarm 패턴의 트레이드오프를 이해하고 태스크 유형에 맞는 오케스트레이션 구조를 선택할 수 있다",
                "level": "중급", "duration": "10분",
                "concepts": ["Supervisor Pattern", "Swarm", "Handoff", "AutoGen", "LangGraph", "Agent Specialization"],
                "search_hints": {
                    "arxiv_query": "multi-agent system LLM collaboration AutoGen orchestration 2024",
                    "web_query": "multi-agent LLM supervisor swarm pattern AutoGen LangGraph 2024"
                }
            },
            {
                "id": "agent-6",
                "title": "Computer Use — AI가 마우스·키보드를 직접 조작한다면",
                "description": "Anthropic Computer Use, Browser Use — GUI 조작 에이전트의 구조와 한계",
                "level": "심화", "duration": "9분",
                "concepts": ["Computer Use", "Browser Use", "Vision-Language Agent", "GUI Grounding", "Screen Parsing"],
                "search_hints": {
                    "arxiv_query": "GUI agent computer use vision language model screen grounding 2024",
                    "web_query": "Anthropic computer use browser automation GUI agent 2024"
                }
            },
            {
                "id": "agent-7",
                "title": "Code Agent — 코드 작성부터 자동 디버깅까지",
                "description": "SWE-bench로 측정하는 코드 에이전트 성능, 샌드박스 실행과 피드백 루프",
                "level": "심화", "duration": "10분",
                "concepts": ["Code Agent", "SWE-bench", "Sandbox Execution", "Devin", "OpenHands", "Test-driven Agent"],
                "search_hints": {
                    "arxiv_query": "code agent SWE-bench software engineering LLM autonomous debugging 2024",
                    "web_query": "SWE-bench code agent Devin OpenHands software engineering AI 2024"
                }
            },
            {
                "id": "agent-8",
                "title": "에이전트 평가와 가드레일 — 어떻게 믿고 배포할까?",
                "description": "Prompt Injection 방어, Tool 권한 최소화, 에이전트 신뢰도 평가 방법",
                "level": "심화", "duration": "10분",
                "concepts": ["Prompt Injection", "Guardrails", "Tool Permission", "AgentBench", "Red-teaming", "Sandboxing"],
                "search_hints": {
                    "arxiv_query": "LLM agent safety prompt injection guardrails evaluation benchmark 2024",
                    "web_query": "AI agent security prompt injection guardrails deployment safety 2024"
                }
            },
            {
                "id": "agent-9",
                "title": "MCP (Model Context Protocol) — 에이전트 도구 표준화",
                "description": "MCP 아키텍처를 이해하고 직접 MCP 서버를 설계할 때 어떤 구조를 선택할지 판단할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["MCP", "Model Context Protocol", "MCP Server", "Tool Discovery", "FastMCP"],
                "search_hints": {
                    "arxiv_query": "model context protocol MCP tool use standardization agent 2024",
                    "web_query": "Anthropic MCP model context protocol agent tool server 2024"
                }
            },
            {
                "id": "agent-10",
                "title": "Long-horizon Task — 프로덕션 에이전트가 실패하는 이유",
                "description": "복잡한 멀티스텝 태스크에서 에이전트가 실패하는 패턴과 해결 전략",
                "level": "심화", "duration": "10분",
                "concepts": ["Long-horizon Task", "Error Propagation", "Recovery Strategy", "Checkpointing", "Human-in-the-loop"],
                "search_hints": {
                    "arxiv_query": "long-horizon planning LLM agent failure mode recovery human loop 2024",
                    "web_query": "production LLM agent failure long-horizon task reliability 2024"
                }
            },
        ],
    },
    "llm": {
        "title": "LLM 이론과 실제",
        "emoji": "🧠",
        "color": "#F59E0B",
        "description": "Transformer 구조부터 RLHF·추론 최적화까지 — 대형 언어 모델의 모든 것",
        "topic_names": ["LLM 기초", "LLM", "Large Language Model", "언어 모델"],
        "kdc_class": "004",
        "collection_strategy": {
            "use_arxiv": True,
            "include_domains": ["arxiv.org", "openai.com", "anthropic.com", "huggingface.co", "ai.google"],
            "rss_sources": [
                {"url": "https://huggingface.co/blog/feed.xml", "name": "HuggingFace"},
                {"url": "https://tldr.tech/ai/rss", "name": "TLDR AI"},
            ],
        },
        "chapters": [
            {
                "id": "llm-1",
                "title": "Attention은 왜 강력한가? — Self-Attention 수식 뜯어보기",
                "description": "Self-Attention의 Q·K·V 연산 흐름을 이해하고 Transformer가 시퀀스의 어느 부분에 주목하는지 설명할 수 있다",
                "level": "입문", "duration": "10분",
                "concepts": ["Self-Attention", "Q/K/V Matrix", "Multi-head Attention", "Positional Encoding", "Softmax"],
                "search_hints": {
                    "arxiv_query": "attention is all you need transformer Vaswani 2017 self-attention mechanism",
                    "web_query": "transformer self-attention Q K V matrix explained visually 2024"
                }
            },
            {
                "id": "llm-2",
                "title": "GPT의 사전훈련 — Next Token Prediction이 왜 이렇게 강력할까?",
                "description": "Autoregressive 언어 모델의 훈련 목표, Emergent Ability, Scaling Law",
                "level": "기본", "duration": "9분",
                "concepts": ["Autoregressive LM", "Next Token Prediction", "Scaling Law", "Emergent Ability", "Perplexity"],
                "search_hints": {
                    "arxiv_query": "scaling laws neural language models Kaplan 2020 emergent abilities GPT",
                    "web_query": "GPT pretraining next token prediction scaling laws emergent abilities explained"
                }
            },
            {
                "id": "llm-3",
                "title": "RLHF — AI를 사람 의도에 맞게 정렬하는 방법",
                "description": "SFT → Reward Model → PPO 파이프라인, Constitutional AI, DPO 비교",
                "level": "기본", "duration": "10분",
                "concepts": ["RLHF", "SFT", "Reward Model", "PPO", "DPO", "Constitutional AI"],
                "search_hints": {
                    "arxiv_query": "RLHF reinforcement learning human feedback InstructGPT DPO alignment 2023 2024",
                    "web_query": "RLHF DPO alignment LLM instruction following comparison 2024"
                }
            },
            {
                "id": "llm-4",
                "title": "프롬프트 엔지니어링의 과학 — CoT·Few-shot·Self-Consistency",
                "description": "Chain-of-Thought가 왜 작동하는지, 그 한계와 더 나은 기법들",
                "level": "기본", "duration": "8분",
                "concepts": ["Chain-of-Thought", "Few-shot Prompting", "Self-Consistency", "Step-back Prompting", "Prompt Sensitivity"],
                "search_hints": {
                    "arxiv_query": "chain of thought prompting reasoning language model Wei 2022 self-consistency",
                    "web_query": "chain of thought prompting CoT few-shot self-consistency prompt engineering 2024"
                }
            },
            {
                "id": "llm-5",
                "title": "Fine-tuning의 현실 — LoRA·QLoRA로 모델 커스터마이징",
                "description": "Full fine-tuning vs LoRA의 차이를 이해하고 RAG와 fine-tuning 중 언제 무엇을 선택할지 판단할 수 있다",
                "level": "중급", "duration": "11분",
                "concepts": ["Fine-tuning", "LoRA", "QLoRA", "PEFT", "Adapter", "Catastrophic Forgetting"],
                "search_hints": {
                    "arxiv_query": "LoRA low-rank adaptation large language model fine-tuning Hu 2021 QLoRA",
                    "web_query": "LoRA QLoRA fine-tuning vs RAG when to use LLM customization 2024"
                }
            },
            {
                "id": "llm-6",
                "title": "양자화와 추론 최적화 — 어떻게 더 빠르고 싸게 쓸까?",
                "description": "INT4/INT8 양자화와 KV Cache의 원리를 이해하고 추론 비용·속도·품질 트레이드오프를 상황에 맞게 선택할 수 있다",
                "level": "중급", "duration": "10분",
                "concepts": ["Quantization", "INT4/INT8", "KV Cache", "Speculative Decoding", "vLLM", "PagedAttention"],
                "search_hints": {
                    "arxiv_query": "LLM inference optimization speculative decoding vLLM paged attention quantization 2024",
                    "web_query": "LLM inference optimization vLLM speculative decoding quantization INT4 2024"
                }
            },
            {
                "id": "llm-7",
                "title": "Long Context의 함정 — 컨텍스트가 길면 정말 더 잘할까?",
                "description": "Position Encoding의 한계와 Lost-in-the-Middle 현상을 이해하고 긴 컨텍스트를 신뢰할 수 있는 조건을 판단할 수 있다",
                "level": "중급", "duration": "9분",
                "concepts": ["RoPE", "ALiBi", "Needle-in-a-Haystack", "Lost-in-the-Middle", "Context Window Scaling"],
                "search_hints": {
                    "arxiv_query": "long context LLM position encoding RoPE ALiBi needle haystack evaluation 2024",
                    "web_query": "long context LLM limitations needle in haystack benchmark position encoding 2024"
                }
            },
            {
                "id": "llm-8",
                "title": "멀티모달 LLM — 이미지·오디오·영상을 어떻게 이해할까?",
                "description": "Vision Encoder + LLM 결합 구조, Flamingo·LLaVA·GPT-4o 비교",
                "level": "심화", "duration": "10분",
                "concepts": ["Vision Encoder", "Cross-Attention", "LLaVA", "Flamingo", "GPT-4o", "Visual Grounding"],
                "search_hints": {
                    "arxiv_query": "multimodal large language model LLaVA vision encoder cross attention 2024",
                    "web_query": "multimodal LLM GPT-4o LLaVA vision language model architecture 2024"
                }
            },
            {
                "id": "llm-9",
                "title": "오픈소스 LLM 생태계 — Llama·Mistral·Qwen 비교",
                "description": "각 오픈소스 모델의 아키텍처 차별점, Instruction Tuning 방법론, 로컬 실행 전략",
                "level": "심화", "duration": "9분",
                "concepts": ["Llama 3", "Mistral", "Qwen", "GQA", "Sliding Window Attention", "Ollama"],
                "search_hints": {
                    "arxiv_query": "Llama 3 Mistral open source LLM grouped query attention architecture 2024",
                    "web_query": "open source LLM comparison Llama Mistral Qwen local deployment 2024"
                }
            },
            {
                "id": "llm-10",
                "title": "LLM 벤치마크의 진실 — MMLU가 측정하지 못하는 것",
                "description": "MMLU·HumanEval·LMSYS Arena 설계 철학, Data Contamination 문제, 평가의 한계",
                "level": "심화", "duration": "10분",
                "concepts": ["MMLU", "HumanEval", "LMSYS Chatbot Arena", "Data Contamination", "LLM-as-a-judge"],
                "search_hints": {
                    "arxiv_query": "LLM evaluation benchmark contamination MMLU HumanEval chatbot arena 2024",
                    "web_query": "LLM benchmark evaluation problems data contamination MMLU limitations 2024"
                }
            },
        ],
    },
    "invest": {
        "title": "주식/투자",
        "emoji": "📈",
        "color": "#EF4444",
        "description": "재무제표부터 매크로 경제까지 — 돈이 일하게 만드는 투자의 원리",
        "topic_names": ["주식/투자", "주식", "투자", "재테크"],
        "kdc_class": "320",
        "collection_strategy": {
            "use_arxiv": False,
            "include_domains": ["investopedia.com", "bloomberg.com", "ft.com", "morningstar.com", "wsj.com", "fool.com"],
            "rss_sources": [
                {"url": "https://feeds.feedburner.com/typepad/krMN", "name": "Freakonomics"},
                {"url": "https://www.economist.com/finance-and-economics/rss.xml", "name": "Economist"},
            ],
        },
        "chapters": [
            {
                "id": "invest-1",
                "title": "주식이란 무엇인가? — 회사 조각을 사는 행위의 의미",
                "description": "소유권·의결권·배당권의 구조, 시가총액과 기업 가치의 관계",
                "level": "입문", "duration": "6분",
                "concepts": ["보통주", "우선주", "시가총액", "주주권", "IPO"],
                "search_hints": {
                    "arxiv_query": None,
                    "web_query": "what is stock market equity ownership IPO explained beginners"
                }
            },
            {
                "id": "invest-2",
                "title": "재무제표 읽기 — PER·PBR·ROE로 기업 가치 판단하기",
                "description": "손익계산서·대차대조표·현금흐름표의 핵심 지표와 해석법",
                "level": "기본", "duration": "9분",
                "concepts": ["PER", "PBR", "ROE", "영업이익률", "FCF (잉여현금흐름)", "EV/EBITDA"],
                "search_hints": {
                    "arxiv_query": "financial statement analysis equity valuation PER PBR ROE fundamental",
                    "web_query": "how to read financial statements PER PBR ROE EV EBITDA stock analysis"
                }
            },
            {
                "id": "invest-3",
                "title": "가치 투자의 철학 — 내재 가치와 안전 마진",
                "description": "워렌 버핏·찰리 멍거의 사고법, 미스터 마켓, 안전 마진 계산",
                "level": "기본", "duration": "8분",
                "concepts": ["내재 가치", "안전 마진", "미스터 마켓", "DCF 할인현금흐름", "경제적 해자"],
                "search_hints": {
                    "arxiv_query": "value investing intrinsic value DCF discount cash flow margin of safety",
                    "web_query": "Warren Buffett value investing intrinsic value moat margin of safety explained"
                }
            },
            {
                "id": "invest-4",
                "title": "ETF와 인덱스 투자 — 왜 대부분의 펀드매니저를 이기나",
                "description": "패시브 투자의 승리 이유, ETF 구조, 섹터·국가·팩터 ETF 활용법",
                "level": "기본", "duration": "8분",
                "concepts": ["ETF", "인덱스 펀드", "패시브 투자", "팩터 투자", "스마트 베타", "비용률"],
                "search_hints": {
                    "arxiv_query": "passive investing ETF index fund vs active management factor investing",
                    "web_query": "ETF index investing vs active fund management factor smart beta explained"
                }
            },
            {
                "id": "invest-5",
                "title": "기술적 분석의 현실 — 이동평균·RSI·MACD가 실제로 작동하나?",
                "description": "차트 지표의 수학적 원리, 지표가 예측력을 가지는 조건과 한계",
                "level": "기본", "duration": "9분",
                "concepts": ["이동평균선", "RSI", "MACD", "볼린저 밴드", "지지/저항", "역추세·추세추종"],
                "search_hints": {
                    "arxiv_query": "technical analysis moving average RSI MACD predictive power stock market",
                    "web_query": "technical analysis indicators RSI MACD does it work evidence 2024"
                }
            },
            {
                "id": "invest-6",
                "title": "채권과 금리 — 금리가 오르면 왜 주식이 떨어질까?",
                "description": "채권 가격-금리 역관계, 수익률 곡선, 통화정책과 주식시장의 연결고리",
                "level": "기본", "duration": "8분",
                "concepts": ["채권 가격", "금리 역관계", "수익률 곡선", "장단기 스프레드", "연준 금리"],
                "search_hints": {
                    "arxiv_query": "interest rate bond price inverse relationship yield curve monetary policy",
                    "web_query": "why rising interest rates hurt stocks bonds yield curve explained"
                }
            },
            {
                "id": "invest-7",
                "title": "행동경제학과 투자 심리 — 손실 회피가 수익을 갉아먹는 방법",
                "description": "전망 이론, 군중 심리, FOMO·공황 매도 패턴과 극복 전략",
                "level": "심화", "duration": "9분",
                "concepts": ["손실 회피", "전망 이론", "군중 심리", "FOMO", "Disposition Effect", "앵커링"],
                "search_hints": {
                    "arxiv_query": "behavioral finance prospect theory loss aversion investor psychology disposition effect",
                    "web_query": "behavioral finance investing psychology loss aversion FOMO market panic"
                }
            },
            {
                "id": "invest-8",
                "title": "포트폴리오 이론 — 분산 투자가 공짜 점심인 이유",
                "description": "마코위츠의 효율적 프론티어, 상관관계·변동성·샤프 비율의 의미",
                "level": "심화", "duration": "10분",
                "concepts": ["효율적 프론티어", "샤프 비율", "상관계수", "분산 투자", "리밸런싱"],
                "search_hints": {
                    "arxiv_query": "modern portfolio theory Markowitz efficient frontier sharpe ratio diversification",
                    "web_query": "Markowitz portfolio theory efficient frontier sharpe ratio diversification explained"
                }
            },
            {
                "id": "invest-9",
                "title": "매크로 투자 — 경제 사이클로 큰 그림 읽기",
                "description": "레이 달리오의 부채 사이클, 올웨더 포트폴리오, 인플레이션·디플레이션 대응 자산",
                "level": "심화", "duration": "10분",
                "concepts": ["경제 사이클", "부채 사이클", "올웨더 포트폴리오", "인플레이션 헤지", "실질 금리"],
                "search_hints": {
                    "arxiv_query": "macroeconomic cycle debt cycle inflation asset allocation Ray Dalio",
                    "web_query": "Ray Dalio all weather portfolio debt cycle macro investing inflation hedge"
                }
            },
            {
                "id": "invest-10",
                "title": "세금과 절세 전략 — 수익만큼 중요한 세후 수익률",
                "description": "양도소득세·배당소득세·금융투자소득세, ISA·연금저축 계좌 활용 전략",
                "level": "심화", "duration": "9분",
                "concepts": ["양도소득세", "금융투자소득세", "ISA 계좌", "연금저축", "세후 수익률"],
                "search_hints": {
                    "arxiv_query": None,
                    "web_query": "Korea stock tax capital gains ISA pension account tax optimization 2024"
                }
            },
        ],
    },
    "psych": {
        "title": "심리학",
        "emoji": "🧬",
        "color": "#EC4899",
        "description": "인간의 마음과 행동을 과학으로 이해하기 — 인지 편향부터 뇌과학까지",
        "kdc_class": "150",
        "topic_names": ["심리학", "Psychology"],
        "collection_strategy": {
            "use_arxiv": True,
            "include_domains": ["psychologytoday.com", "apa.org", "simplypsychology.org", "verywellmind.com", "frontiersin.org"],
            "rss_sources": [
                {"url": "https://www.psychologytoday.com/intl/front-page/feed", "name": "Psychology Today"},
                {"url": "https://www.apa.org/rss/news", "name": "APA"},
            ],
        },
        "chapters": [
            {
                "id": "psych-1",
                "title": "인지 편향 — 우리 뇌가 체계적으로 틀리는 방식",
                "description": "확증 편향·가용성 편향·앵커링이 판단과 의사결정을 왜곡하는 메커니즘",
                "level": "입문", "duration": "7분",
                "concepts": ["확증 편향", "가용성 편향", "앵커링 효과", "대표성 어림법", "인지적 구두쇠"],
                "search_hints": {
                    "arxiv_query": "cognitive bias confirmation availability anchoring heuristic decision making Kahneman",
                    "web_query": "cognitive biases confirmation availability anchoring how they work psychology"
                }
            },
            {
                "id": "psych-2",
                "title": "행동경제학 — 왜 인간은 '합리적'이지 않은가",
                "description": "Kahneman의 시스템 1·2, 전망 이론, 넛지 설계의 원리",
                "level": "기본", "duration": "9분",
                "concepts": ["시스템 1/2", "전망 이론", "넛지", "기본값 효과", "현상 유지 편향"],
                "search_hints": {
                    "arxiv_query": "behavioral economics prospect theory nudge system 1 2 Kahneman Thaler",
                    "web_query": "behavioral economics prospect theory nudge theory system 1 2 thinking fast slow"
                }
            },
            {
                "id": "psych-3",
                "title": "Big Five 성격 모델 — MBTI를 넘어선 과학적 성격 이론",
                "description": "OCEAN 모델의 측정 타당성, 성격이 행동·건강·직업 성과를 예측하는 방식",
                "level": "기본", "duration": "8분",
                "concepts": ["Big Five", "OCEAN", "외향성", "성실성", "신경증", "성격 측정 타당도"],
                "search_hints": {
                    "arxiv_query": "Big Five personality traits OCEAN model validity prediction behavior outcomes",
                    "web_query": "Big Five personality OCEAN vs MBTI scientific validity prediction career health"
                }
            },
            {
                "id": "psych-4",
                "title": "사회 심리학 — 왜 좋은 사람도 나쁜 행동을 할까?",
                "description": "밀그램 복종 실험, 방관자 효과, 집단 사고의 현실적 위험",
                "level": "기본", "duration": "9분",
                "concepts": ["복종 실험", "방관자 효과", "집단 사고", "사회적 촉진", "역할 효과"],
                "search_hints": {
                    "arxiv_query": "social psychology obedience Milgram bystander effect groupthink conformity",
                    "web_query": "Milgram obedience experiment bystander effect groupthink social psychology explained"
                }
            },
            {
                "id": "psych-5",
                "title": "애착 이론 — 유아기 경험이 성인 관계를 결정하는가?",
                "description": "Ainsworth의 4가지 애착 유형, 성인 애착과 연애·직장 관계의 연결",
                "level": "기본", "duration": "8분",
                "concepts": ["안정 애착", "불안-양가 애착", "회피 애착", "무질서 애착", "성인 애착 모델"],
                "search_hints": {
                    "arxiv_query": "attachment theory Ainsworth adult attachment relationship outcomes Bowlby",
                    "web_query": "attachment theory adult relationships secure anxious avoidant explained"
                }
            },
            {
                "id": "psych-6",
                "title": "긍정 심리학 — 행복은 만들 수 있는가?",
                "description": "Seligman의 PERMA 모델, Flow 경험, 감사 일기·강점 사용의 효과 크기",
                "level": "심화", "duration": "8분",
                "concepts": ["PERMA", "Flow", "강점 기반 접근", "감사 실천", "Well-being 측정"],
                "search_hints": {
                    "arxiv_query": "positive psychology PERMA wellbeing flow Csikszentmihalyi Seligman happiness",
                    "web_query": "positive psychology PERMA model flow happiness science Seligman evidence"
                }
            },
            {
                "id": "psych-7",
                "title": "신경과학과 의사결정 — 뇌는 어떻게 선택하는가?",
                "description": "전전두엽·편도체·도파민 회로가 위험 판단과 보상 추구에 미치는 영향",
                "level": "심화", "duration": "9분",
                "concepts": ["전전두엽", "편도체", "도파민 회로", "보상 예측 오차", "감정과 이성"],
                "search_hints": {
                    "arxiv_query": "neuroscience decision making prefrontal cortex amygdala dopamine reward prediction error",
                    "web_query": "neuroscience decision making prefrontal cortex dopamine reward risk assessment"
                }
            },
            {
                "id": "psych-8",
                "title": "트라우마와 회복탄력성 — 역경이 사람을 강하게 만드는 조건",
                "description": "PTSD 메커니즘, 외상 후 성장(PTG), 회복탄력성을 높이는 심리적 요인",
                "level": "심화", "duration": "9분",
                "concepts": ["PTSD", "외상 후 성장 (PTG)", "회복탄력성", "자기 효능감", "사회적 지지"],
                "search_hints": {
                    "arxiv_query": "trauma PTSD post traumatic growth resilience psychological recovery mechanisms",
                    "web_query": "post traumatic growth PTSD resilience recovery psychology research"
                }
            },
            {
                "id": "psych-9",
                "title": "자기결정이론 — 내적 동기를 키우고 번아웃을 막는 방법",
                "description": "Deci & Ryan의 SDT: 자율성·유능감·관계성의 심리 욕구와 직장 동기",
                "level": "심화", "duration": "9분",
                "concepts": ["자기결정이론 (SDT)", "내적 동기", "외적 동기", "자율성", "유능감", "번아웃"],
                "search_hints": {
                    "arxiv_query": "self determination theory intrinsic motivation autonomy competence relatedness Deci Ryan",
                    "web_query": "self determination theory intrinsic motivation burnout workplace SDT Deci Ryan"
                }
            },
            {
                "id": "psych-10",
                "title": "설득과 영향력 — 사람들은 어떻게 의견을 바꾸는가?",
                "description": "Cialdini의 6가지 영향력 원칙, 인지 부조화, 태도 변화의 정교화 가능성 모델",
                "level": "심화", "duration": "10분",
                "concepts": ["Cialdini 영향력 원칙", "사회적 증거", "희소성", "인지 부조화", "정교화 가능성 모델"],
                "search_hints": {
                    "arxiv_query": "persuasion influence social proof Cialdini cognitive dissonance attitude change ELM",
                    "web_query": "Cialdini influence principles persuasion cognitive dissonance attitude change psychology"
                }
            },
        ],
    },
}

# chapter.py 하위 호환용 — CHAPTERS 형식으로 변환
CHAPTERS = {
    track_id: {
        "title": track["title"],
        "chapters": track["chapters"],
    }
    for track_id, track in CURRICULUM_CATALOG.items()
}
