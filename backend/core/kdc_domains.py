"""
KDC (한국십진분류법) 중분류 기반 수집 전략
신규 토픽 커리큘럼 생성 시 kdc_class를 분류받고,
수집 시 해당 분류의 신뢰 도메인을 include_domains로 사용한다.

catalog에 있는 알려진 토픽은 per-topic include_domains 우선 사용.
catalog에 없는 신규 토픽은 이 테이블로 fallback.
"""

KDC_MIDDLE_DOMAINS: dict[str, dict] = {
    # ── 000 총류 ──────────────────────────────────────────────
    "004": {
        "label": "컴퓨터·AI·소프트웨어",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "acm.org", "ieee.org",
            "huggingface.co", "openai.com", "anthropic.com",
            "deepmind.google", "research.google",
        ],
    },

    # ── 100 철학·심리학 ───────────────────────────────────────
    "110": {
        "label": "철학",
        "use_arxiv": False,
        "domains": [
            "plato.stanford.edu", "iep.utm.edu",
            "britannica.com", "philosophybites.com",
            "philosophersmag.com",
        ],
    },
    "150": {
        "label": "심리학",
        "use_arxiv": True,
        "domains": [
            "psychologytoday.com", "apa.org",
            "simplypsychology.org", "verywellmind.com",
            "frontiersin.org", "pubmed.ncbi.nlm.nih.gov",
        ],
    },

    # ── 300 사회과학 ──────────────────────────────────────────
    "320": {
        "label": "경제학·투자·경영",
        "use_arxiv": True,
        "domains": [
            "nber.org", "ssrn.com", "hbr.org",
            "investopedia.com", "bloomberg.com",
            "economist.com", "ft.com", "wsj.com",
        ],
    },
    "330": {
        "label": "사회학·사회문제",
        "use_arxiv": True,
        "domains": [
            "pewresearch.org", "brookings.edu", "ssrn.com",
            "theguardian.com", "theatlantic.com",
        ],
    },
    "340": {
        "label": "정치학·국제관계",
        "use_arxiv": False,
        "domains": [
            "brookings.edu", "foreignaffairs.com", "cfr.org",
            "pewresearch.org", "carnegieendowment.org",
        ],
    },
    "360": {
        "label": "법학",
        "use_arxiv": False,
        "domains": [
            "law.cornell.edu", "ssrn.com",
            "law.harvard.edu", "findlaw.com", "scotusblog.com",
        ],
    },
    "370": {
        "label": "교육학·학습과학",
        "use_arxiv": True,
        "domains": [
            "edutopia.org", "khanacademy.org",
            "ted.com", "edsurge.com", "learningscientists.org",
        ],
    },

    # ── 400 순수과학 ──────────────────────────────────────────
    "410": {
        "label": "수학",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "mathworld.wolfram.com",
            "quantamagazine.org", "ams.org",
            "math.stackexchange.com",
        ],
    },
    "420": {
        "label": "물리학",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "physics.aps.org",
            "quantamagazine.org", "nature.com",
            "scientificamerican.com",
        ],
    },
    "430": {
        "label": "화학",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "chemrxiv.org", "acs.org",
            "nature.com", "rsc.org",
        ],
    },
    "460": {
        "label": "생명과학·생물학",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "biorxiv.org", "nature.com",
            "science.org", "ncbi.nlm.nih.gov",
            "quantamagazine.org",
        ],
    },

    # ── 500 기술과학 ──────────────────────────────────────────
    "510": {
        "label": "의학·건강",
        "use_arxiv": True,
        "domains": [
            "pubmed.ncbi.nlm.nih.gov", "nih.gov",
            "mayoclinic.org", "healthline.com",
            "nejm.org", "who.int", "medscape.com",
        ],
    },
    "550": {
        "label": "기계·전기·전자공학",
        "use_arxiv": True,
        "domains": [
            "arxiv.org", "ieee.org", "spectrum.ieee.org",
            "technologyreview.com", "wired.com",
        ],
    },
    "590": {
        "label": "생활과학·요리·가정",
        "use_arxiv": False,
        "domains": [
            "seriouseats.com", "bonappetit.com",
            "kingarthurbaking.com", "thekitchn.com",
            "foodnetwork.com",
        ],
    },

    # ── 600 예술 ──────────────────────────────────────────────
    "650": {
        "label": "미술·디자인",
        "use_arxiv": False,
        "domains": [
            "artsy.net", "moma.org", "tate.org.uk",
            "theguardian.com", "smithsonianmag.com",
        ],
    },
    "670": {
        "label": "음악",
        "use_arxiv": False,
        "domains": [
            "musictheory.net", "allmusic.com",
            "pitchfork.com", "britannica.com",
            "theguardian.com",
        ],
    },
    "690": {
        "label": "스포츠·체육",
        "use_arxiv": False,
        "domains": [
            "espn.com", "olympic.org",
            "runnersworld.com", "health.com",
            "scientificamerican.com",
        ],
    },

    # ── 700 언어 ──────────────────────────────────────────────
    "710": {
        "label": "언어학",
        "use_arxiv": False,
        "domains": [
            "cambridge.org", "britannica.com",
            "linguisticsociety.org", "languagelog.ldc.upenn.edu",
        ],
    },

    # ── 800 문학 ──────────────────────────────────────────────
    "810": {
        "label": "문학",
        "use_arxiv": False,
        "domains": [
            "britannica.com", "poetryfoundation.org",
            "theguardian.com", "literarydevices.net",
            "sparknotes.com",
        ],
    },

    # ── 900 역사·지리 ─────────────────────────────────────────
    "910": {
        "label": "역사",
        "use_arxiv": False,
        "domains": [
            "history.com", "britannica.com",
            "smithsonianmag.com", "nationalgeographic.com",
            "historyhit.com",
        ],
    },
    "980": {
        "label": "지리·여행",
        "use_arxiv": False,
        "domains": [
            "nationalgeographic.com", "lonelyplanet.com",
            "britannica.com", "worldatlas.com",
        ],
    },
}


def get_kdc_strategy(kdc_class: str) -> dict:
    """
    kdc_class → {use_arxiv, domains} 반환.
    매칭 실패 시 빈 dict (호출부에서 기본값 처리).
    """
    return KDC_MIDDLE_DOMAINS.get(kdc_class, {})
