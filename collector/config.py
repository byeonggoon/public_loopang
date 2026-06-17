"""환경변수 및 수집 설정."""
import os

from dotenv import load_dotenv

load_dotenv()

# --- API 키 ---
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
DATA_GO_KR_KEY = os.getenv("DATA_GO_KR_KEY", "")

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# --- 뉴스 검색 키워드 ---
# 외유성 국외출장/해외연수 논란을 폭넓게 포착하기 위한 키워드 묶음.
NEWS_KEYWORDS = [
    "지방의원 해외연수",
    "외유성 출장",
    "공무국외출장 논란",
    "공무원 해외연수 논란",
    "지방의회 외유",
    "혈세 해외연수",
    "관광성 출장",
]

# 키워드당 가져올 뉴스 개수 (네이버 API: 호출당 최대 100).
NEWS_DISPLAY = 100

# BTIS 제목 검색 키워드 — 최신 덤프 대신 관심 주제를 직접 검색해 범위를 넓힌다.
# (BTIS 기본검색은 기관 필터가 없어 제목 검색으로 외유 의심 보고서를 포착)
BTIS_TITLE_KEYWORDS = [
    "선거관리", "선관위",
    "지방의회", "시의회", "도의회", "군의회", "구의회",
    "해외연수", "국외연수", "연수",
    "시찰", "견학", "벤치마킹",
    "우호교류", "자매결연", "방문단",
]

# 광역 시·도 목록 (지역 추출용).
REGIONS = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]

# 외유 의심 / 분류 태그 규칙 (키워드 -> 태그).
TAG_RULES = {
    "외유의심": ["외유", "관광", "유흥", "사적", "물놀이", "쇼핑"],
    "예산초과": ["예산 초과", "혈세", "과다", "고가", "비싼", "낭비"],
    "부실보고": ["부실", "표절", "베끼기", "복사", "허위", "짜깁기"],
}
