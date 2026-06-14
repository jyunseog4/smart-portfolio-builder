#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Portfolio Builder v5 — Pro Edition
==========================================
v4 대비 추가 사항:
  - 확장 종목 universe: S&P100 + NASDAQ70 + KOSPI100 + KOSDAQ50 + OMX C25 = ~345개
  - 개인 재무관리 강화: 예산, 비상금, 부채, 재무 건강도 점수
  - 🔥 숨은 가치주 발굴 (Deep Value Hunter): 저평가 + 미래 상승 가능성

실행:
  pip install -r requirements.txt
  streamlit run quant_portfolio_app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from scipy.optimize import minimize
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')


# ============================================================
# 페이지 설정 & 트레이더 다크 테마 CSS
# ============================================================
st.set_page_config(
    page_title="Smart Portfolio Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

TRADER_CSS = """
<style>
.stApp { background: #ffffff; color: #000000; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
[data-testid="stToolbar"] { display: none; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

[data-testid="stSidebar"] { background: #f6f8fa; border-right: 1px solid #d0d7de; }
[data-testid="stSidebar"] * { color: #000000 !important; }

h1, h2, h3, h4, h5 {
    font-family: 'JetBrains Mono','SF Mono','Monaco',monospace !important;
    letter-spacing: -0.3px;
    color: #000000 !important;
}
h1 { font-size: 1.8rem !important; font-weight: 700 !important; }
h2 { font-size: 1.3rem !important; font-weight: 600 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }

p, label, span, div { color: #000000; }

[data-testid="stMetric"] {
    background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
    padding: 14px 16px; transition: border-color 0.15s ease;
}
[data-testid="stMetric"]:hover { border-color: #0969da; }
[data-testid="stMetricLabel"] {
    color: #57606a !important; font-size: 0.75rem !important;
    text-transform: uppercase; letter-spacing: 0.5px;
    font-family: 'JetBrains Mono',monospace !important;
}
[data-testid="stMetricValue"] {
    color: #000000 !important;
    font-family: 'JetBrains Mono','SF Mono',monospace !important;
    font-weight: 700 !important; font-size: 1.6rem !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono',monospace !important; font-size: 0.8rem !important;
}

.stButton button {
    background: #f6f8fa; border: 1px solid #d0d7de; color: #000000;
    font-family: 'JetBrains Mono',monospace; font-weight: 500;
    border-radius: 6px; padding: 0.4rem 1.2rem; transition: all 0.15s ease;
}
.stButton button:hover { background: #eaeef2; border-color: #0969da; color: #0969da; }
.stButton button[kind="primary"] { background: #1f883d; border-color: #1a7f37; color: white !important; }
.stButton button[kind="primary"]:hover { background: #1a7f37; border-color: #116329; color: white !important; }
.stButton button[kind="primary"] * { color: white !important; }

.stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: #ffffff !important; border: 1px solid #d0d7de !important;
    color: #000000 !important; font-family: 'JetBrains Mono',monospace !important;
    border-radius: 6px !important;
}
.stTextInput input::placeholder, .stNumberInput input::placeholder {
    color: #8b949e !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #0969da !important; box-shadow: 0 0 0 3px rgba(9,105,218,0.15) !important;
}

[data-baseweb="select"] > div {
    background: #ffffff !important; border-color: #d0d7de !important;
    color: #000000 !important;
    font-family: 'JetBrains Mono',monospace !important;
}
[data-baseweb="popover"] { background: #ffffff !important; }
[data-baseweb="menu"] { background: #ffffff !important; }
[data-baseweb="menu"] li { color: #000000 !important; }

[data-testid="stExpander"] {
    background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
}
[data-testid="stExpander"] summary { color: #000000 !important; }
[data-testid="stExpander"] summary p { color: #000000 !important; }

.stDataFrame, [data-testid="stDataFrame"] {
    background: #ffffff !important;
}
.stDataFrame * {
    font-family: 'JetBrains Mono','SF Mono',monospace !important;
    color: #000000 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff; border-bottom: 1px solid #d0d7de; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #57606a; border-radius: 6px 6px 0 0;
    padding: 8px 16px; font-family: 'JetBrains Mono',monospace; font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #f6f8fa !important; color: #0969da !important;
    border: 1px solid #d0d7de !important; border-bottom: 2px solid #0969da !important;
}

[data-testid="stAlert"] {
    background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
    border-left-width: 3px;
}
[data-testid="stAlert"] * { color: #000000 !important; }

.profile-card {
    background: #f6f8fa;
    border: 1px solid #d0d7de; border-radius: 10px; padding: 24px; margin-bottom: 16px;
}
.profile-avatar {
    width: 64px; height: 64px; border-radius: 50%;
    background: linear-gradient(135deg, #0969da 0%, #0550ae 100%);
    color: white; display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem; font-weight: 700; font-family: 'JetBrains Mono',monospace;
}
.health-card {
    background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 10px;
    padding: 20px; margin: 12px 0;
}
.up { color: #1a7f37 !important; }
.down { color: #cf222e !important; }
.neutral { color: #57606a !important; }
.ticker-text { font-family: 'JetBrains Mono',monospace; color: #0969da; font-weight: 600; }

hr { border: none; border-top: 1px solid #d0d7de; margin: 1rem 0; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #ffffff; }
::-webkit-scrollbar-thumb { background: #d0d7de; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #afb8c1; }

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #0969da 0%, #54aeff 100%);
}

.stSlider [data-baseweb="slider"] [role="slider"] { background: #0969da !important; }
.stForm { background: transparent !important; }
</style>
"""


# ============================================================
# 사용자 데이터 (확장)
# ============================================================
USER_DATA_FILE = Path(__file__).parent / 'user_data.json'

DEFAULT_USER_DATA = {
    'name': '',
    'age': 30,
    'nationality': 'KR',
    'monthly_salary': 0,
    'salary_currency': 'KRW',
    'investment_amount': 0,
    'investment_currency': 'USD',
    'email': '',
    # 새로 추가된 재무 항목
    'monthly_expenses': 0,
    'emergency_fund': 0,
    'total_debt': 0,
    'debt_interest_rate': 0.0,
    'retirement_savings': 0,
    'target_retirement_age': 60,
    'dependents': 0,
    'has_insurance': False,
    'has_pension': False,
    # 재무 목표 (NEW)
    'goal_amount': 0,
    'goal_currency': 'USD',
    'goal_years': 10,
    'goal_purpose': 'house',  # house / retirement / education / marriage / car / freedom / other
    'preferred_etf_region': 'US',  # US / KR
    'selected_scenario': 'moderate',  # conservative / moderate / aggressive
    # 메타
    'created_at': None,
    'updated_at': None,
    'lang': 'ko',
    'risk_profile': 'mid',
}


def load_user_data():
    if USER_DATA_FILE.exists():
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in DEFAULT_USER_DATA.items():
                    if key not in data:
                        data[key] = value
                return data
        except Exception:
            return None
    return None


def save_user_data(data):
    now = datetime.now().isoformat()
    data['updated_at'] = now
    if not data.get('created_at'):
        data['created_at'] = now
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def delete_user_data():
    if USER_DATA_FILE.exists():
        USER_DATA_FILE.unlink()


# ============================================================
# 세금 규칙
# ============================================================
TAX_RULES = {
    'KR': {
        'name_ko': '🇰🇷 한국', 'name_en': '🇰🇷 Korea', 'name_da': '🇰🇷 Korea',
        'capital_gains_domestic': 0.0, 'capital_gains_foreign': 0.22,
        'capital_gains_deduction_krw': 2500000, 'dividend': 0.154, 'transaction': 0.0018,
        'description_ko': '국내주식: 소액주주 양도세 면제, 거래세 0.18% / 해외주식: 양도세 22% (연 250만원 공제), 배당 15.4%',
        'description_en': 'Domestic: capital gains exempt for retail, 0.18% transaction tax / Foreign: 22% capital gains (after KRW 2.5M deduction), 15.4% dividend',
        'description_da': 'Korea: indenlandsk fritaget, udenlandsk 22% kapitalgevinst',
    },
    'DK': {
        'name_ko': '🇩🇰 덴마크', 'name_en': '🇩🇰 Denmark', 'name_da': '🇩🇰 Danmark',
        'aktie_low': 0.27, 'aktie_high': 0.42, 'threshold_dkk': 61000,
        'dividend_low': 0.27, 'dividend_high': 0.42,
        'description_ko': '주식소득(Aktieindkomst): 61,000 DKK까지 27%, 초과분 42%. 배당도 동일.',
        'description_en': 'Aktieindkomst: 27% up to DKK 61,000, 42% above. Same for dividends.',
        'description_da': 'Aktieindkomst: 27% op til 61.000 DKK, 42% over.',
    },
    'US': {
        'name_ko': '🇺🇸 미국', 'name_en': '🇺🇸 USA', 'name_da': '🇺🇸 USA',
        'short_term': 0.24, 'long_term': 0.15,
        'dividend_qualified': 0.15, 'dividend_ordinary': 0.24,
        'description_ko': '단기(1년 미만): ~24% / 장기(1년 이상): 15%, 적격배당 15%',
        'description_en': 'Short-term (<1yr): ~24% / Long-term (>1yr): 15%. Qualified dividends: 15%.',
        'description_da': 'Kortvarig: 24%, Langvarig: 15%',
    },
}


def calculate_tax(gross_gain_usd, nationality, holding_years, exchange_rates):
    if gross_gain_usd <= 0:
        return gross_gain_usd, 0, 0.0
    rules = TAX_RULES.get(nationality, TAX_RULES['KR'])
    if nationality == 'KR':
        rate = rules['capital_gains_foreign']
        krw_rate = exchange_rates.get('KRW', 1300)
        deduction_usd = rules['capital_gains_deduction_krw'] / krw_rate
        taxable = max(0, gross_gain_usd - deduction_usd)
        tax = taxable * rate
    elif nationality == 'DK':
        dkk_rate = exchange_rates.get('DKK', 7)
        gain_dkk = gross_gain_usd * dkk_rate
        if gain_dkk <= rules['threshold_dkk']:
            tax_dkk = gain_dkk * rules['aktie_low']
        else:
            tax_dkk = (rules['threshold_dkk'] * rules['aktie_low']
                       + (gain_dkk - rules['threshold_dkk']) * rules['aktie_high'])
        tax = tax_dkk / dkk_rate
    elif nationality == 'US':
        tax = gross_gain_usd * (rules['long_term'] if holding_years >= 1 else rules['short_term'])
    else:
        tax = 0
    net = gross_gain_usd - tax
    effective_rate = tax / gross_gain_usd if gross_gain_usd > 0 else 0
    return net, tax, effective_rate


# ============================================================
# 다국어 (v4 + 신규)
# ============================================================
TRANSLATIONS = {
    'ko': {
        'title': 'SMART PORTFOLIO BUILDER',
        'subtitle': '데이터로 똑똑하게 — 개인 재무 + 투자 통합 관리',
        'welcome_title': '👋 시작하기',
        'welcome_desc': '먼저 본인 정보를 입력해주세요. 모든 데이터는 본인 컴퓨터에만 저장됩니다.',
        'name': '이름', 'age': '나이', 'nationality': '국적',
        'monthly_salary': '월급', 'salary_currency': '월급 통화',
        'investment_amount': '투자 가능 금액', 'investment_currency': '투자 통화',
        'email': '이메일 (선택)', 'save_profile': '💾 프로필 저장',
        'edit_profile': '✏️ 프로필 수정', 'delete_profile': '🗑️ 프로필 삭제',
        'profile_saved': '✅ 프로필이 저장되었습니다',
        'monthly_expenses': '월 지출',
        'emergency_fund': '비상금',
        'total_debt': '총 부채',
        'debt_interest_rate': '부채 이자율 (%)',
        'retirement_savings': '연금/은퇴 저축',
        'target_retirement_age': '은퇴 목표 나이',
        'dependents': '부양가족 수',
        'has_insurance': '보험 가입',
        'has_pension': '연금 가입',
        # 재무 건강도
        'financial_health': '🏥 재무 건강도',
        'health_score': '재무 건강도 점수',
        'savings_rate': '저축률',
        'emergency_coverage': '비상금 커버리지',
        'debt_to_income': '부채소득비율',
        'retirement_track': '은퇴 준비도',
        # 투자 가능 평가
        'investment_capacity': '💰 투자 여력 분석',
        # 숨은 가치주
        'tab_hidden_gems': '💎 숨은 가치주',
        'hidden_gems_title': '💎 저평가 + 미래 상승 가능성 큰 종목',
        'hidden_gems_subtitle': '전체 시장 기준 · 다중 신호 결합 알고리즘',
        'gem_score': '발굴 점수',
        # 기존
        'recommended_portfolio': '🎯 추천 포트폴리오',
        'run_analysis': '🚀 분석 시작',
        'analyzing': '분석 중...',
        'loading_macro': '📡 시장 데이터 수집 중...',
        'loading_stocks': '📊 종목 분석 중...',
        'tab_dashboard': '🏠 대시보드',
        'tab_finance': '💰 재무관리',
        'tab_overview': '📰 시장 분석',
        'tab_screening': '📊 종목 스크리닝',
        'tab_portfolio': '🎯 포트폴리오',
        'tab_outlook': '🔮 전망 & 유망종목',
        'tab_management': '📋 관리 가이드',
        'tab_glossary': '📖 용어',
        'market_select': '🌏 시장',
        'risk': '위험성향',
        'risk_low': '🛡️ 보수형', 'risk_mid': '⚖️ 중도형', 'risk_high': '🚀 공격형',
        'market_us': '🇺🇸 미국 (S&P + NASDAQ)',
        'market_kr': '🇰🇷 한국 (KOSPI + KOSDAQ)',
        'market_dk': '🇩🇰 덴마크 (OMX)',
        'market_all': '🌍 전체',
        'market_rec': '✨ 추천',
        'expected_return': '예상 수익률', 'volatility': '변동성',
        'sharpe': 'Sharpe', 'mdd': '최대낙폭',
        'years_old': '세', 'years': '년', 'months': '개월',
        # 섹션 헤더
        'section_basic_info': '기본 정보',
        'section_financial_detail': '재무 상세 (선택)',
        'financial_overview_section': '💼 재무 현황',
        'wealth_projection_section': '📈 미래 자산 예측',
        'item_analysis': '📊 항목별 분석',
        'improvement_section': '💡 개선 권장 사항',
        'budget_rule_section': '🎯 예산 분배 (50/30/20 룰)',
        # 헬프 텍스트
        'help_monthly_expenses': '월 평균 지출. 저축률 계산에 사용됩니다.',
        'help_emergency_fund': '비상금. 권장: 월 지출 × 6개월',
        'help_total_debt': '주택담보, 학자금, 신용대출 등 총 부채',
        'help_debt_rate': '평균 이자율',
        'help_retirement_savings': '국민연금, IRP, 401k 등',
        'help_target_age': '은퇴하고 싶은 나이',
        'projection_assumption': '가정: 연 8% 수익률, 매월 같은 비율 추가 적립',
        # 대시보드
        'invested_assets': '투자 자산',
        'annual_salary_label': '연봉',
        'total_debt_label': '총 부채',
        'after_10y_pretax': '10년 후 (세전)',
        'after_10y_aftertax': '10년 후 (세후',
        'after_20y': '20년 후',
        # 재무 상세 헬프
        'help_savings_rate_detail': '월급 대비 저축 비율. 20% 이상 권장.',
        'help_emergency_coverage': '비상금이 월 지출 몇 개월치인지. 6개월 권장.',
        'help_dti_detail': '월 부채 상환 / 월급. 36% 이하 권장.',
        'help_retirement_track_detail': '목표 은퇴자산의 몇 배 달성 예상. 1.0 이상이면 양호.',
        'help_investment_ratio_detail': '총 자산 중 투자 자산 비율. 30~70% 권장.',
        'investment_ratio_label': '투자 비중',
        'all_metrics_good': '✅ 모든 재무 지표가 양호한 수준입니다!',
        # 권장 사항
        'rec_savings_title': '🚨 저축률 부족',
        'rec_savings_text': '현재 저축률 {0:.1f}%. 월 지출을 줄이거나 부수입 마련 검토. 목표: 20% 이상.',
        'rec_emergency_title': '🚨 비상금 부족',
        'rec_emergency_text': '현재 비상금이 월 지출 {0:.1f}개월치. 목표: 6개월치. 갑작스러운 실직·의료비 대비 필수.',
        'rec_dti_title': '🚨 부채 부담 과다',
        'rec_dti_text': '부채소득비율 {0:.1f}%. 고금리 부채부터 우선 상환 권장. 투자 수익률보다 부채 이자율이 높으면 상환이 우선.',
        'rec_retirement_title': '⚠️ 은퇴 준비 부족',
        'rec_retirement_text': '현재 페이스로는 목표 은퇴자산의 {0:.1f}배만 달성 예상. 월 적립액 증가 또는 은퇴 나이 조정 검토.',
        'rec_invest_low_title': '💡 투자 비중 확대 고려',
        'rec_invest_low_text': '투자 자산 비중이 낮습니다. 비상금 6개월치 확보 후 점진적으로 투자 늘리기를 권장.',
        'rec_invest_high_title': '💡 투자 집중도 점검',
        'rec_invest_high_text': '투자 비중이 매우 높습니다. 비상금과 안전자산 비중을 점검해보세요.',
        # 예산
        'budget_caption': '필수 50% / 선택 30% / 저축·투자 20%',
        'budget_essentials': '필수 (50%)',
        'budget_wants': '선택 (30%)',
        'budget_savings_invest': '저축/투자 (20%)',
        'budget_category': '항목',
        'ideal_label': '권장',
        'actual_label': '실제',
        # 에러
        'error_name_required': '이름을 입력해주세요',
        # 분석 안내
        'press_analyze_hint': '👈 사이드바에서 **🚀 분석 시작** 누르시면 포트폴리오와 숨은 가치주가 표시됩니다.',
        'analysis_time_hint': '⏱️ 통합 시장 분석 ~7분',
        'settings_guide_title': '📚 설정 가이드 (클릭)',
        'clear_cache_btn': '🔄 캐시 비우기 (오류 시)',
        'cache_cleared': '✅ 캐시가 비워졌습니다. 다시 분석을 시작해주세요.',
        'analysis_error_title': '⚠️ 분석 중 오류 발생',
        'analysis_error_hint': '아래 버튼으로 캐시를 비우고 다시 시도해주세요. yfinance 서버 일시 장애일 수 있습니다.',
        'no_data_warning': '⚠️ 데이터를 가져올 수 없습니다. 잠시 후 다시 시도하거나 캐시를 비워주세요.',
        # 재무 목표 탭
        'tab_goal': '🎯 재무 목표',
        'goal_planner_title': '🎯 재무 목표 달성 플래너',
        'goal_planner_subtitle': '얼마를 언제까지 모을지 정하면 구체적인 길을 알려드립니다',
        'goal_step1': '📝 Step 1. 목표 설정',
        'goal_step2': '📊 Step 2. 진단',
        'goal_step3': '🎲 Step 3. 시나리오 비교',
        'goal_step4': '💼 Step 4. 구체적 포트폴리오',
        'goal_amount_label': '얼마를 모으고 싶으신가요?',
        'goal_years_label': '몇 년 안에 모으실 건가요?',
        'goal_purpose_label': '이 돈의 용도는?',
        'purpose_house': '🏠 집 구매',
        'purpose_retirement': '🌅 은퇴 자금',
        'purpose_education': '🎓 자녀 교육',
        'purpose_marriage': '💍 결혼 자금',
        'purpose_car': '🚗 차 구매',
        'purpose_freedom': '🦅 재정 자유 (FIRE)',
        'purpose_other': '✨ 기타',
        'save_goal_btn': '🎯 목표 저장',
        'goal_saved': '✅ 목표가 저장되었습니다',
        'no_goal_yet': '👆 위에서 목표를 입력하고 저장해주세요',
        'diag_current_pace': '현재 페이스 진단',
        'diag_current_assets': '현재 자산',
        'diag_monthly_save': '월 적립 가능액',
        'diag_simple_savings_label': '예금만 (연 3%)',
        'diag_required_return': '목표 달성 필요 수익률',
        'diag_achievable': '🎯 달성 가능',
        'diag_difficult': '⚠️ 도전적',
        'diag_impossible': '❌ 비현실적',
        'diag_solutions_header': '💡 해결책',
        'diag_increase_monthly': '월 적립액 늘리기',
        'diag_extend_years': '기간 늘리기',
        'diag_increase_return': '수익률 올리기 (위험 증가)',
        'scenario_expected': '예상 결과',
        'scenario_worst_case': '최악의 경우 (-1σ)',
        'scenario_best_case': '최선의 경우 (+1σ)',
        'scenario_gap': '목표 대비',
        'scenario_volatility': '예상 변동성',
        'scenario_mdd_warn': '과거 유사 시기 최대 낙폭',
        'recommended_for_you': '✨ 당신의 목표에 추천',
        'select_scenario': '시나리오 선택',
        'etf_region_label': 'ETF 종류',
        'etf_region_us': '🇺🇸 미국 상장 ETF (USD)',
        'etf_region_kr': '🇰🇷 한국 상장 ETF (KRW)',
        'core_satellite_ratio': 'Core / Satellite 비율',
        'core_label': '🏛️ CORE (ETF)',
        'satellite_label': '🚀 SATELLITE (개별주)',
        'monthly_buy_plan': '📅 매월 매수 계획',
        'no_stock_screening_yet': '⚠️ Satellite 종목 추천을 위해 먼저 사이드바에서 **🚀 분석 시작**을 눌러주세요',
        'goal_summary_card': '📋 목표 요약',
        'until_goal': '목표까지',
        # 경제 포럼
        'tab_econ_forum': '🌐 경제 포럼',
        'econ_forum_title': '🌐 글로벌 경제 포럼',
        'econ_forum_subtitle': '국가별 상세 경제 분석 · 주식 시황 · 미래 유망 산업',
        'econ_global': '🌐 글로벌',
        'econ_korea': '🇰🇷 한국',
        'econ_usa': '🇺🇸 미국',
        'econ_denmark': '🇩🇰 덴마크',
        'econ_section_situation': '📊 현재 경제 상황',
        'econ_section_stocks': '📈 주식 시장 분석',
        'econ_section_forecast': '🔮 예상 경제 흐름',
        'econ_section_industries': '🚀 미래 유망 산업',
        'forecast_short': '단기 (6개월)',
        'forecast_mid': '중기 (1~2년)',
        'forecast_long': '장기 (3~5년)',
        # 누락된 번역들
        'monthly_save_label': '월 적립 가능',
        'actual_buy_label': '실제 매수 금액',
        'cash_leftover': '남는 현금',
        'cash_leftover_help': '소수 주식 못 사서 남는 부분. 다음 달 매수에 합치세요.',
        'details_btn': '자세히',
        'expected_return_label': '예상 수익률',
        'core_vs_satellite_title': 'Core vs Satellite',
        'stocks_by_weight': '종목별 비중',
        'cumulative_simulation': '📈 누적 자산 시뮬레이션',
        'savings_only_achieve': '예금만 해도 목표 달성!',
        'shortage_label': '부족',
        'currency_label': '통화',
        'no_predict_disclaimer': '⚠️ 미래 예측이 아니라 데이터 관찰 기반 분석입니다. 실제는 다를 수 있습니다.',
        # 진단 추가
        'diag_note_savings_ok': '보수형(예금/채권 위주)으로도 가능',
        'diag_note_invest_needed': '투자 필요 (균형형~공격형 권장)',
        'diag_note_aggressive_needed': '공격적 투자 필요 (위험 ↑)',
        'diag_note_impossible_text': '목표 또는 기간 조정 필요',
        'diag_current_label': '현재',
        'diag_needed_label': '필요',
        'diag_current_goal': '현재 목표',
        'diag_assumed_7pct': '(연 7% 수익률 가정)',
        'diag_required_return_short': '필요 수익률',
        'diag_review_aggressive': '공격형 시나리오 검토',
        'diag_risk_warning': '(위험 감수 필요)',
        'goal_at_pretax': '/mo',
        'recommended_badge': '⭐ 추천',
        # 재무목표 달성 매니저 (사이드바)
        'goal_manager_title': '🎯 재무목표 달성 매니저',
        'goal_manager_no_goal': '👇 아래 \'재무 목표\' 탭에서 목표를 먼저 설정해주세요.',
        'my_goal_label': '📋 내 목표',
        'until_target': '목표까지',
        'required_pace': '🎯 필요 페이스',
        'required_return_label': '필요 수익률',
        'current_scenario': '현재 시나리오',
        'asset_allocation': '💼 권장 자산 배분',
        'asset_bonds': '🏦 채권',
        'asset_etf': '📊 ETF',
        'asset_stocks': '🚀 개별주',
        'asset_commodities': '🪙 원자재',
        'advanced_section': '🔬 고급 분석 (선택)',
        'advanced_section_desc': '전체 시장 멀티팩터 분석 + 숨은 가치주 발굴',
        'change_etf_region': 'ETF 종류 변경',
        'change_scenario': '시나리오 변경',
        'physical_gold_note': '💡 실물 금/은은 KRX 골드시장 또는 시중은행에서 구매',
        'see_portfolio_tab_hint': '👉 포트폴리오 탭에서 매수 수량 / 💎 숨은 가치주 탭에서 저평가 종목 확인',
    },
    'en': {
        'title': 'SMART PORTFOLIO BUILDER',
        'subtitle': 'Smart investing — Personal finance + Investment in one',
        'welcome_title': '👋 Get Started',
        'welcome_desc': 'Please enter your information. All data stays on your computer.',
        'name': 'Name', 'age': 'Age', 'nationality': 'Nationality',
        'monthly_salary': 'Monthly Salary', 'salary_currency': 'Salary Currency',
        'investment_amount': 'Investment Amount', 'investment_currency': 'Currency',
        'email': 'Email (optional)', 'save_profile': '💾 Save Profile',
        'edit_profile': '✏️ Edit Profile', 'delete_profile': '🗑️ Delete',
        'profile_saved': '✅ Profile saved',
        'monthly_expenses': 'Monthly Expenses',
        'emergency_fund': 'Emergency Fund',
        'total_debt': 'Total Debt',
        'debt_interest_rate': 'Debt Interest Rate (%)',
        'retirement_savings': 'Retirement Savings',
        'target_retirement_age': 'Target Retirement Age',
        'dependents': 'Dependents',
        'has_insurance': 'Has Insurance',
        'has_pension': 'Has Pension',
        'financial_health': '🏥 Financial Health',
        'health_score': 'Health Score',
        'savings_rate': 'Savings Rate',
        'emergency_coverage': 'Emergency Coverage',
        'debt_to_income': 'Debt-to-Income',
        'retirement_track': 'Retirement Track',
        'investment_capacity': '💰 Investment Capacity',
        'tab_hidden_gems': '💎 Hidden Gems',
        'hidden_gems_title': '💎 Undervalued + Future Upside Stocks',
        'hidden_gems_subtitle': 'Full market scan · Multi-signal algorithm',
        'gem_score': 'Gem Score',
        'recommended_portfolio': '🎯 Recommended Portfolio',
        'run_analysis': '🚀 Run Analysis',
        'analyzing': 'Analyzing...',
        'loading_macro': '📡 Loading market data...',
        'loading_stocks': '📊 Analyzing stocks...',
        'tab_dashboard': '🏠 Dashboard',
        'tab_finance': '💰 Finance',
        'tab_overview': '📰 Market',
        'tab_screening': '📊 Screening',
        'tab_portfolio': '🎯 Portfolio',
        'tab_outlook': '🔮 Outlook',
        'tab_management': '📋 Guide',
        'tab_glossary': '📖 Glossary',
        'market_select': '🌏 Market',
        'risk': 'Risk',
        'risk_low': '🛡️ Conservative', 'risk_mid': '⚖️ Moderate', 'risk_high': '🚀 Aggressive',
        'market_us': '🇺🇸 USA (S&P + NASDAQ)',
        'market_kr': '🇰🇷 Korea (KOSPI + KOSDAQ)',
        'market_dk': '🇩🇰 Denmark (OMX)',
        'market_all': '🌍 All',
        'market_rec': '✨ Recommended',
        'expected_return': 'Expected Return', 'volatility': 'Volatility',
        'sharpe': 'Sharpe', 'mdd': 'Max Drawdown',
        'years_old': 'yo', 'years': 'yrs', 'months': 'mo',
        # Section headers
        'section_basic_info': 'Basic Information',
        'section_financial_detail': 'Financial Details (Optional)',
        'financial_overview_section': '💼 Financial Overview',
        'wealth_projection_section': '📈 Wealth Projection',
        'item_analysis': '📊 Component Analysis',
        'improvement_section': '💡 Improvement Recommendations',
        'budget_rule_section': '🎯 Budget Allocation (50/30/20 Rule)',
        # Help texts
        'help_monthly_expenses': 'Monthly average expenses. Used for savings rate calculation.',
        'help_emergency_fund': 'Emergency fund. Recommended: 6 months of expenses',
        'help_total_debt': 'Total debt (mortgage, student loans, credit, etc.)',
        'help_debt_rate': 'Average interest rate',
        'help_retirement_savings': 'National pension, IRA, 401k, etc.',
        'help_target_age': 'Target retirement age',
        'projection_assumption': 'Assumes 8% annual return, monthly contribution at same rate',
        # Dashboard
        'invested_assets': 'Invested Assets',
        'annual_salary_label': 'Annual Salary',
        'total_debt_label': 'Total Debt',
        'after_10y_pretax': '10y (pre-tax)',
        'after_10y_aftertax': '10y (after tax',
        'after_20y': 'In 20 years',
        # Finance details
        'help_savings_rate_detail': 'Savings vs salary. 20%+ recommended.',
        'help_emergency_coverage': 'How many months of expenses your emergency fund covers. 6 months recommended.',
        'help_dti_detail': 'Monthly debt service / salary. Under 36% recommended.',
        'help_retirement_track_detail': 'Multiplier of retirement target. 1.0+ is good.',
        'help_investment_ratio_detail': 'Investment ratio of total assets. 30-70% recommended.',
        'investment_ratio_label': 'Investment Ratio',
        'all_metrics_good': '✅ All financial metrics are in good shape!',
        # Recommendations
        'rec_savings_title': '🚨 Low Savings Rate',
        'rec_savings_text': 'Current savings rate {0:.1f}%. Reduce expenses or earn additional income. Target: 20%+.',
        'rec_emergency_title': '🚨 Insufficient Emergency Fund',
        'rec_emergency_text': 'Emergency fund covers only {0:.1f} months of expenses. Target: 6 months. Essential for unexpected job loss or medical bills.',
        'rec_dti_title': '🚨 High Debt Burden',
        'rec_dti_text': 'Debt-to-income ratio {0:.1f}%. Prioritize paying off high-interest debt first. If debt rate exceeds investment return, paying off comes first.',
        'rec_retirement_title': '⚠️ Retirement Preparation Lacking',
        'rec_retirement_text': 'Current pace projects only {0:.1f}x of retirement target. Consider increasing monthly contributions or adjusting target retirement age.',
        'rec_invest_low_title': '💡 Consider Increasing Investment',
        'rec_invest_low_text': 'Investment ratio is low. After securing 6 months emergency fund, gradually increase investing is recommended.',
        'rec_invest_high_title': '💡 Review Investment Concentration',
        'rec_invest_high_text': 'Investment ratio is very high. Review your emergency fund and safe asset allocation.',
        # Budget
        'budget_caption': 'Essentials 50% / Wants 30% / Savings 20%',
        'budget_essentials': 'Essentials (50%)',
        'budget_wants': 'Wants (30%)',
        'budget_savings_invest': 'Savings/Invest (20%)',
        'budget_category': 'Category',
        'ideal_label': 'Ideal',
        'actual_label': 'Actual',
        # Errors
        'error_name_required': 'Name is required',
        # Analysis hints
        'press_analyze_hint': '👈 Press **🚀 Run Analysis** in the sidebar to see portfolio and hidden gems.',
        'analysis_time_hint': '⏱️ Full market analysis ~7 min',
        'settings_guide_title': '📚 Settings Guide (click)',
        'clear_cache_btn': '🔄 Clear Cache (on error)',
        'cache_cleared': '✅ Cache cleared. Please start analysis again.',
        'analysis_error_title': '⚠️ Error during analysis',
        'analysis_error_hint': 'Click the button below to clear cache and retry. yfinance servers may be temporarily down.',
        'no_data_warning': '⚠️ Cannot fetch data. Please try again later or clear cache.',
        # Financial Goal Tab
        'tab_goal': '🎯 Financial Goal',
        'goal_planner_title': '🎯 Financial Goal Planner',
        'goal_planner_subtitle': "Tell us how much and when — we'll show you the path",
        'goal_step1': '📝 Step 1. Set Your Goal',
        'goal_step2': '📊 Step 2. Diagnosis',
        'goal_step3': '🎲 Step 3. Compare Scenarios',
        'goal_step4': '💼 Step 4. Detailed Portfolio',
        'goal_amount_label': 'How much do you want to save?',
        'goal_years_label': 'How many years to reach it?',
        'goal_purpose_label': "What's this money for?",
        'purpose_house': '🏠 Buy a house',
        'purpose_retirement': '🌅 Retirement',
        'purpose_education': "🎓 Children's education",
        'purpose_marriage': '💍 Marriage',
        'purpose_car': '🚗 Buy a car',
        'purpose_freedom': '🦅 Financial freedom (FIRE)',
        'purpose_other': '✨ Other',
        'save_goal_btn': '🎯 Save Goal',
        'goal_saved': '✅ Goal saved',
        'no_goal_yet': '👆 Please enter and save your goal above',
        'diag_current_pace': 'Current Pace Diagnosis',
        'diag_current_assets': 'Current Assets',
        'diag_monthly_save': 'Monthly Saving Capacity',
        'diag_simple_savings_label': 'Savings only (3% APY)',
        'diag_required_return': 'Required Annual Return',
        'diag_achievable': '🎯 Achievable',
        'diag_difficult': '⚠️ Challenging',
        'diag_impossible': '❌ Unrealistic',
        'diag_solutions_header': '💡 Solutions',
        'diag_increase_monthly': 'Increase monthly contribution',
        'diag_extend_years': 'Extend timeline',
        'diag_increase_return': 'Higher return (more risk)',
        'scenario_expected': 'Expected outcome',
        'scenario_worst_case': 'Worst case (-1σ)',
        'scenario_best_case': 'Best case (+1σ)',
        'scenario_gap': 'vs Target',
        'scenario_volatility': 'Expected volatility',
        'scenario_mdd_warn': 'Historical max drawdown',
        'recommended_for_you': '✨ Recommended for your goal',
        'select_scenario': 'Select scenario',
        'etf_region_label': 'ETF type',
        'etf_region_us': '🇺🇸 US-listed ETFs (USD)',
        'etf_region_kr': '🇰🇷 Korea-listed ETFs (KRW)',
        'core_satellite_ratio': 'Core / Satellite ratio',
        'core_label': '🏛️ CORE (ETF)',
        'satellite_label': '🚀 SATELLITE (Stocks)',
        'monthly_buy_plan': '📅 Monthly Buying Plan',
        'no_stock_screening_yet': '⚠️ Please press **🚀 Run Analysis** in the sidebar first (for satellite stock recommendations)',
        'goal_summary_card': '📋 Goal Summary',
        'until_goal': 'Until goal',
        # Economic Forum
        'tab_econ_forum': '🌐 Economic Forum',
        'econ_forum_title': '🌐 Global Economic Forum',
        'econ_forum_subtitle': 'Detailed economic analysis · Market outlook · Future industries by country',
        'econ_global': '🌐 Global',
        'econ_korea': '🇰🇷 Korea',
        'econ_usa': '🇺🇸 USA',
        'econ_denmark': '🇩🇰 Denmark',
        'econ_section_situation': '📊 Current Economic Situation',
        'econ_section_stocks': '📈 Stock Market Analysis',
        'econ_section_forecast': '🔮 Expected Economic Flow',
        'econ_section_industries': '🚀 Future Promising Industries',
        'forecast_short': 'Short-term (6 months)',
        'forecast_mid': 'Mid-term (1-2 years)',
        'forecast_long': 'Long-term (3-5 years)',
        'monthly_save_label': 'Monthly Save Capacity',
        'actual_buy_label': 'Actual Purchase Amount',
        'cash_leftover': 'Cash Leftover',
        'cash_leftover_help': "Can't buy fractional shares. Carry over to next month.",
        'details_btn': 'Details',
        'expected_return_label': 'Expected Return',
        'core_vs_satellite_title': 'Core vs Satellite',
        'stocks_by_weight': 'Stocks by Weight',
        'cumulative_simulation': '📈 Cumulative Wealth Simulation',
        'savings_only_achieve': 'Goal achievable with savings only!',
        'shortage_label': 'Shortage',
        'currency_label': 'Currency',
        'no_predict_disclaimer': "⚠️ This is data-based analysis, not a prediction of the future. Actual outcomes may differ.",
        'diag_note_savings_ok': 'Achievable with conservative (savings/bonds focused)',
        'diag_note_invest_needed': 'Investment needed (moderate~aggressive recommended)',
        'diag_note_aggressive_needed': 'Aggressive investment required (high risk)',
        'diag_note_impossible_text': 'Goal or timeline adjustment needed',
        'diag_current_label': 'Current',
        'diag_needed_label': 'Needed',
        'diag_current_goal': 'Current goal',
        'diag_assumed_7pct': '(assuming 7% annual return)',
        'diag_required_return_short': 'Required return',
        'diag_review_aggressive': 'Review aggressive scenario',
        'diag_risk_warning': '(Risk acceptance required)',
        'goal_at_pretax': '/mo',
        'recommended_badge': '⭐ Recommended',
        # Goal Achievement Manager (sidebar)
        'goal_manager_title': '🎯 Goal Achievement Manager',
        'goal_manager_no_goal': "👇 Please set your goal in the 'Financial Goal' tab first.",
        'my_goal_label': '📋 My Goal',
        'until_target': 'Until target',
        'required_pace': '🎯 Required Pace',
        'required_return_label': 'Required return',
        'current_scenario': 'Current scenario',
        'asset_allocation': '💼 Recommended Asset Allocation',
        'asset_bonds': '🏦 Bonds',
        'asset_etf': '📊 ETFs',
        'asset_stocks': '🚀 Individual Stocks',
        'asset_commodities': '🪙 Commodities',
        'advanced_section': '🔬 Advanced Analysis (Optional)',
        'advanced_section_desc': 'Full-market multi-factor + Hidden Gems',
        'change_etf_region': 'Change ETF type',
        'change_scenario': 'Change scenario',
        'physical_gold_note': '💡 Physical gold/silver via KRX gold market or banks',
        'see_portfolio_tab_hint': '👉 Check Portfolio tab for share quantities / 💎 Hidden Gems for undervalued stocks',
    },
    'da': {
        'title': 'SMART PORTFOLIO BUILDER',
        'subtitle': 'Smart investering — Personlig økonomi + Investering',
        'welcome_title': '👋 Kom i gang',
        'welcome_desc': 'Indtast dine oplysninger. Alle data gemmes på din computer.',
        'name': 'Navn', 'age': 'Alder', 'nationality': 'Nationalitet',
        'monthly_salary': 'Månedsløn', 'salary_currency': 'Lønvaluta',
        'investment_amount': 'Investeringsbeløb', 'investment_currency': 'Valuta',
        'email': 'Email (valgfri)', 'save_profile': '💾 Gem',
        'edit_profile': '✏️ Rediger', 'delete_profile': '🗑️ Slet',
        'profile_saved': '✅ Profil gemt',
        'monthly_expenses': 'Månedlige udgifter',
        'emergency_fund': 'Nødfond',
        'total_debt': 'Samlet gæld',
        'debt_interest_rate': 'Gældsrente (%)',
        'retirement_savings': 'Pensionsopsparing',
        'target_retirement_age': 'Pensionsalder mål',
        'dependents': 'Afhængige',
        'has_insurance': 'Har forsikring',
        'has_pension': 'Har pension',
        'financial_health': '🏥 Økonomisk sundhed',
        'health_score': 'Sundhedsscore',
        'savings_rate': 'Opsparingsrate',
        'emergency_coverage': 'Nødfond dækning',
        'debt_to_income': 'Gæld-til-indkomst',
        'retirement_track': 'Pensionsspor',
        'investment_capacity': '💰 Investeringskapacitet',
        'tab_hidden_gems': '💎 Skjulte perler',
        'hidden_gems_title': '💎 Undervurderede aktier med opsidepotentiale',
        'hidden_gems_subtitle': 'Fuld markedsanalyse',
        'gem_score': 'Perle-score',
        'recommended_portfolio': '🎯 Anbefalet portefølje',
        'run_analysis': '🚀 Start analyse',
        'analyzing': 'Analyserer...',
        'loading_macro': '📡 Henter markedsdata...',
        'loading_stocks': '📊 Analyserer aktier...',
        'tab_dashboard': '🏠 Dashboard',
        'tab_finance': '💰 Økonomi',
        'tab_overview': '📰 Marked',
        'tab_screening': '📊 Screening',
        'tab_portfolio': '🎯 Portefølje',
        'tab_outlook': '🔮 Udsigt',
        'tab_management': '📋 Guide',
        'tab_glossary': '📖 Ordliste',
        'market_select': '🌏 Marked',
        'risk': 'Risiko',
        'risk_low': '🛡️ Konservativ', 'risk_mid': '⚖️ Moderat', 'risk_high': '🚀 Aggressiv',
        'market_us': '🇺🇸 USA (S&P + NASDAQ)',
        'market_kr': '🇰🇷 Korea (KOSPI + KOSDAQ)',
        'market_dk': '🇩🇰 Danmark (OMX)',
        'market_all': '🌍 Alle',
        'market_rec': '✨ Anbefalet',
        'expected_return': 'Forventet afkast', 'volatility': 'Volatilitet',
        'sharpe': 'Sharpe', 'mdd': 'Maks. tab',
        'years_old': 'år', 'years': 'år', 'months': 'mdr',
        # Sektionsoverskrifter
        'section_basic_info': 'Grundlæggende oplysninger',
        'section_financial_detail': 'Økonomiske detaljer (valgfri)',
        'financial_overview_section': '💼 Økonomisk overblik',
        'wealth_projection_section': '📈 Formueprognose',
        'item_analysis': '📊 Komponentanalyse',
        'improvement_section': '💡 Forbedringsforslag',
        'budget_rule_section': '🎯 Budgetfordeling (50/30/20-reglen)',
        # Hjælpetekster
        'help_monthly_expenses': 'Månedlige udgifter i gennemsnit. Bruges til opsparingsrate.',
        'help_emergency_fund': 'Nødfond. Anbefalet: 6 måneders udgifter',
        'help_total_debt': 'Samlet gæld (boliglån, studielån, forbrugslån mv.)',
        'help_debt_rate': 'Gennemsnitlig rente',
        'help_retirement_savings': 'Folkepension, ratepension, arbejdsgiverpension mv.',
        'help_target_age': 'Ønsket pensionsalder',
        'projection_assumption': 'Antagelse: 8% årligt afkast, månedligt bidrag med samme rate',
        # Dashboard
        'invested_assets': 'Investerede aktiver',
        'annual_salary_label': 'Årsløn',
        'total_debt_label': 'Samlet gæld',
        'after_10y_pretax': '10 år (før skat)',
        'after_10y_aftertax': '10 år (efter skat',
        'after_20y': 'Om 20 år',
        # Økonomi detaljer
        'help_savings_rate_detail': 'Opsparing vs løn. 20%+ anbefalet.',
        'help_emergency_coverage': 'Hvor mange måneders udgifter din nødfond dækker. 6 måneder anbefalet.',
        'help_dti_detail': 'Månedlig gældsservice / løn. Under 36% anbefalet.',
        'help_retirement_track_detail': 'Multiplikator af pensionsmål. 1.0+ er godt.',
        'help_investment_ratio_detail': 'Investeringsandel af samlede aktiver. 30-70% anbefalet.',
        'investment_ratio_label': 'Investeringsandel',
        'all_metrics_good': '✅ Alle økonomiske målinger er i god stand!',
        # Anbefalinger
        'rec_savings_title': '🚨 Lav opsparingsrate',
        'rec_savings_text': 'Nuværende opsparingsrate {0:.1f}%. Reducer udgifter eller tjen ekstra. Mål: 20%+.',
        'rec_emergency_title': '🚨 Utilstrækkelig nødfond',
        'rec_emergency_text': 'Nødfond dækker kun {0:.1f} måneders udgifter. Mål: 6 måneder. Essentiel ved pludseligt jobskifte eller medicinske udgifter.',
        'rec_dti_title': '🚨 Høj gældsbyrde',
        'rec_dti_text': 'Gæld-til-indkomst {0:.1f}%. Prioriter højrentegæld først. Hvis gældsrente overstiger afkast, har afdrag førsteprioritet.',
        'rec_retirement_title': '⚠️ Mangelfuld pensionsforberedelse',
        'rec_retirement_text': 'Nuværende tempo prognoser kun {0:.1f}x af pensionsmål. Overvej øgede månedlige bidrag eller juster pensionsalder.',
        'rec_invest_low_title': '💡 Overvej øget investering',
        'rec_invest_low_text': 'Investeringsandel er lav. Efter at sikre 6 måneders nødfond, anbefales gradvist øget investering.',
        'rec_invest_high_title': '💡 Gennemgå investeringskoncentration',
        'rec_invest_high_text': 'Investeringsandel er meget høj. Gennemgå din nødfond og sikre aktiver.',
        # Budget
        'budget_caption': 'Nødvendigt 50% / Ønsker 30% / Opsparing 20%',
        'budget_essentials': 'Nødvendigt (50%)',
        'budget_wants': 'Ønsker (30%)',
        'budget_savings_invest': 'Opsparing/Invest (20%)',
        'budget_category': 'Kategori',
        'ideal_label': 'Anbefalet',
        'actual_label': 'Faktisk',
        # Fejl
        'error_name_required': 'Navn er påkrævet',
        # Analyse hints
        'press_analyze_hint': '👈 Tryk **🚀 Start analyse** i sidemenuen for at se portefølje og skjulte perler.',
        'analysis_time_hint': '⏱️ Fuld markedsanalyse ~7 min',
        'settings_guide_title': '📚 Indstillingsguide (klik)',
        'clear_cache_btn': '🔄 Ryd cache (ved fejl)',
        'cache_cleared': '✅ Cache ryddet. Start analysen igen.',
        'analysis_error_title': '⚠️ Fejl under analyse',
        'analysis_error_hint': 'Klik på knappen nedenfor for at rydde cache og prøv igen. yfinance-serverne kan være midlertidigt nede.',
        'no_data_warning': '⚠️ Kan ikke hente data. Prøv igen senere eller ryd cache.',
        # Finansielt Mål Tab
        'tab_goal': '🎯 Finansielt mål',
        'goal_planner_title': '🎯 Finansiel målplanlægger',
        'goal_planner_subtitle': 'Fortæl os hvor meget og hvornår — vi viser vejen',
        'goal_step1': '📝 Step 1. Sæt dit mål',
        'goal_step2': '📊 Step 2. Diagnose',
        'goal_step3': '🎲 Step 3. Sammenlign scenarier',
        'goal_step4': '💼 Step 4. Detaljeret portefølje',
        'goal_amount_label': 'Hvor meget vil du spare op?',
        'goal_years_label': 'Hvor mange år for at nå det?',
        'goal_purpose_label': 'Hvad er pengene til?',
        'purpose_house': '🏠 Køb af bolig',
        'purpose_retirement': '🌅 Pension',
        'purpose_education': '🎓 Børneuddannelse',
        'purpose_marriage': '💍 Bryllup',
        'purpose_car': '🚗 Køb af bil',
        'purpose_freedom': '🦅 Økonomisk frihed (FIRE)',
        'purpose_other': '✨ Andet',
        'save_goal_btn': '🎯 Gem mål',
        'goal_saved': '✅ Mål gemt',
        'no_goal_yet': '👆 Indtast og gem dit mål ovenfor',
        'diag_current_pace': 'Diagnose af nuværende tempo',
        'diag_current_assets': 'Nuværende aktiver',
        'diag_monthly_save': 'Månedlig opsparingskapacitet',
        'diag_simple_savings_label': 'Kun opsparing (3% rente)',
        'diag_required_return': 'Krævet årligt afkast',
        'diag_achievable': '🎯 Opnåeligt',
        'diag_difficult': '⚠️ Udfordrende',
        'diag_impossible': '❌ Urealistisk',
        'diag_solutions_header': '💡 Løsninger',
        'diag_increase_monthly': 'Øg månedligt bidrag',
        'diag_extend_years': 'Forlæng tidslinjen',
        'diag_increase_return': 'Højere afkast (mere risiko)',
        'scenario_expected': 'Forventet resultat',
        'scenario_worst_case': 'Værste tilfælde (-1σ)',
        'scenario_best_case': 'Bedste tilfælde (+1σ)',
        'scenario_gap': 'vs Mål',
        'scenario_volatility': 'Forventet volatilitet',
        'scenario_mdd_warn': 'Historisk maks. tab',
        'recommended_for_you': '✨ Anbefalet til dit mål',
        'select_scenario': 'Vælg scenarie',
        'etf_region_label': 'ETF-type',
        'etf_region_us': '🇺🇸 US-noterede ETFer (USD)',
        'etf_region_kr': '🇰🇷 Korea-noterede ETFer (KRW)',
        'core_satellite_ratio': 'Core / Satellite forhold',
        'core_label': '🏛️ CORE (ETF)',
        'satellite_label': '🚀 SATELLITE (Aktier)',
        'monthly_buy_plan': '📅 Månedlig købsplan',
        'no_stock_screening_yet': '⚠️ Tryk **🚀 Start analyse** i sidemenuen først (for satellitanbefalinger)',
        'goal_summary_card': '📋 Målsammendrag',
        'until_goal': 'Indtil mål',
        # Økonomisk Forum
        'tab_econ_forum': '🌐 Økonomisk forum',
        'econ_forum_title': '🌐 Globalt økonomisk forum',
        'econ_forum_subtitle': 'Detaljeret økonomisk analyse · Markedsudsigt · Fremtidige industrier pr. land',
        'econ_global': '🌐 Global',
        'econ_korea': '🇰🇷 Korea',
        'econ_usa': '🇺🇸 USA',
        'econ_denmark': '🇩🇰 Danmark',
        'econ_section_situation': '📊 Nuværende økonomisk situation',
        'econ_section_stocks': '📈 Aktiemarkedsanalyse',
        'econ_section_forecast': '🔮 Forventet økonomisk flow',
        'econ_section_industries': '🚀 Fremtidige lovende industrier',
        'forecast_short': 'Kort sigt (6 måneder)',
        'forecast_mid': 'Mellem sigt (1-2 år)',
        'forecast_long': 'Lang sigt (3-5 år)',
        'monthly_save_label': 'Månedlig opsparingskapacitet',
        'actual_buy_label': 'Faktisk købsbeløb',
        'cash_leftover': 'Kontanter tilbage',
        'cash_leftover_help': 'Kan ikke købe brøkdele af aktier. Overfør til næste måned.',
        'details_btn': 'Detaljer',
        'expected_return_label': 'Forventet afkast',
        'core_vs_satellite_title': 'Core vs Satellite',
        'stocks_by_weight': 'Aktier efter vægt',
        'cumulative_simulation': '📈 Kumulativ formuesimulering',
        'savings_only_achieve': 'Mål kan nås med opsparing alene!',
        'shortage_label': 'Mangler',
        'currency_label': 'Valuta',
        'no_predict_disclaimer': '⚠️ Dette er databaseret analyse, ikke en forudsigelse. Faktiske resultater kan afvige.',
        'diag_note_savings_ok': 'Opnåeligt med konservativ (opsparing/obligationer)',
        'diag_note_invest_needed': 'Investering nødvendig (moderat~aggressiv anbefalet)',
        'diag_note_aggressive_needed': 'Aggressiv investering krævet (høj risiko)',
        'diag_note_impossible_text': 'Mål eller tidslinje skal justeres',
        'diag_current_label': 'Nuværende',
        'diag_needed_label': 'Nødvendig',
        'diag_current_goal': 'Nuværende mål',
        'diag_assumed_7pct': '(antager 7% årligt afkast)',
        'diag_required_return_short': 'Krævet afkast',
        'diag_review_aggressive': 'Gennemgå aggressivt scenarie',
        'diag_risk_warning': '(Risikoaccept krævet)',
        'goal_at_pretax': '/mdr',
        'recommended_badge': '⭐ Anbefalet',
        # Målopnåelsesmanager (sidebar)
        'goal_manager_title': '🎯 Målopnåelsesmanager',
        'goal_manager_no_goal': "👇 Indstil dit mål i 'Finansielt mål' fanen først.",
        'my_goal_label': '📋 Mit mål',
        'until_target': 'Indtil mål',
        'required_pace': '🎯 Krævet tempo',
        'required_return_label': 'Krævet afkast',
        'current_scenario': 'Nuværende scenarie',
        'asset_allocation': '💼 Anbefalet aktivallokering',
        'asset_bonds': '🏦 Obligationer',
        'asset_etf': '📊 ETFer',
        'asset_stocks': '🚀 Individuelle aktier',
        'asset_commodities': '🪙 Råvarer',
        'advanced_section': '🔬 Avanceret analyse (valgfri)',
        'advanced_section_desc': 'Fuld-marked multifaktor + Skjulte perler',
        'change_etf_region': 'Skift ETF-type',
        'change_scenario': 'Skift scenarie',
        'physical_gold_note': '💡 Fysisk guld/sølv via KRX guldmarked eller banker',
        'see_portfolio_tab_hint': '👉 Tjek Portefølje for aktiemængder / 💎 Skjulte perler for undervurderede aktier',
    },
}


def t(key):
    lang = st.session_state.get('lang', 'ko')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ko']).get(key, key)


# ============================================================
# 종목 유니버스 (대폭 확장)
# ============================================================

# S&P 500 시가총액 상위 100개
SP500_UNIVERSE = [
    'AAPL','MSFT','NVDA','GOOGL','GOOG','AMZN','META','BRK-B','TSLA','AVGO',
    'JPM','LLY','V','XOM','UNH','MA','JNJ','PG','HD','COST',
    'ABBV','CVX','WMT','MRK','NFLX','KO','ADBE','PEP','BAC','CRM',
    'TMO','ORCL','AMD','LIN','CSCO','ACN','MCD','ABT','WFC','INTC',
    'DIS','IBM','PFE','GE','CAT','NKE','INTU','GS','CMCSA','NOW',
    'TXN','UBER','SPGI','BLK','UPS','ISRG','HON','BX','VRTX','PLTR',
    'NEE','DE','RTX','BKNG','LMT','AXP','ELV','LOW','PGR','TJX',
    'MS','PANW','CB','SCHW','BSX','SYK','MMC','ETN','MDT','BMY',
    'ADP','ANET','C','BA','MO','REGN','FI','ZTS','CI','GILD',
    'AMAT','MU','DUK','EQIX','SO','SLB','APH','LRCX','KKR','ICE',
]

# NASDAQ 100 (S&P 500과 중복 제거)
NASDAQ_UNIVERSE = [
    'PEP','ADBE','CSCO','NFLX','AMD','INTC','CMCSA','TXN','QCOM','HON',
    'INTU','AMGN','SBUX','GILD','MDLZ','ADI','ISRG','VRTX','REGN','LRCX',
    'PANW','KLAC','MELI','SNPS','CDNS','MAR','CTAS','MNST','ASML','ORLY',
    'ABNB','FTNT','ADSK','CHTR','ROP','MRVL','PCAR','PYPL','NXPI','PAYX',
    'AEP','MCHP','ROST','KDP','AZN','CPRT','IDXX','KHC','BIIB','EXC',
    'DASH','LULU','XEL','CTSH','FAST','EA','ON','ODFL','CSGP','VRSK',
    'CCEP','TEAM','GEHC','DDOG','DXCM','ZS','ANSS','CRWD','MDB','SMCI',
]
# 중복 제거
NASDAQ_UNIVERSE = list(set(NASDAQ_UNIVERSE) - set(SP500_UNIVERSE))[:70]

# KOSPI 시가총액 상위 100개
KOSPI_UNIVERSE = [
    '005930.KS','000660.KS','373220.KS','207940.KS','005380.KS','000270.KS',
    '012450.KS','068270.KS','005490.KS','035420.KS','105560.KS','055550.KS',
    '035720.KS','012330.KS','028260.KS','015760.KS','086790.KS','051910.KS',
    '006400.KS','017670.KS','003550.KS','032830.KS','009150.KS','030200.KS',
    '011200.KS','010130.KS','034730.KS','267260.KS','329180.KS','034020.KS',
    '316140.KS','024110.KS','138040.KS','138930.KS','139480.KS','010140.KS',
    '011170.KS','009540.KS','018260.KS','032640.KS','000810.KS','047040.KS',
    '034220.KS','272210.KS','097950.KS','161390.KS','241560.KS','004020.KS',
    '012630.KS','000150.KS','005940.KS','000720.KS','029780.KS','047810.KS',
    '180640.KS','008770.KS','021240.KS','035250.KS','069960.KS','004990.KS',
    '128940.KS','271560.KS','006800.KS','009830.KS','020150.KS','000990.KS',
    '003490.KS','004370.KS','078930.KS','011070.KS','088350.KS','017800.KS',
    '011780.KS','035250.KS','006260.KS','001040.KS','402340.KS','003410.KS',
    '073240.KS','006360.KS','035250.KS','001450.KS','000080.KS','047050.KS',
    '111770.KS','010120.KS','093370.KS','069620.KS','009240.KS','007070.KS',
    '009830.KS','000240.KS','097230.KS','030000.KS','000880.KS','001120.KS',
    '030210.KS','005830.KS','267250.KS','161890.KS',
]
KOSPI_UNIVERSE = list(dict.fromkeys(KOSPI_UNIVERSE))[:100]  # 중복 제거

# KOSDAQ 시가총액 상위 50개
KOSDAQ_UNIVERSE = [
    '247540.KQ',  # 에코프로비엠
    '086520.KQ',  # 에코프로
    '091990.KQ',  # 셀트리온헬스케어
    '028300.KQ',  # HLB
    '196170.KQ',  # 알테오젠
    '263750.KQ',  # 펄어비스
    '058470.KQ',  # 리노공업
    '041510.KQ',  # 에스엠
    '067310.KQ',  # 하나마이크론
    '293490.KQ',  # 카카오게임즈
    '357780.KQ',  # 솔브레인
    '141080.KQ',  # 레고켐바이오
    '112040.KQ',  # 위메이드
    '039030.KQ',  # 이오테크닉스
    '214150.KQ',  # 클래시스
    '328130.KQ',  # 루닛
    '348370.KQ',  # 엔켐
    '240810.KQ',  # 원익IPS
    '418550.KQ',  # 제이오
    '950140.KQ',  # 잉글우드랩
    '393890.KQ',  # 더블유씨피
    '278280.KQ',  # 천보
    '195940.KQ',  # HK이노엔
    '178320.KQ',  # 서진시스템
    '084990.KQ',  # 헬릭스미스
    '108860.KQ',  # 셀바스AI
    '950130.KQ',  # 엑세스바이오
    '950170.KQ',  # JTC
    '253450.KQ',  # 스튜디오드래곤
    '215000.KQ',  # 골프존
    '060280.KQ',  # 큐렉소
    '060720.KQ',  # KH바텍
    '278470.KQ',  # 에이피알
    '290510.KQ',  # 코리아센터
    '950210.KQ',  # 프레스티지바이오파마
    '321820.KQ',  # 디앤씨미디어
    '352820.KQ',  # 하이브
    '298540.KQ',  # 더네이쳐홀딩스
    '900140.KQ',  # 엘브이엠씨홀딩스
    '950160.KQ',  # 코오롱티슈진
    '215600.KQ',  # 신라젠
    '085660.KQ',  # 차바이오텍
    '215200.KQ',  # 메가스터디교육
    '034950.KQ',  # 한국기업평가
    '054620.KQ',  # APS홀딩스
    '950110.KQ',  # SBI핀테크
    '347860.KQ',  # 알체라
    '298380.KQ',  # 에이비엘바이오
    '950220.KQ',  # 네오이뮨텍
    '950200.KQ',  # 소마젠
]

# 한국 종목명
KOREAN_NAMES = {
    '005930.KS':'삼성전자','000660.KS':'SK하이닉스','373220.KS':'LG에너지솔루션',
    '207940.KS':'삼성바이오로직스','005380.KS':'현대차','000270.KS':'기아',
    '012450.KS':'한화에어로스페이스','068270.KS':'셀트리온','005490.KS':'POSCO홀딩스',
    '035420.KS':'NAVER','105560.KS':'KB금융','055550.KS':'신한지주',
    '035720.KS':'카카오','012330.KS':'현대모비스','028260.KS':'삼성물산',
    '015760.KS':'한국전력','086790.KS':'하나금융지주','051910.KS':'LG화학',
    '006400.KS':'삼성SDI','017670.KS':'SK텔레콤','003550.KS':'LG',
    '032830.KS':'삼성생명','009150.KS':'삼성전기','030200.KS':'KT',
    '011200.KS':'HMM','010130.KS':'고려아연','034730.KS':'SK',
    '267260.KS':'HD현대일렉트릭','329180.KS':'HD현대중공업','034020.KS':'두산에너빌리티',
    '316140.KS':'우리금융지주','024110.KS':'기업은행','138040.KS':'메리츠금융지주',
    '247540.KQ':'에코프로비엠','086520.KQ':'에코프로','091990.KQ':'셀트리온헬스케어',
    '028300.KQ':'HLB','196170.KQ':'알테오젠','263750.KQ':'펄어비스',
    '058470.KQ':'리노공업','041510.KQ':'에스엠','067310.KQ':'하나마이크론',
    '293490.KQ':'카카오게임즈','357780.KQ':'솔브레인','141080.KQ':'레고켐바이오',
    '112040.KQ':'위메이드','039030.KQ':'이오테크닉스','214150.KQ':'클래시스',
    '328130.KQ':'루닛','348370.KQ':'엔켐','240810.KQ':'원익IPS',
    '352820.KQ':'하이브','195940.KQ':'HK이노엔',
}

# 덴마크 OMX (확장 가능하지만 OMX C25가 사실상 시장 대부분)
OMXC25_UNIVERSE = [
    'NOVO-B.CO','DSV.CO','MAERSK-B.CO','ORSTED.CO','CARL-B.CO',
    'COLO-B.CO','DEMANT.CO','PNDORA.CO','VWS.CO','TRYG.CO',
    'DANSKE.CO','ROCK-B.CO','GMAB.CO','AMBU-B.CO','GN.CO',
    'JYSK.CO','ISS.CO','FLS.CO','LUN.CO','SIM.CO',
    'BAVA.CO','NKT.CO','CHRH.CO','NDA-DK.CO','NETC.CO',
]

DANISH_NAMES = {
    'NOVO-B.CO':'Novo Nordisk','DSV.CO':'DSV','MAERSK-B.CO':'Mærsk',
    'ORSTED.CO':'Ørsted','CARL-B.CO':'Carlsberg','COLO-B.CO':'Coloplast',
    'DEMANT.CO':'Demant','PNDORA.CO':'Pandora','VWS.CO':'Vestas',
    'TRYG.CO':'Tryg','DANSKE.CO':'Danske Bank','ROCK-B.CO':'Rockwool',
    'GMAB.CO':'Genmab','AMBU-B.CO':'Ambu','GN.CO':'GN Store Nord',
    'JYSK.CO':'Jyske Bank','ISS.CO':'ISS','FLS.CO':'FLSmidth',
    'LUN.CO':'Lundbeck','SIM.CO':'SimCorp','BAVA.CO':'Bavarian Nordic',
    'NKT.CO':'NKT','CHRH.CO':'Novonesis','NDA-DK.CO':'Nordea Bank',
    'NETC.CO':'Netcompany',
}

MACRO_TICKERS = {
    'SPY':'S&P 500','^IXIC':'NASDAQ','^VIX':'VIX','^TNX':'10Y Yield',
    'TLT':'Long Treasury','GLD':'Gold','UUP':'Dollar Index',
    '^KS11':'KOSPI','^KQ11':'KOSDAQ','^OMXC25':'OMX C25',
    'KRW=X':'USD/KRW','DKK=X':'USD/DKK',
}

SECTOR_ETFS = {
    'XLK':'Technology','XLF':'Financial','XLV':'Healthcare','XLE':'Energy',
    'XLI':'Industrial','XLY':'Cons. Disc.','XLP':'Cons. Staples',
    'XLU':'Utilities','XLB':'Materials','XLRE':'Real Estate',
}

RISK_ALLOCATION = {
    'low':  {'stocks': 0.30, 'bonds': 0.55, 'gold': 0.10, 'cash': 0.05},
    'mid':  {'stocks': 0.60, 'bonds': 0.30, 'gold': 0.05, 'cash': 0.05},
    'high': {'stocks': 0.85, 'bonds': 0.10, 'gold': 0.05, 'cash': 0.00},
}

CURRENCY_SYMBOLS = {'USD': '$', 'KRW': '₩', 'DKK': 'kr.'}


# ============================================================
# Core-Satellite 포트폴리오용 ETF Universe
# ============================================================

# 미국 상장 ETF (달러)
ETF_US = {
    # 주식
    'VOO':  {'name': 'S&P 500 (미국 대형주)',     'category': 'us_equity',     'currency': 'USD'},
    'VTI':  {'name': '미국 전체 시장',             'category': 'us_equity',     'currency': 'USD'},
    'QQQ':  {'name': 'NASDAQ 100 (테크)',          'category': 'us_tech',       'currency': 'USD'},
    'VEA':  {'name': '선진국 주식 (유럽/일본)',    'category': 'intl_equity',   'currency': 'USD'},
    'VWO':  {'name': '신흥국 주식',                'category': 'em_equity',     'currency': 'USD'},
    'EDEN': {'name': 'iShares 덴마크',             'category': 'denmark_equity','currency': 'USD'},
    'EWY':  {'name': 'iShares 한국',               'category': 'korea_equity',  'currency': 'USD'},
    # 채권
    'AGG':  {'name': '미국 종합 채권',             'category': 'us_bond',       'currency': 'USD'},
    'BND':  {'name': '미국 전체 채권',             'category': 'us_bond',       'currency': 'USD'},
    'TLT':  {'name': '미국 장기 국채 (20년+)',     'category': 'us_long_bond',  'currency': 'USD'},
    # 안전자산
    'GLD':  {'name': '금 (현물 추종)',             'category': 'gold',          'currency': 'USD'},
    'IAU':  {'name': '금 (저비용)',                'category': 'gold',          'currency': 'USD'},
    # 부동산
    'VNQ':  {'name': '미국 리츠',                  'category': 'reit',          'currency': 'USD'},
}

# 한국 상장 ETF (원화)
ETF_KR = {
    # 미국 노출
    '360750.KS': {'name': 'TIGER 미국S&P500',      'category': 'us_equity',     'currency': 'KRW'},
    '379800.KS': {'name': 'KODEX 미국S&P500TR',    'category': 'us_equity',     'currency': 'KRW'},
    '133690.KS': {'name': 'TIGER 미국나스닥100',   'category': 'us_tech',       'currency': 'KRW'},
    '381180.KS': {'name': 'TIGER 미국필라델피아반도체', 'category': 'us_tech',  'currency': 'KRW'},
    # 한국
    '069500.KS': {'name': 'KODEX 200',             'category': 'korea_equity',  'currency': 'KRW'},
    '232080.KS': {'name': 'TIGER 코스닥150',       'category': 'kosdaq_equity', 'currency': 'KRW'},
    '278530.KS': {'name': 'KODEX 200TR',           'category': 'korea_equity',  'currency': 'KRW'},
    # 선진국/신흥국
    '195930.KS': {'name': 'TIGER 일본니케이225',   'category': 'intl_equity',   'currency': 'KRW'},
    '195980.KS': {'name': 'ARIRANG 신흥국MSCI',    'category': 'em_equity',     'currency': 'KRW'},
    # 채권
    '153130.KS': {'name': 'KODEX 단기채권',        'category': 'us_bond',       'currency': 'KRW'},
    '114260.KS': {'name': 'KODEX 국고채3년',       'category': 'us_bond',       'currency': 'KRW'},
    '305080.KS': {'name': 'TIGER 미국채30년스트립액티브(합성 H)', 'category': 'us_long_bond', 'currency': 'KRW'},
    # 금
    '132030.KS': {'name': 'KODEX 골드선물(H)',     'category': 'gold',          'currency': 'KRW'},
    '411060.KS': {'name': 'ACE KRX금현물',         'category': 'gold',          'currency': 'KRW'},
    # 리츠
    '157490.KS': {'name': 'KODEX 미국리츠',        'category': 'reit',          'currency': 'KRW'},
}

# 시나리오별 ETF 배분 (카테고리 단위)
ETF_ALLOCATIONS = {
    'conservative': {
        # 채권 위주, 안정성 우선
        'us_equity':     0.10,
        'intl_equity':   0.05,
        'us_bond':       0.55,
        'gold':          0.10,
    },
    'moderate': {
        # 균형형
        'us_equity':     0.40,
        'intl_equity':   0.15,
        'us_bond':       0.30,
        'gold':          0.10,
        'em_equity':     0.05,
    },
    'aggressive': {
        # 주식 위주
        'us_equity':     0.50,
        'us_tech':       0.15,
        'intl_equity':   0.15,
        'em_equity':     0.05,
        'us_bond':       0.10,
        'gold':          0.05,
    },
}

# 시나리오별 예상 수익률/변동성
SCENARIO_PARAMS = {
    'conservative': {'return': 0.045, 'volatility': 0.07, 'mdd': -0.10},
    'moderate':     {'return': 0.075, 'volatility': 0.13, 'mdd': -0.25},
    'aggressive':   {'return': 0.105, 'volatility': 0.20, 'mdd': -0.40},
}


# ============================================================
# 자산 배분 & 종목 추천 (재무목표 달성 매니저용)
# ============================================================

# 시나리오별 4대 자산 배분 비율
PORTFOLIO_BREAKDOWN = {
    'conservative': {
        'bonds':       0.55,   # 채권 (안정성 우선)
        'etf':         0.25,   # ETF (분산 투자)
        'stocks':      0.10,   # 개별주 (보조)
        'commodities': 0.10,   # 금/은 (헷지)
    },
    'moderate': {
        'bonds':       0.25,
        'etf':         0.40,
        'stocks':      0.25,
        'commodities': 0.10,
    },
    'aggressive': {
        'bonds':       0.10,
        'etf':         0.40,
        'stocks':      0.40,
        'commodities': 0.10,
    },
}

# 자산별 추천 종목 (지역별)
BOND_RECS = {
    'US': [  # 미국 상장 (USD)
        {'ticker': 'AGG',  'name_ko': '미국 종합 채권',         'name_en': 'US Aggregate Bond',   'flag': '🇺🇸'},
        {'ticker': 'TLT',  'name_ko': '미국 장기 국채 (20Y+)',  'name_en': 'US Long Treasury',    'flag': '🇺🇸'},
        {'ticker': 'TIP',  'name_ko': '인플레이션 보호 채권',   'name_en': 'Inflation-Protected', 'flag': '🇺🇸'},
        {'ticker': 'BND',  'name_ko': '미국 전체 채권',          'name_en': 'Total Bond Market',   'flag': '🇺🇸'},
    ],
    'KR': [  # 한국 상장 (KRW)
        {'ticker': '114260.KS', 'name_ko': 'KODEX 국고채3년',     'name_en': 'KODEX Korea 3Y',    'flag': '🇰🇷'},
        {'ticker': '153130.KS', 'name_ko': 'KODEX 단기채권',      'name_en': 'KODEX Short Bond',  'flag': '🇰🇷'},
        {'ticker': '305080.KS', 'name_ko': 'TIGER 미국채30년',     'name_en': 'TIGER US 30Y',      'flag': '🇺🇸→🇰🇷'},
        {'ticker': '136340.KS', 'name_ko': 'KBSTAR 중기우량회사채', 'name_en': 'KBSTAR Corp Bond', 'flag': '🇰🇷'},
    ],
}

ETF_RECS = {
    'US': [  # 미국 상장 (USD)
        {'ticker': 'VOO',  'name_ko': 'S&P 500 (미국 대형주)',   'name_en': 'S&P 500',           'flag': '🇺🇸'},
        {'ticker': 'QQQ',  'name_ko': 'NASDAQ 100 (테크)',       'name_en': 'NASDAQ 100',        'flag': '🇺🇸'},
        {'ticker': 'VTI',  'name_ko': '미국 전체 시장',           'name_en': 'US Total Market',   'flag': '🇺🇸'},
        {'ticker': 'VEA',  'name_ko': '선진국 주식 (유럽/일본)',  'name_en': 'Developed Markets', 'flag': '🌍'},
        {'ticker': 'VWO',  'name_ko': '신흥국 주식',              'name_en': 'Emerging Markets',  'flag': '🌍'},
        {'ticker': 'EWY',  'name_ko': 'iShares 한국',             'name_en': 'iShares Korea',     'flag': '🇰🇷'},
        {'ticker': 'EDEN', 'name_ko': 'iShares 덴마크',           'name_en': 'iShares Denmark',   'flag': '🇩🇰'},
    ],
    'KR': [  # 한국 상장 (KRW)
        {'ticker': '360750.KS', 'name_ko': 'TIGER 미국S&P500',    'name_en': 'TIGER US S&P500',  'flag': '🇺🇸→🇰🇷'},
        {'ticker': '133690.KS', 'name_ko': 'TIGER 미국나스닥100', 'name_en': 'TIGER US NASDAQ',  'flag': '🇺🇸→🇰🇷'},
        {'ticker': '069500.KS', 'name_ko': 'KODEX 200',           'name_en': 'KODEX 200',        'flag': '🇰🇷'},
        {'ticker': '195930.KS', 'name_ko': 'TIGER 일본니케이225', 'name_en': 'TIGER Nikkei',     'flag': '🇯🇵'},
        {'ticker': '232080.KS', 'name_ko': 'TIGER 코스닥150',     'name_en': 'TIGER KOSDAQ150',  'flag': '🇰🇷'},
    ],
}

# 개별주 추천 (글로벌 우량주 - 통화별로 분산)
STOCK_RECS = [
    # 🇺🇸 미국
    {'ticker': 'AAPL',       'name': 'Apple',                    'flag': '🇺🇸', 'sector_ko': 'IT/소비재',  'sector_en': 'IT/Consumer'},
    {'ticker': 'MSFT',       'name': 'Microsoft',                'flag': '🇺🇸', 'sector_ko': 'AI/클라우드','sector_en': 'AI/Cloud'},
    {'ticker': 'NVDA',       'name': 'NVIDIA',                   'flag': '🇺🇸', 'sector_ko': 'AI 반도체',  'sector_en': 'AI Chips'},
    {'ticker': 'LLY',        'name': 'Eli Lilly',                'flag': '🇺🇸', 'sector_ko': '제약/GLP-1','sector_en': 'Pharma/GLP-1'},
    # 🇰🇷 한국
    {'ticker': '005930.KS',  'name': '삼성전자',                  'flag': '🇰🇷', 'sector_ko': '반도체',     'sector_en': 'Semiconductor'},
    {'ticker': '000660.KS',  'name': 'SK하이닉스',                'flag': '🇰🇷', 'sector_ko': 'HBM/반도체', 'sector_en': 'HBM/Semi'},
    {'ticker': '012450.KS',  'name': '한화에어로스페이스',        'flag': '🇰🇷', 'sector_ko': 'K-방산',     'sector_en': 'K-Defense'},
    {'ticker': '207940.KS',  'name': '삼성바이오로직스',          'flag': '🇰🇷', 'sector_ko': 'K-바이오',   'sector_en': 'K-Bio'},
    # 🇩🇰 덴마크
    {'ticker': 'NOVO-B.CO',  'name': 'Novo Nordisk',             'flag': '🇩🇰', 'sector_ko': 'GLP-1 1위',  'sector_en': 'GLP-1 Leader'},
    {'ticker': 'VWS.CO',     'name': 'Vestas',                   'flag': '🇩🇰', 'sector_ko': '풍력 1위',   'sector_en': 'Wind Leader'},
]

# 원자재 (금/은/실물)
COMMODITY_RECS = {
    'US': [
        {'ticker': 'GLD',  'name_ko': '금 ETF (현물 추종)',     'name_en': 'Gold ETF',           'type': '🥇', 'flag': '🇺🇸'},
        {'ticker': 'IAU',  'name_ko': '금 ETF (저비용)',         'name_en': 'Gold ETF (low fee)', 'type': '🥇', 'flag': '🇺🇸'},
        {'ticker': 'SLV',  'name_ko': '은 ETF',                  'name_en': 'Silver ETF',         'type': '🥈', 'flag': '🇺🇸'},
        {'ticker': 'PHYS', 'name_ko': 'Sprott 실물 금 트러스트', 'name_en': 'Physical Gold Trust','type': '💎', 'flag': '🇺🇸'},
    ],
    'KR': [
        {'ticker': '411060.KS', 'name_ko': 'ACE KRX금현물',       'name_en': 'ACE KRX Gold Spot',  'type': '🥇', 'flag': '🇰🇷'},
        {'ticker': '132030.KS', 'name_ko': 'KODEX 골드선물(H)',   'name_en': 'KODEX Gold Futures', 'type': '🥇', 'flag': '🇰🇷'},
        {'ticker': '139320.KS', 'name_ko': 'TIGER 골드선물',      'name_en': 'TIGER Gold',         'type': '🥇', 'flag': '🇰🇷'},
        {'ticker': 'PHYSICAL',  'name_ko': '실물 금/은 (KRX·시중은행)', 'name_en': 'Physical Gold/Silver (KRX/Banks)', 'type': '💎', 'flag': '🇰🇷'},
    ],
}


def scenario_to_risk(scenario):
    """시나리오 → risk 프로파일 매핑"""
    return {
        'conservative': 'low',
        'moderate': 'mid',
        'aggressive': 'high',
    }.get(scenario, 'mid')


def select_etf_for_category(category, region):
    """카테고리에 맞는 ETF 한 개 선택 (지역에 따라)"""
    etf_pool = ETF_US if region == 'US' else ETF_KR
    candidates = [(ticker, info) for ticker, info in etf_pool.items()
                  if info['category'] == category]
    if not candidates:
        # fallback: 가장 유사한 카테고리
        if category == 'us_long_bond':
            return select_etf_for_category('us_bond', region)
        if category == 'em_equity':
            return select_etf_for_category('intl_equity', region)
        if category == 'us_tech':
            return select_etf_for_category('us_equity', region)
        return None, None
    return candidates[0]


def build_core_portfolio(scenario, core_weight, region):
    """시나리오와 지역에 따른 Core ETF 포트폴리오 구성
    Returns: dict of {ticker: weight}
    """
    allocation = ETF_ALLOCATIONS[scenario]
    total = sum(allocation.values())

    portfolio = {}
    for category, ratio in allocation.items():
        ticker, info = select_etf_for_category(category, region)
        if ticker is None:
            continue
        # core_weight 내에서 비율
        final_weight = (ratio / total) * core_weight
        if ticker in portfolio:
            portfolio[ticker] += final_weight
        else:
            portfolio[ticker] = final_weight
    return portfolio


# ============================================================
# 유틸리티
# ============================================================
def get_universe_by_market(market_key):
    if market_key == 'us':
        return SP500_UNIVERSE + NASDAQ_UNIVERSE
    elif market_key == 'kr':
        return KOSPI_UNIVERSE + KOSDAQ_UNIVERSE
    elif market_key == 'dk':
        return OMXC25_UNIVERSE
    elif market_key == 'all':
        return SP500_UNIVERSE + NASDAQ_UNIVERSE + KOSPI_UNIVERSE + KOSDAQ_UNIVERSE + OMXC25_UNIVERSE
    return SP500_UNIVERSE + NASDAQ_UNIVERSE


def get_full_universe():
    """숨은 가치주 발굴용 - 전체 시장"""
    return SP500_UNIVERSE + NASDAQ_UNIVERSE + KOSPI_UNIVERSE + KOSDAQ_UNIVERSE + OMXC25_UNIVERSE


def get_market_name(ticker):
    if ticker.endswith('.KS'):
        return '🇰🇷 KOSPI'
    elif ticker.endswith('.KQ'):
        return '🇰🇷 KOSDAQ'
    elif ticker.endswith('.CO'):
        return '🇩🇰 DK'
    return '🇺🇸 US'


def get_stock_currency(ticker):
    if ticker.endswith('.KS') or ticker.endswith('.KQ'):
        return 'KRW'
    elif ticker.endswith('.CO'):
        return 'DKK'
    return 'USD'


def get_display_name(ticker, fallback):
    if ticker in KOREAN_NAMES:
        return KOREAN_NAMES[ticker]
    if ticker in DANISH_NAMES:
        return DANISH_NAMES[ticker]
    return fallback


def convert_amount(amount, from_curr, to_curr, exchange_rates):
    if from_curr == to_curr:
        return amount
    if from_curr == 'USD':
        usd = amount
    elif from_curr == 'KRW':
        usd = amount / exchange_rates.get('KRW', 1300)
    elif from_curr == 'DKK':
        usd = amount / exchange_rates.get('DKK', 7)
    else:
        usd = amount
    if to_curr == 'USD':
        return usd
    elif to_curr == 'KRW':
        return usd * exchange_rates.get('KRW', 1300)
    elif to_curr == 'DKK':
        return usd * exchange_rates.get('DKK', 7)
    return usd


def fmt_money(amount, currency):
    symbol = CURRENCY_SYMBOLS.get(currency, '')
    if currency == 'KRW':
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:,.2f}" if amount < 1000 else f"{symbol}{amount:,.0f}"


# ============================================================
# 데이터 수집
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        end = datetime.now()
        start = end - timedelta(days=400)
        hist = stock.history(start=start, end=end)
        if len(hist) < 150:
            return None

        if len(hist) >= 252:
            momentum = hist['Close'].iloc[-21] / hist['Close'].iloc[-252] - 1
            momentum_3m = hist['Close'].iloc[-1] / hist['Close'].iloc[-63] - 1 if len(hist) >= 63 else np.nan
        else:
            momentum = np.nan
            momentum_3m = np.nan

        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)

        sector = info.get('sector', 'N/A')
        if not sector or sector == 'N/A':
            sector = info.get('industry', 'N/A')

        current_price = info.get('currentPrice')
        if not current_price:
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else np.nan

        return {
            'ticker': ticker,
            'name': get_display_name(ticker, info.get('shortName', ticker)),
            'market': get_market_name(ticker),
            'sector': sector,
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', np.nan),
            'pe_ratio': info.get('trailingPE', np.nan),
            'forward_pe': info.get('forwardPE', np.nan),
            'pb_ratio': info.get('priceToBook', np.nan),
            'ps_ratio': info.get('priceToSalesTrailing12Months', np.nan),
            'roe': info.get('returnOnEquity', np.nan),
            'roa': info.get('returnOnAssets', np.nan),
            'operating_margin': info.get('operatingMargins', np.nan),
            'profit_margin': info.get('profitMargins', np.nan),
            'debt_to_equity': info.get('debtToEquity', np.nan),
            'current_ratio': info.get('currentRatio', np.nan),
            'revenue_growth': info.get('revenueGrowth', np.nan),
            'earnings_growth': info.get('earningsGrowth', np.nan),
            'momentum_12_1': momentum,
            'momentum_3m': momentum_3m,
            'volatility': volatility,
            'current_price': current_price,
            'currency': get_stock_currency(ticker),
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_stocks(tickers):
    records = []
    progress = st.progress(0, text=t('loading_stocks'))
    for i, ticker in enumerate(tickers):
        rec = fetch_stock_data(ticker)
        if rec:
            records.append(rec)
        progress.progress((i+1)/len(tickers), text=f"{ticker} ({i+1}/{len(tickers)})")
    progress.empty()
    return pd.DataFrame(records)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_macro_data():
    data = {}
    for ticker, name in MACRO_TICKERS.items():
        try:
            hist = yf.Ticker(ticker).history(period="1y")
            if len(hist) < 21:
                continue
            current = hist['Close'].iloc[-1]
            data[ticker] = {
                'name': name,
                'current': current,
                '1m_change': (current / hist['Close'].iloc[-21] - 1) * 100,
                '3m_change': (current / hist['Close'].iloc[-63] - 1) * 100 if len(hist) >= 63 else 0,
                '1y_change': (current / hist['Close'].iloc[0] - 1) * 100,
                'history': hist['Close'],
            }
        except Exception:
            continue
    return data


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sector_data():
    results = []
    for ticker, name in SECTOR_ETFS.items():
        try:
            hist = yf.Ticker(ticker).history(period="3mo")
            if len(hist) < 21:
                continue
            ret_1m = (hist['Close'].iloc[-1] / hist['Close'].iloc[-21] - 1) * 100
            ret_3m = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
            results.append({'Sector': name, 'ETF': ticker, '1M': ret_1m, '3M': ret_3m})
        except Exception:
            continue
    return pd.DataFrame(results).sort_values('1M', ascending=False)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_exchange_rates():
    rates = {'USD': 1.0}
    try:
        krw = yf.Ticker('KRW=X').history(period='5d')
        rates['KRW'] = krw['Close'].iloc[-1] if len(krw) else 1300
    except:
        rates['KRW'] = 1300
    try:
        dkk = yf.Ticker('DKK=X').history(period='5d')
        rates['DKK'] = dkk['Close'].iloc[-1] if len(dkk) else 7
    except:
        rates['DKK'] = 7
    return rates


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(tickers, years=2):
    end = datetime.now()
    start = end - timedelta(days=365 * years)
    data = yf.download(tickers, start=start, end=end, progress=False)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
    return data.dropna(axis=1, how='all')


# ============================================================
# 팩터 & 포트폴리오 최적화
# ============================================================
def calculate_factors(df):
    df = df.copy()
    # yfinance가 일부 종목 데이터를 문자열로 반환하는 경우 방어
    numeric_cols = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'roe', 'roa',
                    'operating_margin', 'profit_margin', 'debt_to_equity',
                    'current_ratio', 'revenue_growth', 'earnings_growth',
                    'momentum_12_1', 'momentum_3m', 'volatility',
                    'current_price', 'market_cap', 'forward_pe']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['earnings_yield'] = 1 / df['pe_ratio']
    df['book_to_market'] = 1 / df['pb_ratio']
    df['low_vol'] = -df['volatility']
    return df


def zscore_normalize(df, cols):
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        df[f'{col}_z'] = np.nan
        for mkt in df['market'].unique():
            mask = df['market'] == mkt
            x = df.loc[mask, col]
            mean, std = x.mean(), x.std()
            if std > 0:
                z = ((x - mean) / std).clip(-3, 3)
            else:
                z = pd.Series(0.0, index=x.index)
            df.loc[mask, f'{col}_z'] = z
    return df


def combine_factors(df, weights):
    df = df.copy()
    df['value_score'] = df[['earnings_yield_z', 'book_to_market_z']].mean(axis=1)
    df['quality_score'] = df[['roe_z', 'roa_z', 'operating_margin_z']].mean(axis=1)
    df['momentum_score'] = df['momentum_12_1_z']
    df['low_vol_score'] = df['low_vol_z']
    df['total_score'] = (
        df['value_score'] * weights['value']
        + df['quality_score'] * weights['quality']
        + df['momentum_score'] * weights['momentum']
        + df['low_vol_score'] * weights['low_vol']
    )
    return df


def run_screening(weights, universe):
    df = fetch_all_stocks(universe)
    if df.empty:
        return df

    # 1. 팩터 계산 (이미 pd.to_numeric으로 방어됨)
    try:
        df = calculate_factors(df)
    except Exception as e:
        print(f"calculate_factors error: {e}")
        return pd.DataFrame()

    # 2. 핵심 지표 누락 종목 제거
    required = ['earnings_yield', 'book_to_market', 'roe', 'momentum_12_1', 'volatility']
    df = df.dropna(subset=required).reset_index(drop=True)

    if df.empty:
        return df

    # 3. 시장별 z-score 정규화
    try:
        df = zscore_normalize(df, [
            'earnings_yield', 'book_to_market', 'roe', 'roa',
            'operating_margin', 'momentum_12_1', 'low_vol'
        ])
    except Exception as e:
        print(f"zscore_normalize error: {e}")
        return df  # 정규화 실패해도 원본 반환

    # 4. 팩터 조합
    try:
        df = combine_factors(df, weights)
    except Exception as e:
        print(f"combine_factors error: {e}")
        return df

    return df.sort_values('total_score', ascending=False).reset_index(drop=True)


def portfolio_metrics(weights, returns):
    ann_return = np.sum(returns.mean() * weights) * 252
    ann_vol = np.sqrt(weights @ (returns.cov() * 252) @ weights)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0
    return ann_return, ann_vol, sharpe


def optimize_max_sharpe(returns, max_weight=0.25):
    n = returns.shape[1]
    init = np.array([1/n] * n)
    bounds = tuple((0.02, max_weight) for _ in range(n))
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)
    result = minimize(
        lambda w: -portfolio_metrics(w, returns)[2],
        init, method='SLSQP', bounds=bounds, constraints=constraints,
        options={'ftol': 1e-9, 'maxiter': 500},
    )
    return result.x if result.success else init


def compute_max_drawdown(returns_series):
    cumulative = (1 + returns_series).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def recommend_market(macro):
    scores = {}
    spy_1y = macro.get('SPY', {}).get('1y_change', 0)
    spy_3m = macro.get('SPY', {}).get('3m_change', 0)
    vix = macro.get('^VIX', {}).get('current', 20)
    scores['us'] = spy_1y * 0.5 + spy_3m * 0.5 - max(0, vix - 20) * 2
    kospi_1y = macro.get('^KS11', {}).get('1y_change', 0)
    kospi_3m = macro.get('^KS11', {}).get('3m_change', 0)
    scores['kr'] = kospi_1y * 0.5 + kospi_3m * 0.5
    omxc_1y = macro.get('^OMXC25', {}).get('1y_change', 0)
    omxc_3m = macro.get('^OMXC25', {}).get('3m_change', 0)
    scores['dk'] = omxc_1y * 0.5 + omxc_3m * 0.5
    best = sorted(scores.items(), key=lambda x: -x[1])
    return best[0][0], scores


# ============================================================
# 🔥 숨은 가치주 발굴 알고리즘 (Deep Value Hunter)
# ============================================================
def find_hidden_gems(stock_df, macro, top_n=15):
    """저평가 + 미래 상승 가능성 큰 종목 찾기
    
    다중 신호 결합:
    1. 가치 신호: 낮은 PER, 낮은 PBR, 낮은 PSR
    2. 품질 신호: 양호한 ROE, 적은 부채, 양의 이익률
    3. 회복 신호: 3개월 모멘텀 > 12개월 모멘텀 (turnaround)
    4. 성장 신호: 매출 성장, 이익 성장
    5. 가치 함정 회피: 너무 낮은 PER (< 5)은 위험 신호로 간주
    """
    if stock_df.empty:
        return pd.DataFrame()
    
    df = stock_df.copy()
    
    # 필수 지표 누락 제거
    df = df.dropna(subset=['pe_ratio', 'pb_ratio', 'roe']).copy()
    
    if df.empty:
        return df
    
    # ── 1. Deep Value Score (저평가 정도) ──
    # PER 낮을수록, PBR 낮을수록 ↑
    # 단, PER < 5는 의심 (가치 함정 가능성) → 페널티
    df['value_signal'] = 0.0
    for mkt in df['market'].unique():
        mask = df['market'] == mkt
        sub = df[mask]
        
        # PER 점수 (역수, 단 너무 낮으면 페널티)
        pe = sub['pe_ratio']
        pe_score = np.where(pe < 5, -1.0,  # 가치 함정 의심
                            np.where(pe > 100, -0.5,  # 너무 비쌈
                                     1 / pe))
        pe_z = pd.Series(pe_score).rank(pct=True).values * 2 - 1
        
        # PBR 점수
        pb = sub['pb_ratio']
        pb_score = np.where(pb < 0.3, -1.0,  # 청산 위험
                            np.where(pb > 20, -0.5,
                                     1 / pb))
        pb_z = pd.Series(pb_score).rank(pct=True).values * 2 - 1
        
        df.loc[mask, 'value_signal'] = (pe_z + pb_z) / 2
    
    # ── 2. Quality Signal (재무 건전성) ──
    # ROE > 0, 부채비율 적정, 이익률 양수
    df['quality_signal'] = 0.0
    for mkt in df['market'].unique():
        mask = df['market'] == mkt
        sub = df[mask]
        
        roe_score = sub['roe'].clip(-1, 1).rank(pct=True).values * 2 - 1
        
        # 부채비율: 너무 높으면 페널티
        debt = sub['debt_to_equity'].fillna(50)
        debt_score = np.where(debt > 200, -1.0,
                              np.where(debt < 30, 0.5, 0.0))
        debt_z = pd.Series(debt_score).rank(pct=True).values * 2 - 1
        
        # 이익률
        margin_score = sub['operating_margin'].fillna(0).clip(-0.5, 0.5).rank(pct=True).values * 2 - 1
        
        df.loc[mask, 'quality_signal'] = (roe_score + debt_z + margin_score) / 3
    
    # ── 3. Turnaround Signal (회복 신호) ──
    # 3개월 모멘텀이 12개월보다 강함 = 최근 반등 시작
    df['turnaround_signal'] = 0.0
    if 'momentum_3m' in df.columns:
        df['turnaround_signal'] = (
            df['momentum_3m'].fillna(0) - df['momentum_12_1'].fillna(0)
        ).rank(pct=True) * 2 - 1
    
    # ── 4. Growth Signal (성장 신호) ──
    df['growth_signal'] = 0.0
    if 'revenue_growth' in df.columns:
        rev_g = df['revenue_growth'].fillna(0).clip(-0.5, 1.0)
        df['growth_signal'] += rev_g.rank(pct=True) * 2 - 1
    if 'earnings_growth' in df.columns:
        earn_g = df['earnings_growth'].fillna(0).clip(-1, 2.0)
        df['growth_signal'] += (earn_g.rank(pct=True) * 2 - 1)
    df['growth_signal'] /= 2
    
    # ── 5. 산업 모멘텀 보정 ──
    # 매크로 환경 고려
    tnx = macro.get('^TNX', {}).get('current', 4)
    
    # ── 종합 Gem Score ──
    # 가중 평균: 가치 35%, 품질 25%, 회복 20%, 성장 20%
    df['gem_score'] = (
        df['value_signal'] * 0.35
        + df['quality_signal'] * 0.25
        + df['turnaround_signal'] * 0.20
        + df['growth_signal'] * 0.20
    )
    
    # 너무 작은 시가총액 또는 너무 적은 데이터는 제외
    df = df[df['market_cap'].fillna(0) > 1e9]  # 시총 10억 USD 이상
    
    return df.sort_values('gem_score', ascending=False).head(top_n).copy()


# ============================================================
# 개인 재무 관리 (강화)
# ============================================================
def project_wealth(initial_usd, monthly_invest_usd, years, annual_return=0.08):
    months = int(years * 12)
    if months == 0:
        return initial_usd
    monthly_return = annual_return / 12
    fv = initial_usd * ((1 + monthly_return) ** months)
    if monthly_invest_usd > 0:
        fv += monthly_invest_usd * (((1 + monthly_return) ** months - 1) / monthly_return)
    return fv


def calculate_required_return(current_usd, monthly_usd, years, target_usd):
    """목표 달성에 필요한 연 수익률 역산 (이분법)"""
    if years <= 0 or target_usd <= 0:
        return 0.0
    # 적립금 합계도 못 따라가면 무한
    total_contributions = current_usd + monthly_usd * 12 * years
    if total_contributions >= target_usd:
        # 단순 예금만 해도 됨 (0% 수익률 가정)
        return 0.0

    # 이분법으로 수익률 찾기
    low, high = 0.0, 1.0  # 0% ~ 100%
    for _ in range(60):
        mid = (low + high) / 2
        fv = project_wealth(current_usd, monthly_usd, years, mid)
        if fv < target_usd:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def project_goal_scenarios(current_usd, monthly_usd, years, target_usd):
    """3가지 시나리오로 목표 달성 분석"""
    scenarios = {}
    for key in ['conservative', 'moderate', 'aggressive']:
        params = SCENARIO_PARAMS[key]
        expected_fv = project_wealth(current_usd, monthly_usd, years, params['return'])
        # 변동성 고려한 범위 (단순화: ±1σ)
        ann_vol = params['volatility']
        worst_case = project_wealth(current_usd, monthly_usd, years, params['return'] - ann_vol * 0.5)
        best_case = project_wealth(current_usd, monthly_usd, years, params['return'] + ann_vol * 0.5)
        scenarios[key] = {
            'expected_return': params['return'],
            'volatility': ann_vol,
            'mdd': params['mdd'],
            'expected_fv': expected_fv,
            'worst_fv': max(0, worst_case),
            'best_fv': best_case,
            'gap_to_target': expected_fv - target_usd,
            'achievable': expected_fv >= target_usd,
        }
    return scenarios


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_etf_price(ticker):
    """ETF 현재가격 + 통화"""
    try:
        etf = yf.Ticker(ticker)
        info = etf.info
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not price:
            hist = etf.history(period='5d')
            if len(hist) > 0:
                price = hist['Close'].iloc[-1]
        return float(price) if price else None
    except Exception:
        return None


def build_full_portfolio(scenario, core_weight, region, satellite_stocks, stock_info_map):
    """Core (ETF) + Satellite (개별주) 통합 포트폴리오 빌드

    Args:
        scenario: 'conservative' / 'moderate' / 'aggressive'
        core_weight: 0.30 ~ 0.40 (Core 비율)
        region: 'US' or 'KR' (ETF 지역)
        satellite_stocks: 위성 종목 ticker 리스트
        stock_info_map: 종목 정보 dict

    Returns:
        DataFrame with: ticker, name, type, weight, price, currency
    """
    satellite_weight = 1.0 - core_weight

    rows = []

    # Core (ETF)
    core_portfolio = build_core_portfolio(scenario, core_weight, region)
    etf_pool = ETF_US if region == 'US' else ETF_KR
    for ticker, weight in core_portfolio.items():
        info = etf_pool.get(ticker, {})
        price = fetch_etf_price(ticker)
        rows.append({
            'ticker': ticker,
            'name': info.get('name', ticker),
            'type': 'CORE (ETF)',
            'weight': weight,
            'price': price,
            'currency': info.get('currency', 'USD'),
            'category': info.get('category', ''),
        })

    # Satellite (개별주) - 균등 분배
    n_satellite = len(satellite_stocks)
    if n_satellite > 0:
        weight_per_stock = satellite_weight / n_satellite
        for ticker in satellite_stocks:
            info = stock_info_map.get(ticker, {})
            rows.append({
                'ticker': ticker,
                'name': info.get('name', ticker),
                'type': 'SATELLITE (Stock)',
                'weight': weight_per_stock,
                'price': info.get('current_price'),
                'currency': info.get('currency', 'USD'),
                'category': info.get('sector', '')[:20],
            })

    return pd.DataFrame(rows)


def get_purpose_recommendation(purpose, years):
    """용도별 권장 시나리오 안내"""
    recommendations = {
        'house': {
            'recommended': 'moderate' if years >= 5 else 'conservative',
            'note_ko': '집 구매는 시점이 중요해서 단기는 보수형, 5년+면 균형형 권장. 결정적 시점 1~2년 전엔 안전자산으로 옮기세요.',
            'note_en': 'House purchase needs timing certainty. Conservative for short term, moderate for 5+ years. Shift to safe assets 1-2 years before purchase.',
            'note_da': 'Boligkøb kræver timing-sikkerhed. Konservativ på kort sigt, moderat for 5+ år. Skift til sikre aktiver 1-2 år før køb.',
        },
        'retirement': {
            'recommended': 'aggressive' if years >= 15 else 'moderate',
            'note_ko': '은퇴는 장기라 공격형이 유리. 은퇴 5년 전부터 점진적 보수형 전환 권장.',
            'note_en': 'Retirement is long-term, aggressive favored. Gradually shift to conservative 5 years before retirement.',
            'note_da': 'Pension er langsigtet, aggressiv foretrækkes. Skift gradvist til konservativ 5 år før pension.',
        },
        'education': {
            'recommended': 'moderate',
            'note_ko': '자녀 교육비는 시점이 정해진 목표. 균형형 권장 + 결정적 시점 3년 전 안전자산 전환.',
            'note_en': 'Education funding has fixed timing. Moderate recommended, shift to safe assets 3 years before.',
            'note_da': 'Uddannelsesfinansiering har fast timing. Moderat anbefalet.',
        },
        'marriage': {
            'recommended': 'conservative' if years <= 3 else 'moderate',
            'note_ko': '결혼은 보통 단기 목표. 3년 이내면 보수형, 그 이상은 균형형.',
            'note_en': 'Marriage is usually a short-term goal. Conservative for 3 years or less.',
            'note_da': 'Bryllup er normalt et kortsigtet mål. Konservativ for 3 år eller mindre.',
        },
        'car': {
            'recommended': 'conservative',
            'note_ko': '차 구매는 단기 목표. 보수형 권장. 손실 시 구매 미뤄야 함.',
            'note_en': 'Car purchase is short-term. Conservative recommended.',
            'note_da': 'Bilkøb er kortsigtet. Konservativ anbefalet.',
        },
        'freedom': {
            'recommended': 'aggressive',
            'note_ko': '재정 자유 (FIRE)는 장기 목표. 공격형 + 4% Rule 활용.',
            'note_en': 'Financial freedom (FIRE) is long-term. Aggressive + 4% Rule.',
            'note_da': 'Økonomisk frihed (FIRE) er langsigtet. Aggressiv + 4%-reglen.',
        },
        'other': {
            'recommended': 'moderate',
            'note_ko': '목표에 따라 권장 시나리오가 다를 수 있어요. 균형형이 기본 권장.',
            'note_en': 'Recommended scenario varies by goal. Moderate as default.',
            'note_da': 'Anbefalet scenarie varierer efter mål. Moderat som standard.',
        },
    }
    return recommendations.get(purpose, recommendations['other'])


def calculate_financial_health(user_data, exchange_rates):
    """재무 건강도 종합 평가 (0~100점)"""
    monthly_salary_usd = convert_amount(
        user_data['monthly_salary'], user_data['salary_currency'], 'USD', exchange_rates
    )
    monthly_expenses_usd = convert_amount(
        user_data.get('monthly_expenses', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    investment_usd = convert_amount(
        user_data['investment_amount'], user_data['investment_currency'], 'USD', exchange_rates
    )
    emergency_usd = convert_amount(
        user_data.get('emergency_fund', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    debt_usd = convert_amount(
        user_data.get('total_debt', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    retirement_usd = convert_amount(
        user_data.get('retirement_savings', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    
    components = {}
    
    # 1. 저축률 (월급 - 지출 vs 월급)
    if monthly_salary_usd > 0:
        savings_rate = max(0, (monthly_salary_usd - monthly_expenses_usd) / monthly_salary_usd)
        # 20% 이상: 만점, 10%: 50점, 0%: 0점
        components['savings_rate'] = {
            'value': savings_rate * 100,
            'score': min(100, savings_rate * 500),  # 20% → 100점
            'weight': 0.25,
        }
    else:
        components['savings_rate'] = {'value': 0, 'score': 0, 'weight': 0.25}
    
    # 2. 비상금 (월 지출 대비 몇 개월치)
    if monthly_expenses_usd > 0:
        emergency_months = emergency_usd / monthly_expenses_usd
        # 6개월 이상: 만점, 3개월: 50점, 0개월: 0점
        components['emergency'] = {
            'value': emergency_months,
            'score': min(100, emergency_months / 6 * 100),
            'weight': 0.20,
        }
    else:
        components['emergency'] = {'value': 0, 'score': 50, 'weight': 0.20}
    
    # 3. 부채소득비율 (월 부채 상환 / 월급)
    annual_debt_service = debt_usd * (user_data.get('debt_interest_rate', 0) / 100 + 0.10)  # 원금+이자 가정
    monthly_debt_service = annual_debt_service / 12
    if monthly_salary_usd > 0:
        dti = monthly_debt_service / monthly_salary_usd
        # 0%: 만점, 36% 초과: 0점
        components['dti'] = {
            'value': dti * 100,
            'score': max(0, 100 - dti * 280),  # 36% → 0점
            'weight': 0.20,
        }
    else:
        components['dti'] = {'value': 0, 'score': 100, 'weight': 0.20}
    
    # 4. 은퇴 준비도 (현재 자산 + 예상 적립 vs 목표)
    age = user_data['age']
    target_age = user_data.get('target_retirement_age', 60)
    years_to_retirement = max(1, target_age - age)
    monthly_save = max(0, monthly_salary_usd - monthly_expenses_usd)
    
    total_retirement_assets = retirement_usd + investment_usd
    projected_retirement = project_wealth(total_retirement_assets, monthly_save, years_to_retirement, 0.07)
    
    # 25년치 지출 = 4% Rule (FIRE 운동의 기준)
    target_retirement = monthly_expenses_usd * 12 * 25
    
    if target_retirement > 0:
        retirement_ratio = min(2.0, projected_retirement / target_retirement)
        components['retirement'] = {
            'value': retirement_ratio,
            'score': min(100, retirement_ratio * 50),  # 1.0배: 50점, 2.0배: 100점
            'weight': 0.20,
            'projected': projected_retirement,
            'target': target_retirement,
        }
    else:
        components['retirement'] = {'value': 0, 'score': 50, 'weight': 0.20}
    
    # 5. 투자 자산 비중 (총자산 대비 투자 비중)
    total_assets = investment_usd + emergency_usd + retirement_usd
    if total_assets > 0:
        invest_ratio = investment_usd / total_assets
        # 30~70%가 이상적
        if 0.3 <= invest_ratio <= 0.7:
            score = 100
        elif invest_ratio < 0.3:
            score = invest_ratio / 0.3 * 100
        else:
            score = max(0, (1 - (invest_ratio - 0.7) / 0.3) * 100)
        components['investment_ratio'] = {
            'value': invest_ratio * 100,
            'score': score,
            'weight': 0.15,
        }
    else:
        components['investment_ratio'] = {'value': 0, 'score': 0, 'weight': 0.15}
    
    # 종합 점수
    total_score = sum(c['score'] * c['weight'] for c in components.values())
    
    return {
        'total_score': total_score,
        'components': components,
        'monthly_salary_usd': monthly_salary_usd,
        'monthly_expenses_usd': monthly_expenses_usd,
        'monthly_save_usd': monthly_save,
        'years_to_retirement': years_to_retirement,
    }


def get_health_grade(score):
    if score >= 80: return ('A', '#1a7f37', '우수')
    if score >= 65: return ('B', '#0969da', '양호')
    if score >= 50: return ('C', '#9a6700', '보통')
    if score >= 35: return ('D', '#b35900', '주의')
    return ('F', '#cf222e', '위험')


# ============================================================
# 주식 매수 수량 계산
# ============================================================
def calculate_shares(weight, total_user_amount, user_currency,
                     stock_price, stock_currency, exchange_rates):
    target_amount_user = weight * total_user_amount
    target_amount_stock = convert_amount(target_amount_user, user_currency, stock_currency, exchange_rates)
    if stock_price <= 0:
        return 0, 0, 0
    shares = int(target_amount_stock / stock_price)
    actual_amount_stock = shares * stock_price
    actual_amount_user = convert_amount(actual_amount_stock, stock_currency, user_currency, exchange_rates)
    return shares, actual_amount_stock, actual_amount_user


# ============================================================
# 시장 분석 텍스트
# ============================================================
def generate_market_situation(macro, sectors, market_key, lang='ko'):
    vix = macro.get('^VIX', {}).get('current', 20)
    tnx = macro.get('^TNX', {}).get('current', 4)
    paragraphs = []

    if lang == 'ko':
        if vix < 15:
            mood = "매우 평온한"
            mood_desc = "투자자들이 큰 걱정 없이 매수 중. 분산 유지하세요."
        elif vix < 20:
            mood = "안정적인"
            mood_desc = "균형잡힌 포지셔닝이 적합."
        elif vix < 25:
            mood = "약간 불안한"
            mood_desc = "시장 긴장감. 분산 중요."
        else:
            mood = "불안한"
            mood_desc = "공포 모드. 역사적으로 매수 기회였던 경우 多."

        paragraphs.append(f"**🌍 글로벌 분위기: {mood}** (VIX {vix:.1f})\n\n{mood_desc}")

        if market_key in ['us', 'all', 'rec']:
            spy_1y = macro.get('SPY', {}).get('1y_change', 0)
            nasdaq_1y = macro.get('^IXIC', {}).get('1y_change', 0)
            if spy_1y > 20:
                p = f"미국 S&P 500은 1년간 **+{spy_1y:.1f}%**, NASDAQ은 **+{nasdaq_1y:.1f}%** 급등했습니다. AI 붐과 빅테크 실적이 주도하고 있어요. 과열 신호도 있어 **분할 매수** 권장."
            elif spy_1y > 5:
                p = f"미국 시장은 1년간 S&P 500 +{spy_1y:.1f}%, NASDAQ +{nasdaq_1y:.1f}%로 견조한 상승세. 신규 자금 유입에 적합한 환경."
            else:
                p = f"미국 시장: S&P 500 {spy_1y:+.1f}%, NASDAQ {nasdaq_1y:+.1f}%. 종목별 차별화 시기."
            paragraphs.append(f"**🇺🇸 미국 시장**\n\n{p}")

        if market_key in ['kr', 'all', 'rec']:
            kospi_1y = macro.get('^KS11', {}).get('1y_change', 0)
            kosdaq_1y = macro.get('^KQ11', {}).get('1y_change', 0)
            krw_1m = macro.get('KRW=X', {}).get('1m_change', 0)
            if kospi_1y > 30:
                p = (f"한국 KOSPI **+{kospi_1y:.1f}%**, KOSDAQ **+{kosdaq_1y:.1f}%** 강세. "
                     "AI·반도체 수퍼사이클(삼성전자, SK하이닉스)에 글로벌 자금 유입. "
                     "상승 대부분이 대형주 집중 → **종목 양극화 심함**. "
                     f"환율 1개월 {krw_1m:+.1f}% — "
                     f"{'원화 약세는 수출주 유리' if krw_1m > 0 else '원화 강세는 외국인 매수에 부담'}.")
            else:
                p = f"KOSPI {kospi_1y:+.1f}%, KOSDAQ {kosdaq_1y:+.1f}%. 한국 시장 동향."
            paragraphs.append(f"**🇰🇷 한국 시장**\n\n{p}")

        if market_key in ['dk', 'all', 'rec']:
            omxc_1y = macro.get('^OMXC25', {}).get('1y_change', 0)
            if omxc_1y > 20:
                p = (f"덴마크 OMX C25 **+{omxc_1y:.1f}%** 강세. "
                     "Novo Nordisk의 GLP-1 비만치료제 글로벌 수요와 Ørsted·Vestas의 회복이 주도. "
                     "북유럽 ESG 자금 유입 꾸준. Novo Nordisk 의존도 매우 높음.")
            else:
                p = f"덴마크 OMX C25 {omxc_1y:+.1f}%."
            paragraphs.append(f"**🇩🇰 덴마크 시장**\n\n{p}")

        if tnx > 4.5:
            paragraphs.append(f"📊 **미국 10Y 금리 {tnx:.2f}%** — 고금리.\n\n성장주 부담, **Value+Quality+금융주** 유리.")
        elif tnx < 3:
            paragraphs.append(f"📊 **미국 10Y 금리 {tnx:.2f}%** — 저금리.\n\n**Growth+Momentum+테크·리츠** 유리.")
        else:
            paragraphs.append(f"📊 **미국 10Y 금리 {tnx:.2f}%** — 중립.")

    elif lang == 'en':
        paragraphs.append(f"**🌍 VIX {vix:.1f}**")
        if market_key in ['us','all','rec']:
            spy_1y = macro.get('SPY', {}).get('1y_change', 0)
            nasdaq_1y = macro.get('^IXIC', {}).get('1y_change', 0)
            paragraphs.append(f"**🇺🇸 USA**: S&P 500 {spy_1y:+.1f}%, NASDAQ {nasdaq_1y:+.1f}% YoY")
        if market_key in ['kr','all','rec']:
            kospi_1y = macro.get('^KS11', {}).get('1y_change', 0)
            kosdaq_1y = macro.get('^KQ11', {}).get('1y_change', 0)
            paragraphs.append(f"**🇰🇷 Korea**: KOSPI {kospi_1y:+.1f}%, KOSDAQ {kosdaq_1y:+.1f}% YoY")
        if market_key in ['dk','all','rec']:
            omxc_1y = macro.get('^OMXC25', {}).get('1y_change', 0)
            paragraphs.append(f"**🇩🇰 Denmark**: OMX C25 {omxc_1y:+.1f}% YoY")
        paragraphs.append(f"📊 **US 10Y {tnx:.2f}%**")
    else:
        paragraphs.append(f"**🌍 VIX {vix:.1f}**, **US 10Y {tnx:.2f}%**")

    return paragraphs


def generate_future_outlook(macro, lang='ko'):
    vix = macro.get('^VIX', {}).get('current', 20)
    tnx = macro.get('^TNX', {}).get('current', 4)
    spy_1y = macro.get('SPY', {}).get('1y_change', 0)

    if lang == 'ko':
        if vix < 18 and tnx < 4.5 and spy_1y > 5:
            base = "현재 조건 유지 시 연 10~15% 안정적 수익 기대. 기술·헬스케어·소비재 주도."
        elif vix > 22:
            base = "시장 불안. 분할 매수가 가장 안전. 3~6개월 분산 매수."
        elif tnx > 5:
            base = "고금리 환경 지속. 가치주 + 금융주 + 현금 풍부한 회사 유리."
        else:
            base = "혼조세. 개별 종목 선정이 가장 중요."
        return [
            {'name':'🐂 낙관 (30%)','desc':'새로운 강세장. AI·반도체·바이오·재생에너지.','color':'success'},
            {'name':'⚖️ 기본 (50%)','desc':base,'color':'info'},
            {'name':'🐻 비관 (20%)','desc':'경기침체. 주식 -15~25%. 방어: 금, 국채, 필수소비재.','color':'warning'},
        ]
    elif lang == 'en':
        return [
            {'name':'🐂 Bullish (30%)','desc':'New bull market. AI, semiconductors, biotech.','color':'success'},
            {'name':'⚖️ Base case (50%)','desc':'Current conditions persist.','color':'info'},
            {'name':'🐻 Bearish (20%)','desc':'Recession fears. Stocks -15-25%.','color':'warning'},
        ]
    else:
        return [
            {'name':'🐂 Optimistisk (30%)','desc':'Nyt tyremarked.','color':'success'},
            {'name':'⚖️ Basis (50%)','desc':'Stabilt afkast forventes.','color':'info'},
            {'name':'🐻 Pessimistisk (20%)','desc':'Recessionsfrygt.','color':'warning'},
        ]


def identify_future_promising(stock_df, macro):
    if stock_df.empty:
        return pd.DataFrame()
    df = stock_df.copy()
    tnx = macro.get('^TNX', {}).get('current', 4)
    vix = macro.get('^VIX', {}).get('current', 20)
    if tnx > 4.5:
        w = {'value':0.40,'quality':0.30,'momentum':0.20,'low_vol':0.10}
    elif tnx < 3:
        w = {'value':0.15,'quality':0.30,'momentum':0.40,'low_vol':0.15}
    else:
        w = {'value':0.25,'quality':0.30,'momentum':0.25,'low_vol':0.20}
    if vix > 22:
        w['low_vol'] += 0.10; w['momentum'] -= 0.10
    df['future_score'] = (
        df['value_score']*w['value'] + df['quality_score']*w['quality']
        + df['momentum_score']*w['momentum'] + df['low_vol_score']*w['low_vol']
    )
    return df.sort_values('future_score', ascending=False).head(5).copy()


# ============================================================
# UI: 환영 화면
# ============================================================
def render_welcome():
    # 상단 우측에 언어 선택
    top_c1, top_c2 = st.columns([5, 1])
    with top_c2:
        lang_options = {'ko': '🇰🇷 한국어', 'en': '🇺🇸 English', 'da': '🇩🇰 Dansk'}
        current_lang = st.session_state.get('lang', 'ko')
        new_lang = st.selectbox(
            "🌐",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(current_lang),
            label_visibility='collapsed',
            key='welcome_lang',
        )
        if new_lang != current_lang:
            st.session_state.lang = new_lang
            st.rerun()

    st.markdown(f"# {t('title')}")
    st.markdown(f"##### {t('subtitle')}")
    st.markdown("---")
    st.markdown(f"## {t('welcome_title')}")
    st.markdown(t('welcome_desc'))
    st.markdown("")

    with st.form("welcome_form", clear_on_submit=False):
        st.markdown(f"##### {t('section_basic_info')}")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(t('name'), placeholder="Yunsuk Jang")
            age = st.number_input(t('age'), 18, 100, 30)
            nationality = st.selectbox(
                t('nationality'),
                options=['KR', 'DK', 'US'],
                format_func=lambda x: {'KR':'🇰🇷 한국','DK':'🇩🇰 덴마크','US':'🇺🇸 미국'}[x],
            )
            email = st.text_input(t('email'), placeholder="me@example.com")
        with c2:
            salary_currency = st.selectbox(
                t('salary_currency'),
                options=['KRW', 'USD', 'DKK'],
                format_func=lambda x: f"{CURRENCY_SYMBOLS[x]} {x}",
            )
            salary_default = {'KRW':4500000,'USD':4000,'DKK':35000}[salary_currency]
            monthly_salary = st.number_input(
                t('monthly_salary'), 0, value=salary_default,
                step=100000 if salary_currency == 'KRW' else 100,
            )
            investment_currency = st.selectbox(
                t('investment_currency'),
                options=['USD', 'KRW', 'DKK'],
                format_func=lambda x: f"{CURRENCY_SYMBOLS[x]} {x}",
            )
            invest_default = {'USD':10000,'KRW':13000000,'DKK':70000}[investment_currency]
            investment_amount = st.number_input(
                t('investment_amount'), 0, value=invest_default,
                step=1000 if investment_currency in ['USD','DKK'] else 100000,
            )

        st.markdown(f"##### {t('section_financial_detail')}")
        c1, c2 = st.columns(2)
        with c1:
            monthly_expenses = st.number_input(
                t('monthly_expenses'), 0, value=int(monthly_salary*0.6),
                step=100000 if salary_currency == 'KRW' else 100,
                help=t('help_monthly_expenses'),
            )
            emergency_fund = st.number_input(
                t('emergency_fund'), 0, value=0,
                step=100000 if salary_currency == 'KRW' else 100,
                help=t('help_emergency_fund'),
            )
            total_debt = st.number_input(
                t('total_debt'), 0, value=0,
                step=100000 if salary_currency == 'KRW' else 100,
                help=t('help_total_debt'),
            )
            debt_interest_rate = st.number_input(
                t('debt_interest_rate'), 0.0, 20.0, 0.0, 0.5,
                help=t('help_debt_rate'),
            )
        with c2:
            retirement_savings = st.number_input(
                t('retirement_savings'), 0, value=0,
                step=100000 if salary_currency == 'KRW' else 100,
                help=t('help_retirement_savings'),
            )
            target_retirement_age = st.number_input(
                t('target_retirement_age'), 30, 80, 60,
                help=t('help_target_age'),
            )
            dependents = st.number_input(t('dependents'), 0, 10, 0)
            c2a, c2b = st.columns(2)
            with c2a:
                has_insurance = st.checkbox(t('has_insurance'))
            with c2b:
                has_pension = st.checkbox(t('has_pension'))

        st.markdown("")
        submitted = st.form_submit_button(t('save_profile'), use_container_width=True, type="primary")

        if submitted:
            if not name.strip():
                st.error(t('error_name_required'))
                return False
            data = DEFAULT_USER_DATA.copy()
            data.update({
                'name': name.strip(), 'age': int(age), 'nationality': nationality,
                'monthly_salary': int(monthly_salary), 'salary_currency': salary_currency,
                'investment_amount': int(investment_amount), 'investment_currency': investment_currency,
                'email': email.strip(),
                'monthly_expenses': int(monthly_expenses),
                'emergency_fund': int(emergency_fund),
                'total_debt': int(total_debt),
                'debt_interest_rate': float(debt_interest_rate),
                'retirement_savings': int(retirement_savings),
                'target_retirement_age': int(target_retirement_age),
                'dependents': int(dependents),
                'has_insurance': has_insurance,
                'has_pension': has_pension,
                'lang': st.session_state.get('lang', 'ko'),
            })
            if save_user_data(data):
                st.session_state.user_data = data
                st.success(t('profile_saved'))
                st.rerun()
            return True
    return False


# ============================================================
# UI: 개인 대시보드
# ============================================================
def render_personal_dashboard(user_data, macro, exchange_rates):
    lang = st.session_state.get('lang', 'ko')
    initials = ''.join([n[0].upper() for n in user_data['name'].split()[:2]]) if user_data['name'] else 'U'
    nat_emoji = {'KR':'🇰🇷','DK':'🇩🇰','US':'🇺🇸'}[user_data['nationality']]
    nat_name = TAX_RULES[user_data['nationality']][f'name_{lang}']

    st.markdown(f"""
    <div class="profile-card">
      <div style="display: flex; align-items: center; gap: 20px;">
        <div class="profile-avatar">{initials}</div>
        <div style="flex: 1;">
          <div style="font-size: 1.5rem; font-weight: 700; color: #000000;">{user_data['name']}</div>
          <div style="color: #57606a; font-size: 0.95rem; margin-top: 4px;">
            {user_data['age']} {t('years_old')} · {nat_name} · {user_data.get('email','')}
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    monthly_salary_usd = convert_amount(user_data['monthly_salary'], user_data['salary_currency'], 'USD', exchange_rates)
    investment_usd = convert_amount(user_data['investment_amount'], user_data['investment_currency'], 'USD', exchange_rates)
    display_curr = user_data['investment_currency']

    st.markdown(f"### {t('financial_overview_section')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        salary_display = convert_amount(monthly_salary_usd, 'USD', display_curr, exchange_rates)
        st.metric(t('monthly_salary'), fmt_money(salary_display, display_curr))
    with c2:
        invest_display = convert_amount(investment_usd, 'USD', display_curr, exchange_rates)
        st.metric(t('invested_assets'), fmt_money(invest_display, display_curr))
    with c3:
        annual_display = convert_amount(monthly_salary_usd * 12, 'USD', display_curr, exchange_rates)
        st.metric(t('annual_salary_label'), fmt_money(annual_display, display_curr))
    with c4:
        debt_usd = convert_amount(user_data.get('total_debt', 0), user_data['salary_currency'], 'USD', exchange_rates)
        debt_display = convert_amount(debt_usd, 'USD', display_curr, exchange_rates)
        st.metric(t('total_debt_label'), fmt_money(debt_display, display_curr))

    # 미래 예측
    st.markdown(f"### {t('wealth_projection_section')}")
    monthly_expenses_usd = convert_amount(
        user_data.get('monthly_expenses', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    monthly_save_usd = max(0, monthly_salary_usd - monthly_expenses_usd)
    if monthly_save_usd == 0:
        monthly_save_usd = monthly_salary_usd * 0.2

    proj_10y = project_wealth(investment_usd, monthly_save_usd, 10, 0.08)
    proj_20y = project_wealth(investment_usd, monthly_save_usd, 20, 0.08)
    gain_10y = proj_10y - investment_usd - (monthly_save_usd * 12 * 10)
    _, _, eff_rate = calculate_tax(gain_10y, user_data['nationality'], 10, exchange_rates)
    net_gain_10y = gain_10y * (1 - eff_rate)
    after_tax_10y = investment_usd + (monthly_save_usd * 12 * 10) + net_gain_10y

    c1, c2, c3 = st.columns(3)
    with c1:
        proj_display = convert_amount(proj_10y, 'USD', display_curr, exchange_rates)
        st.metric(t('after_10y_pretax'), fmt_money(proj_display, display_curr),
                  help=t('projection_assumption'))
    with c2:
        aft_display = convert_amount(after_tax_10y, 'USD', display_curr, exchange_rates)
        st.metric(f"{t('after_10y_aftertax')} - {nat_name.split()[0]})", fmt_money(aft_display, display_curr),
                  f"-{eff_rate*100:.1f}% tax", delta_color="off")
    with c3:
        proj20_display = convert_amount(proj_20y, 'USD', display_curr, exchange_rates)
        st.metric(t('after_20y'), fmt_money(proj20_display, display_curr))

    st.markdown("---")


# ============================================================
# UI: 재무관리 탭 (신규)
# ============================================================
def get_econ_content(country, lang):
    """국가별 경제 분석 콘텐츠 (3개 언어)"""
    content = ECON_CONTENT.get(country, {}).get(lang, {})
    return content


# 국가별 경제 분석 콘텐츠 (정적 데이터)
ECON_CONTENT = {
    'GLOBAL': {
        'ko': {
            'situation': """
**🌍 글로벌 경제 개요 (2026년 현재)**

세계 GDP는 약 110조 달러 규모이며, 미국·중국·EU 3개 권역이 전체의 약 60%를 차지합니다.
COVID-19 이후 본격화된 글로벌 인플레이션은 2024년을 기점으로 안정세에 접어들었고, 
주요국 중앙은행들은 **금리 인하 사이클**에 진입한 상태입니다.

**핵심 동향:**
- **AI 혁명 가속화**: 생성형 AI가 기업 생산성에 본격 반영되며 산업 구조 재편 중
- **에너지 전환**: 태양광/풍력 단가 급락, EV 보급률 글로벌 평균 25% 돌파
- **지정학적 분절화**: 미·중 기술 패권 경쟁, 공급망 재편 가속
- **인구 변화**: 선진국 고령화 vs 인도/아프리카 청년층 증가
- **부채 부담**: 글로벌 부채/GDP 비율 350% 도달 (역사적 최고)

**리스크:**
- 미·중 무역 분쟁 재격화 가능성
- 중동·우크라이나 지정학적 리스크
- 상업용 부동산 부실 (미국, 중국)
- AI 자본 지출 거품 우려
""",
            'stocks': """
**📊 글로벌 주식 시장 현황**

세계 주식 시가총액 약 120조 달러 중 **미국이 60% 이상**을 차지하며 압도적 지배력을 유지합니다.

- **미국 (S&P 500)**: AI 7대장(Magnificent 7)이 시가총액 30%+ 차지
- **유럽 (STOXX 600)**: 럭셔리/제약 강세 (LVMH, Novo Nordisk)
- **일본 (Nikkei)**: 30년 박스 돌파, 기업 지배구조 개혁 효과
- **중국 (Shanghai)**: 부동산 부실 여파로 박스권, 정부 부양책 의존
- **인도 (Sensex)**: 신흥국 중 가장 강세, 청년층 노동력 매력
- **신흥국 전반**: 강달러 부담으로 underperform 지속

**테마별 흐름:**
- 🚀 강세: AI 인프라, 비만치료제(GLP-1), 방산, 우주
- 📉 약세: 상업용 부동산, 전통 자동차, 일부 핀테크
- 🔄 회복: 친환경 에너지 (조정 후 매수 기회)
""",
            'forecast': """
**🔮 글로벌 경제 시나리오**

**단기 (6개월):**
연준의 점진적 금리 인하 → 주식·채권 동반 강세 가능. 단, AI 자본 지출 둔화 시 변동성 확대.
중국 부양책 효과 + 인도 성장 → 신흥국 부분 반등 가능.

**중기 (1~2년):**
AI 생산성 효과가 실제 기업 이익으로 반영되는지가 핵심. 
인플레이션 2% 안착 vs 2차 재반등 가능성 분기점.
미국 대선 후 정책 변화에 따라 무역분쟁 양상 변화.

**장기 (3~5년):**
**3대 메가트렌드**가 시장을 재편할 것으로 예상:
1. **AI 생산성 혁명**: 화이트칼라 직업 30%+ 영향, 새로운 직군 창출
2. **에너지 전환 완료기**: 신재생 발전 비중 50%+ 도달, 전기차 신차 판매 70%+
3. **인구 절벽**: 한국·일본·유럽 노동력 감소, 자동화/이민 정책 압박
""",
            'industries': """
**🚀 향후 5년간 글로벌 유망 산업**

1. **AI 인프라 & 칩** ⭐⭐⭐
   - GPU, AI 가속기, HBM 메모리, 데이터센터
   - 대표주: NVIDIA, TSMC, Broadcom, ASML, SK하이닉스
   - 리스크: 자본 지출 사이클 둔화 가능

2. **비만/당뇨 치료제 (GLP-1)** ⭐⭐⭐
   - 글로벌 비만 인구 10억명+, 시장 $200B 예상
   - 대표주: Novo Nordisk, Eli Lilly
   - 차세대: 알약형, 근육 보존형

3. **사이버보안**
   - AI로 공격·방어 모두 진화, 기업 지출 증가
   - 대표주: CrowdStrike, Palo Alto Networks

4. **소형 모듈 원자로 (SMR)**
   - AI 데이터센터 전력 수요 폭증으로 부각
   - 대표주: Vistra, Constellation Energy

5. **방산/우주**
   - 지정학적 긴장 + 우주 경제 본격화
   - 대표주: Lockheed Martin, RTX, 한화에어로스페이스

6. **로봇/자동화**
   - 휴머노이드 로봇 상용화 단계
   - 대표주: Tesla, ABB, Fanuc

7. **유전자 치료 & 정밀의학**
   - CRISPR 치료제 상용화, 희귀질환 정복
   - 대표주: Vertex, Crispr Therapeutics
""",
        },
        'en': {
            'situation': """
**🌍 Global Economic Overview (2026)**

Global GDP is around $110T, with US, China, and EU accounting for ~60%. 
Inflation that surged after COVID has stabilized since 2024, and major central banks 
are now in a **rate-cutting cycle**.

**Key trends:**
- **AI revolution accelerating**: GenAI driving real productivity gains
- **Energy transition**: Solar/wind costs plummeting, EV share past 25% globally
- **Geopolitical fragmentation**: US-China tech rivalry, supply chain restructuring
- **Demographic shifts**: Aging developed nations vs young India/Africa
- **Debt burden**: Global debt/GDP at 350% (historical high)

**Risks:** US-China trade tensions, Middle East/Ukraine geopolitics, 
commercial real estate stress (US, China), AI capex bubble concerns.
""",
            'stocks': """
**📊 Global Stock Market Snapshot**

Of the ~$120T global market cap, **US dominates with 60%+**.

- **US (S&P 500)**: Magnificent 7 = 30%+ of market cap
- **Europe (STOXX 600)**: Luxury/pharma leading (LVMH, Novo Nordisk)
- **Japan (Nikkei)**: Broke 30-year box, governance reform paying off
- **China (Shanghai)**: Range-bound due to property issues
- **India (Sensex)**: Strongest EM, demographic dividend
- **EM overall**: Underperforming due to strong USD

**Themes:** AI infra, GLP-1, defense, space (strong); commercial RE (weak); renewables (recovery).
""",
            'forecast': """
**🔮 Global Economic Scenarios**

**Short-term (6m):** Gradual Fed rate cuts → simultaneous stock/bond strength likely. 
AI capex slowdown could increase volatility. China stimulus + India growth → EM partial rebound.

**Mid-term (1-2y):** Key question: do AI productivity gains translate to actual earnings? 
Inflation anchored at 2% vs second wave. Post-election US policy shifts affecting trade.

**Long-term (3-5y):** Three mega-trends reshaping markets:
1. AI productivity revolution (30%+ white-collar impact)
2. Energy transition completion (50%+ renewable, 70%+ EV new sales)
3. Demographic cliff (Korea/Japan/Europe labor shrinkage)
""",
            'industries': """
**🚀 Promising Global Industries (5 years)**

1. **AI Infrastructure & Chips** ⭐⭐⭐
   - GPU, AI accelerators, HBM, data centers
   - Leaders: NVIDIA, TSMC, Broadcom, ASML, SK Hynix

2. **Obesity/Diabetes Drugs (GLP-1)** ⭐⭐⭐
   - 1B+ global obese population, $200B market projected
   - Leaders: Novo Nordisk, Eli Lilly

3. **Cybersecurity**
   - AI evolving both attack and defense
   - Leaders: CrowdStrike, Palo Alto Networks

4. **Small Modular Reactors (SMR)**
   - Powering AI data centers
   - Leaders: Vistra, Constellation Energy

5. **Defense/Space**
   - Geopolitical tensions + commercial space economy
   - Leaders: Lockheed Martin, RTX, Hanwha Aerospace

6. **Robotics/Automation**
   - Humanoid robots commercializing
   - Leaders: Tesla, ABB, Fanuc

7. **Gene Therapy & Precision Medicine**
   - CRISPR therapies commercializing
   - Leaders: Vertex, Crispr Therapeutics
""",
        },
        'da': {
            'situation': """
**🌍 Global økonomisk oversigt (2026)**

Global BNP er ca. 110 billioner USD, hvor USA, Kina og EU tegner sig for ~60%. 
Inflationen efter COVID stabiliserede sig fra 2024, og store centralbanker er nu i en **rentenedsættelsescyklus**.

**Hovedtendenser:**
- **AI-revolution accelererer**: GenAI driver produktivitetsstigninger
- **Energiomstilling**: Sol/vind-omkostninger falder, EV-andel over 25% globalt
- **Geopolitisk fragmentering**: USA-Kina tech-rivalisering
- **Demografiske skift**: Aldrende udviklede lande vs unge Indien/Afrika
- **Gældsbyrde**: Global gæld/BNP på 350% (historisk høj)
""",
            'stocks': """
**📊 Globalt aktiemarkedsoverblik**

Af de ~120 billioner USD global markedsværdi dominerer **USA med 60%+**.

- USA (S&P 500): Magnificent 7 = 30%+ af markedsværdi
- Europa (STOXX 600): Luksus/pharma førende (LVMH, Novo Nordisk)
- Japan (Nikkei): Brød 30-årig kasse
- Kina: Range-bound pga. ejendomsproblemer
- Indien: Stærkeste EM
""",
            'forecast': """
**🔮 Globale økonomiske scenarier**

**Kort sigt (6m):** Gradvise Fed-rentenedsættelser → aktier/obligationer styrkelse sandsynlig.

**Mellem sigt (1-2 år):** Centralt: oversætter AI-produktivitet til faktisk indtjening?

**Lang sigt (3-5 år):** Tre mega-trends omformer markeder: AI-produktivitet, energiomstilling, demografisk klif.
""",
            'industries': """
**🚀 Lovende globale industrier (5 år)**

1. **AI infrastruktur & chips** - NVIDIA, TSMC, ASML
2. **Fedme/diabetes-lægemidler (GLP-1)** - Novo Nordisk, Eli Lilly
3. **Cybersikkerhed** - CrowdStrike, Palo Alto
4. **Små modulære reaktorer (SMR)** - Vistra
5. **Forsvar/rumfart** - Lockheed Martin, RTX
6. **Robotik/automatisering** - Tesla, ABB
7. **Genterapi & præcisionsmedicin** - Vertex
""",
        },
    },
    'KR': {
        'ko': {
            'situation': """
**🇰🇷 한국 경제 현황 — 적나라한 진단**

한국은 GDP $1.8조 규모의 세계 12위 경제이지만, **구조적 변곡점**에 직면해 있습니다.

**1. 저성장 고착화**
- 잠재성장률 2% 미만으로 추락 (1990년대 7%+ → 2026년 1.8% 예상)
- 잠재성장률이 인구 감소 + 생산성 정체로 계속 하락 중
- "선진국 함정"에 빠진 상태 — 일본의 1990년대를 닮아감

**2. 가계부채 위기**
- GDP 대비 가계부채 **100%+ (세계 최고 수준)**
- 부동산 가격 정점 후 조정 진행 중 (서울 -15~20%)
- 영끌·빚투 세대의 부담 가중

**3. 인구 절벽**
- 합계출산율 **0.72명 (세계 최저)**
- 2025년부터 인구 감소 본격화
- 생산가능인구 매년 30만명 감소
- 잠재성장률 추가 하락 압력

**4. 반도체 의존성**
- 수출의 20%+ 반도체에 의존
- 미·중 갈등 직격탄 (중국으로 수출 제한)
- 메모리 사이클 변동성 = 한국 경제 변동성

**5. 양극화**
- 대기업 vs 중소기업 임금 격차 확대
- 청년 실업률 7%+ (전체 3% 대비)
- 자영업 폐업률 증가

**한국은행 기준금리:** 3%대 (미국 따라 인하 사이클)
**환율:** 원/달러 1,300~1,400 박스권
**무역수지:** 흑자 지속 (반도체 회복 시)
""",
            'stocks': """
**📈 한국 주식 시장 — 코리아 디스카운트의 진실**

**KOSPI 현황:**
- 지수 시가총액 약 2,200조원
- **삼성전자 + SK하이닉스 = 시장의 30%+** (의존도 비정상적 높음)
- 외국인 비중 30%대
- PER 평균 12배 (미국 22배, 일본 16배 대비 저평가)

**코리아 디스카운트 원인:**
1. **지배구조 문제**: 재벌 총수 일가 중심, 소액주주 권익 보호 부족
2. **낮은 배당성향**: 평균 25% (미국 40%, 일본 35%)
3. **물적분할 / 인적분할 남발**: 모회사 주주 가치 훼손
4. **지정학적 리스크**: 북한, 미·중 갈등
5. **회계 투명성 의심**

**최근 긍정적 변화:**
- 2025년 상법 개정 → 자사주 의무 소각 (Yunsuk님 석사논문 주제!)
- 밸류업 프로그램 (정부 주도)
- 일부 기업 배당 확대

**KOSDAQ 현황:**
- 바이오 + 2차전지 + 게임 중심
- 변동성 매우 큰 시장 (개인투자자 80%)
- 에코프로 등 테마주 거품/붕괴 반복

**주도 섹터 (2026 현재):**
- 🚀 강세: AI 반도체(HBM), 방산, 조선, 일부 K-바이오
- 📉 약세: 화학, 철강, 일부 IT 부품
- 🔄 회복: 자동차 (현대차/기아 미국 시장 점유율 ↑)

**외국인 매매 동향:** AI/반도체 + 방산 중심 매수, 화학/소비재 매도
""",
            'forecast': """
**🔮 한국 경제 흐름 예측**

**단기 (6개월):**
- 미국 금리 인하 → 원화 강세 → 수출 부담 vs 외국인 자금 유입
- 반도체 사이클: HBM은 상승세, 일반 메모리는 회복기
- 부동산 추가 조정 가능성 (PF 부실 등 리스크)
- 11월 미국 대선 이후 무역 정책 변화 주시

**중기 (1~2년):**
- 반도체 신규 증설 효과 본격화 (삼성, SK하이닉스)
- AI 가속기 + HBM 수요 폭증 수혜
- 가계부채 디레버리징 진행 → 내수 부진 지속
- 정부 밸류업 프로그램 효과 미지수 (단기 회의적)

**장기 (3~5년):**
- **구조적 도전**: 인구 감소 본격화로 잠재성장률 1%대 안착
- **새로운 기회**: K-방산 글로벌 점유율 확대, K-바이오 성장
- **변수**: AI/로봇 도입으로 생산성 회복 가능성
- **리스크**: 일본화 (장기 디플레이션 + 자산 가격 하락)
""",
            'industries': """
**🚀 한국 유망 산업 — 향후 5년**

1. **AI 반도체 / HBM** ⭐⭐⭐ (최강 경쟁력)
   - 삼성전자, SK하이닉스가 글로벌 시장의 70%+ 점유
   - NVIDIA, AMD 의 AI GPU에 필수
   - 향후 5년간 수요 폭증 예상
   - **핵심 종목:** 005930.KS (삼성전자), 000660.KS (SK하이닉스)

2. **K-방산** ⭐⭐⭐ (새로운 글로벌 강자)
   - 폴란드·중동·동남아 수주 폭증
   - 가성비 + 빠른 납기 + 기술력
   - **핵심 종목:** 012450.KS (한화에어로스페이스), 047810.KS (한국항공우주), 064350.KS (현대로템)

3. **K-바이오 / 바이오시밀러** ⭐⭐
   - 셀트리온, 삼성바이오로직스 글로벌 위탁생산 강자
   - GLP-1 비만치료제 바이오시밀러 시장 개척 중
   - **핵심 종목:** 207940.KS (삼성바이오로직스), 068270.KS (셀트리온)

4. **2차전지 (회복 가능성)** ⭐⭐
   - 일시 조정 후 EV 보급률 ↑로 중장기 회복 예상
   - LG, 삼성 SDI, SK 온이 글로벌 top 5
   - **핵심 종목:** 373220.KS (LG에너지솔루션), 006400.KS (삼성SDI)

5. **K-원전 / SMR** ⭐⭐
   - 두산에너빌리티가 SMR 글로벌 공급
   - AI 데이터센터 전력 수요 폭증
   - **핵심 종목:** 034020.KS (두산에너빌리티)

6. **로봇 / 자동화** ⭐⭐
   - 인구 감소 + 인건비 상승으로 자동화 필수
   - 휴머노이드 로봇 신성장 동력
   - **핵심 종목:** 두산로보틱스, 레인보우로보틱스

7. **조선 (글로벌 회복)** ⭐⭐
   - LNG선·암모니아선 발주 폭증
   - 한국·중국이 글로벌 90% 점유
   - **핵심 종목:** 329180.KS (HD현대중공업), 267260.KS (HD현대일렉트릭)

8. **K-콘텐츠 / 엔터** ⭐
   - 글로벌 K-팝, 드라마 영향력 지속
   - 단, 변동성 매우 큼
   - **핵심 종목:** 352820.KQ (하이브), 035720.KS (카카오)

**피해야 할 산업:**
- ❌ 전통 화학·철강 (중국 과잉생산)
- ❌ 일부 게임주 (중국 시장 의존)
- ❌ 부동산 PF 관련주
""",
        },
        'en': {
            'situation': """
**🇰🇷 Korea — Frank Diagnosis**

Korea is the world's 12th largest economy ($1.8T GDP), but faces **structural inflection points**.

**1. Stagnant growth**: Potential growth rate below 2% (vs 7%+ in 1990s). "Developed country trap" — resembling Japan's 1990s.

**2. Household debt crisis**: Debt-to-GDP **over 100% (highest globally)**. Real estate post-peak correction underway.

**3. Demographic cliff**: Birth rate **0.72 (world's lowest)**. Working population declining 300K/year.

**4. Semiconductor dependency**: 20%+ of exports. US-China tensions hit Korea hardest.

**5. Polarization**: Chaebol vs SME wage gap widening. Youth unemployment 7%+.

**BOK Rate:** ~3% (following US cuts). **FX:** USD/KRW 1,300-1,400 range.
""",
            'stocks': """
**📈 Korea Stock Market — The "Korea Discount" Truth**

**KOSPI:** Market cap ~$1.6T. **Samsung + SK Hynix = 30%+ of market** (abnormally high concentration). PER 12x vs US 22x.

**Causes of Korea Discount:**
1. Governance issues (chaebol family control)
2. Low dividend payout (25% vs US 40%)
3. Excessive spinoffs hurting minority shareholders
4. Geopolitical risk (NK, US-China)
5. Accounting transparency concerns

**Recent positive changes:**
- 2025 commercial law amendment → mandatory treasury stock retirement (Yunsuk's thesis topic!)
- Government Value-Up Program
- Some companies increasing dividends

**Hot sectors (2026):** AI semis (HBM), defense, shipbuilding, biotech
**Weak:** Chemicals, steel, some IT components
""",
            'forecast': """
**🔮 Korea Economic Forecast**

**Short-term (6m):** US rate cuts → KRW strength → export pressure vs foreign inflows. Semiconductor cycle: HBM up, general memory recovering.

**Mid-term (1-2y):** New semiconductor capacity benefits. AI/HBM demand surge. Household deleveraging continues → domestic demand weak.

**Long-term (3-5y):** Structural challenge from population decline (potential growth ~1%). New opportunities: K-defense global share, K-bio. Risk: Japanification.
""",
            'industries': """
**🚀 Korea — Promising Industries (5 years)**

1. **AI Semiconductors / HBM** ⭐⭐⭐
   - Samsung, SK Hynix dominate 70%+ globally
   - Essential for NVIDIA/AMD AI GPUs
   - **Stocks:** 005930.KS, 000660.KS

2. **K-Defense** ⭐⭐⭐
   - Massive orders from Poland, Middle East
   - Value + fast delivery + quality
   - **Stocks:** 012450.KS, 047810.KS, 064350.KS

3. **K-Bio / Biosimilars** ⭐⭐
   - Celltrion, Samsung Biologics — global CMO leaders
   - **Stocks:** 207940.KS, 068270.KS

4. **Batteries (Recovery)** ⭐⭐
   - LG, Samsung SDI in global top 5
   - **Stocks:** 373220.KS, 006400.KS

5. **K-Nuclear / SMR** ⭐⭐
   - Doosan supplying SMR globally
   - AI data center power demand surge
   - **Stocks:** 034020.KS

6. **Robotics/Automation** ⭐⭐
   - Aging society driving demand
   - **Stocks:** Doosan Robotics, Rainbow Robotics

7. **Shipbuilding** ⭐⭐
   - LNG/Ammonia ship orders surging
   - **Stocks:** 329180.KS, 267260.KS

8. **K-Content/Entertainment** ⭐
   - K-pop, dramas global influence continues
   - **Stocks:** 352820.KQ, 035720.KS
""",
        },
        'da': {
            'situation': """
**🇰🇷 Korea — Ærlig diagnose**

Korea er verdens 12. største økonomi ($1,8T BNP), men står overfor **strukturelle vendepunkter**.

**1. Stagnerende vækst**: Potentiel vækstrate under 2%. "Udviklet lands fælde".

**2. Husholdningsgældskrise**: Gæld-til-BNP **over 100% (højest globalt)**.

**3. Demografisk klif**: Fertilitet **0,72 (verdens laveste)**. Arbejdsstyrke falder 300K/år.

**4. Halvlederafhængighed**: 20%+ af eksport. USA-Kina spændinger rammer Korea hårdest.

**Rente:** ~3%. **Valuta:** USD/KRW 1.300-1.400.
""",
            'stocks': """
**📈 Korea aktiemarked — "Korea Discount" sandheden**

KOSPI: Markedsværdi ~$1,6T. Samsung + SK Hynix = 30%+ af markedet. P/E 12x vs USA 22x.

**Årsager til Korea Discount:** Familiekontrollerede konglomerater, lavt udbytte (25% vs USA 40%), opsplitninger der skader minoritetsaktionærer.

**Positive ændringer 2025:** Obligatorisk indløsning af egne aktier (Yunsuks specialeemne!).

**Stærke sektorer:** AI-halvledere (HBM), forsvar, skibsbygning, biotek.
""",
            'forecast': """
**🔮 Korea økonomisk prognose**

**Kort sigt:** US-rentenedsættelser → KRW-styrke → eksportpres.

**Mellem sigt:** Ny halvlederkapacitet betaler sig. AI/HBM efterspørgsel stiger.

**Lang sigt:** Strukturel udfordring fra befolkningstilbagegang. Nye muligheder: K-forsvar, K-bio. Risiko: Japanisering.
""",
            'industries': """
**🚀 Korea — Lovende industrier (5 år)**

1. **AI-halvledere / HBM** - Samsung, SK Hynix dominerer 70%+ globalt
2. **K-Defense** - Massive ordrer fra Polen, Mellemøsten
3. **K-Bio / Biosimilars** - Celltrion, Samsung Biologics
4. **Batterier (Genopretning)** - LG, Samsung SDI
5. **K-Nuclear / SMR** - Doosan Enerbility
6. **Robotik/Automatisering** - Aldrende samfund driver efterspørgsel
7. **Skibsbygning** - LNG/Ammoniak ordrer stiger
""",
        },
    },
    'US': {
        'ko': {
            'situation': """
**🇺🇸 미국 경제 현황 — 글로벌 패권의 진실**

미국은 GDP $28조의 세계 최대 경제이자, **AI 시대의 새로운 산업혁명**을 주도하고 있습니다.

**1. 압도적 GDP & 생산성**
- 1인당 GDP $85,000+ (선진국 중 최상위)
- AI/소프트웨어 생산성 혁명으로 노동생산성 격차 확대
- 자본 시장이 글로벌 자금의 60%+ 흡수

**2. 강달러 영향**
- DXY (달러 인덱스) 100~105 박스권
- 강달러 = 미국 인플레 억제 + 신흥국 부담
- 기축통화 지위 흔들리지 않음

**3. 노동시장**
- 실업률 4% 내외 (역사적 저점 부근)
- 임금 상승률 4%대 (인플레 압력)
- AI 도입으로 화이트칼라 일자리 변화 시작

**4. 부채 위험**
- 연방정부 부채 $35조+, GDP 대비 120%
- 이자 비용이 국방비 초과
- 장기 재정 지속가능성 의문

**5. 정치적 분열**
- 양극화 심화, 무역 정책 불확실성
- 대선 결과에 따라 글로벌 경제 충격

**연준 기준금리:** 4~5% (점진적 인하 사이클)
**인플레이션:** 2.5~3% (목표 2%에 근접)
**경제 성장:** 2~2.5%
""",
            'stocks': """
**📈 미국 주식 시장 — AI 시대의 황금기?**

**S&P 500 / NASDAQ 현황:**
- 시가총액 약 $50조 (글로벌의 60%)
- **Magnificent 7이 시장의 30%+ 차지**: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
- 시가총액 집중도 역대 최고 → 시장 안정성 우려

**섹터별 동향:**
- 🚀 **테크 (XLK)**: AI 인프라 수혜 지속, 일부 과열
- 🚀 **헬스케어 (XLV)**: Eli Lilly의 GLP-1 폭주, 바이오테크 회복
- 🚀 **방산 (ITA)**: 지정학적 긴장 + 우주 경제
- ⚠️ **상업용 부동산 (VNQ)**: WFH 영향 지속, 일부 부실
- 📉 **에너지 (XLE)**: 신재생 전환으로 장기 압박
- 🔄 **금융 (XLF)**: 금리 인하 사이클에서 회복 기대

**채권 시장:**
- 10년물 국채금리 4~5% 박스권
- 회사채 스프레드 축소 (위험 감수 모드)
- 장단기 금리차 역전 해소 진행

**옵션·파생상품:**
- VIX 평균 15 수준 (낙관 우세)
- 단, 갑작스러운 변동성 확대 가능성 항상 존재

**리스크:**
- AI 자본 지출 거품 우려 (NVIDIA 매출의 50%+ 빅테크 의존)
- 시가총액 집중 → 한 종목 폭락 시 시장 전체 충격
- 부동산·신용 카드 부실 가능성
""",
            'forecast': """
**🔮 미국 경제 흐름 예측**

**단기 (6개월):**
- 연준 금리 인하 가속 → 주식·채권 동반 강세 가능
- AI 4분기 실적이 핵심 관전 포인트
- 대선 후 정책 변화 (관세, 이민, 규제)
- 변동성 확대 가능 (시가총액 집중 리스크)

**중기 (1~2년):**
- AI 생산성 효과가 기업 이익에 본격 반영
- 인플레이션 2% 안착 vs 2차 재상승 가능성
- 노동시장 점진적 둔화 (실업률 4.5~5%로 상승)
- 재정 적자 문제 가시화

**장기 (3~5년):**
- **AI 슈퍼사이클**: 생산성 혁명으로 잠재성장률 상향 가능 (1.8% → 2.5%)
- **달러 패권**: 위협받지만 단기 대체재 부재
- **재정 위기 가능성**: 부채/GDP 130%+ 도달 시 신뢰 위기
- **인구는 강점**: 이민 + 자연증가로 지속 성장
""",
            'industries': """
**🚀 미국 유망 산업 — 향후 5년**

1. **AI 인프라 (반도체 + 데이터센터)** ⭐⭐⭐
   - NVIDIA GPU, AMD MI, Broadcom AI ASIC
   - 데이터센터 REIT (DLR, EQIX)
   - 전력 인프라 (VRT, ETN)
   - **핵심 종목:** NVDA, AMD, AVGO, ANET, VRT

2. **AI 소프트웨어 / 클라우드** ⭐⭐⭐
   - MSFT (Azure + Copilot)
   - GOOGL (Gemini + Cloud)
   - 응용 AI: Palantir, Service Now
   - **핵심 종목:** MSFT, GOOGL, NOW, PLTR

3. **비만 치료제 / GLP-1** ⭐⭐⭐
   - Eli Lilly가 Novo Nordisk와 글로벌 양강
   - 차세대 알약형, 근육 보존형 개발 중
   - **핵심 종목:** LLY, VKTX (신규)

4. **사이버보안** ⭐⭐
   - AI 시대 사이버 공격 급증
   - **핵심 종목:** CRWD, PANW, ZS, OKTA

5. **소형 원자로 (SMR)** ⭐⭐
   - AI 데이터센터 전력 수요 폭증
   - **핵심 종목:** VST, CEG, GEV, OKLO

6. **로봇 / 휴머노이드** ⭐⭐
   - 테슬라 옵티머스, Figure AI
   - **핵심 종목:** TSLA, ABB, IRBT

7. **우주 / 방산** ⭐⭐
   - SpaceX (비상장) + 록히드, RTX
   - **핵심 종목:** LMT, RTX, RKLB, BA

8. **양자 컴퓨팅** ⭐ (초기 단계)
   - IBM, Google, IonQ
   - 5~10년 후 본격 상용화 예상
   - **핵심 종목:** IBM, IONQ, RGTI

9. **유전자 치료** ⭐⭐
   - CRISPR 치료제 FDA 승인 가속
   - **핵심 종목:** VRTX, CRSP, BEAM

**피해야 할 산업:**
- ❌ 상업용 부동산 (특히 오피스)
- ❌ 일부 전통 미디어
- ❌ 신용카드 (부실 우려)
""",
        },
        'en': {
            'situation': """
**🇺🇸 USA — Truth Behind Global Dominance**

US is the world's largest economy at $28T GDP, leading the **new industrial revolution** of the AI era.

**1. Dominant productivity**: GDP/capita $85,000+. AI/software productivity gap widening.

**2. Strong dollar**: DXY 100-105. Reserve currency status intact.

**3. Labor market**: Unemployment ~4%, near historic lows. Wage growth 4%+.

**4. Debt risk**: Federal debt $35T+, 120% of GDP. Interest costs exceed defense spending.

**5. Political fragmentation**: Polarization, trade policy uncertainty.

**Fed rate:** 4-5%. **Inflation:** 2.5-3%. **Growth:** 2-2.5%.
""",
            'stocks': """
**📈 US Stock Market — AI Golden Age?**

S&P 500/NASDAQ: ~$50T market cap (60% of global). **Magnificent 7 = 30%+ of market**.

**Sectors:** Tech (AI infra), Healthcare (GLP-1), Defense (geopolitics) — strong. Commercial RE — weak. Financials — recovery hopes.

**Bonds:** 10Y yield 4-5%. **VIX:** ~15 (optimism).

**Risks:** AI capex bubble, market concentration, real estate/credit card delinquencies.
""",
            'forecast': """
**🔮 US Economic Forecast**

**Short-term (6m):** Fed rate cuts → simultaneous stock/bond strength. AI Q4 earnings critical. Post-election policy shifts.

**Mid-term (1-2y):** AI productivity translating to earnings. Inflation anchoring. Labor market gradual cooling.

**Long-term (3-5y):** AI supercycle could lift potential growth (1.8% → 2.5%). Dollar dominance intact. Fiscal crisis possible at 130%+ debt/GDP.
""",
            'industries': """
**🚀 US — Promising Industries (5 years)**

1. **AI Infrastructure** ⭐⭐⭐ - NVDA, AMD, AVGO, ANET, VRT
2. **AI Software/Cloud** ⭐⭐⭐ - MSFT, GOOGL, NOW, PLTR
3. **GLP-1/Obesity Drugs** ⭐⭐⭐ - LLY, VKTX
4. **Cybersecurity** ⭐⭐ - CRWD, PANW, ZS
5. **Small Modular Reactors** ⭐⭐ - VST, CEG, GEV, OKLO
6. **Robotics/Humanoid** ⭐⭐ - TSLA, ABB
7. **Space/Defense** ⭐⭐ - LMT, RTX, RKLB
8. **Quantum Computing** ⭐ - IBM, IONQ
9. **Gene Therapy** ⭐⭐ - VRTX, CRSP, BEAM
""",
        },
        'da': {
            'situation': """
**🇺🇸 USA — Sandheden bag global dominans**

USA er verdens største økonomi med $28T BNP, og fører den **nye industrielle revolution** i AI-alderen.

**1. Dominerende produktivitet**: BNP/indbygger $85.000+.
**2. Stærk dollar**: DXY 100-105.
**3. Arbejdsmarked**: Arbejdsløshed ~4%.
**4. Gældsrisiko**: Føderal gæld $35T+, 120% af BNP.
**5. Politisk fragmentering**.

**Fed-rente:** 4-5%. **Inflation:** 2,5-3%. **Vækst:** 2-2,5%.
""",
            'stocks': """
**📈 USA aktiemarked — AI's guldalder?**

S&P 500/NASDAQ: ~$50T markedsværdi (60% af globalt). **Magnificent 7 = 30%+ af markedet**.

**Sektorer:** Tech, Sundhed, Forsvar — stærke. Kommerciel ejendom — svag.
""",
            'forecast': """
**🔮 USA økonomisk prognose**

**Kort sigt:** Fed-rentenedsættelser → aktier/obligationer styrkelse.

**Mellem sigt:** AI-produktivitet oversættes til indtjening.

**Lang sigt:** AI-supercyklus kan løfte vækstpotentialet (1,8% → 2,5%).
""",
            'industries': """
**🚀 USA — Lovende industrier (5 år)**

1. **AI Infrastruktur** - NVDA, AMD, AVGO
2. **AI Software/Cloud** - MSFT, GOOGL
3. **GLP-1/Fedme-lægemidler** - LLY
4. **Cybersikkerhed** - CRWD, PANW
5. **Små modulære reaktorer** - VST, CEG
6. **Robotik/Humanoide** - TSLA, ABB
7. **Rumfart/Forsvar** - LMT, RTX
""",
        },
    },
    'DK': {
        'ko': {
            'situation': """
**🇩🇰 덴마크 경제 현황 — 작지만 강한 북유럽 강국**

덴마크는 인구 590만명, GDP $4,000억 규모의 **세계 1인당 GDP 톱 10** 국가입니다.

**1. 복지국가 모델의 성공**
- 1인당 GDP $68,000+
- 높은 세금 (소득세 최고 55%) + 보편적 복지
- 행복지수 세계 top 3 단골
- 노동시장 유연성 + 강한 사회 안전망 ("Flexicurity")

**2. 산업 구조의 특수성**
- **Novo Nordisk가 GDP의 5%+** (한 회사 의존도 비정상)
- 풍력 에너지 글로벌 리더 (Ørsted, Vestas)
- 해운 (Mærsk) + 양조 (Carlsberg)
- 제약·헬스케어 강세

**3. EU 회원국이지만 유로존 미가입**
- 자체 통화 (DKK) 유지
- 단, DKK는 유로에 사실상 페그 (변동성 매우 낮음)
- 통화 정책 독립성 + EU 시장 접근의 이점

**4. 친환경/지속가능성 리더**
- 2030년까지 전력 100% 재생에너지 목표 (이미 70%+)
- 해상풍력 글로벌 점유율 압도적
- ESG 투자 자금이 덴마크 시장에 꾸준히 유입

**5. 안정성**
- 정부 부채 / GDP 30%대 (매우 건전)
- 무역수지 흑자 지속
- 외환보유고 충분
- 인구 안정 (이민으로 보완)

**중앙은행 정책 금리:** 2~3% (ECB 따라 움직임)
**환율 (USD/DKK):** 6.5~7.5
**인플레이션:** 2% 안착
""",
            'stocks': """
**📈 덴마크 주식 시장 — Novo Nordisk 의존성의 양날의 검**

**OMX Copenhagen 25 현황:**
- 25개 종목으로 구성된 작은 시장
- **Novo Nordisk가 지수의 30%+ 차지** (의존도 매우 높음)
- 평균 배당수익률 2~3% (안정적)
- ESG 투자 자금 유입 활발

**핵심 종목 분석:**

🌟 **Novo Nordisk (NOVO-B.CO)** — 시가총액 €500B+
- 비만/당뇨 치료제(GLP-1) 글로벌 1위
- Wegovy, Ozempic 글로벌 폭발적 수요
- 리스크: 미국 GLP-1 경쟁사(Eli Lilly), 약가 압박

🌪️ **Ørsted (ORSTED.CO)** — 해상풍력 글로벌 1위
- 미국 풍력 프로젝트 손실 후 회복기
- 장기적 친환경 전환 수혜

🏗️ **Vestas (VWS.CO)** — 풍력 터빈 글로벌 톱
- 자재비 안정화 + 신규 수주 증가
- 미국 IRA 보조금 수혜

🚢 **Mærsk (MAERSK-B.CO)** — 글로벌 해운 2위
- 운임 변동성 크지만 친환경 선박 전환 주도
- 홍해 사태 영향 회복

🍺 **Carlsberg (CARL-B.CO)** — 글로벌 맥주 4위
- 안정적 배당주 + 신흥국 성장

🧬 **Genmab (GMAB.CO)** — 항체 의약품
- Darzalex 로열티 + 신약 파이프라인

**섹터 비중:**
- 헬스케어: 40%+ (Novo Nordisk 영향)
- 산업재 (해운, 풍력): 25%
- 금융: 15%
- 소비재: 10%
- 기타: 10%

**리스크:**
- Novo Nordisk 한 종목 의존 → 분산 필수
- 시장 규모 작아 유동성 낮음
- 외국인 자금 유출입에 민감
""",
            'forecast': """
**🔮 덴마크 경제 흐름 예측**

**단기 (6개월):**
- ECB 금리 인하 → DKK 약세 가능 → 수출 유리
- Novo Nordisk 신약 데이터 발표가 시장 좌우
- 해운 운임 추이 (Mærsk)
- 풍력 발전 신규 수주 (Ørsted, Vestas)

**중기 (1~2년):**
- GLP-1 시장 성숙기 진입 → Novo Nordisk 성장률 둔화 우려
- 친환경 에너지 전환 본격화 → Ørsted/Vestas 수혜
- EU 경기 회복 시 산업재 강세 가능
- 미국 대선 후 풍력 정책 변화 주시 (IRA 영향)

**장기 (3~5년):**
- **글로벌 비만 인구 증가**: 10억명+ → Novo Nordisk 장기 성장
- **해상풍력 본격 상용화**: 덴마크 기업들이 글로벌 표준 주도
- **지속가능성 프리미엄**: ESG 자금 유입 지속
- **인구 변화**: 이민 정책으로 안정적 성장 유지
""",
            'industries': """
**🚀 덴마크 유망 산업 — 향후 5년**

1. **비만/당뇨 치료제 (GLP-1)** ⭐⭐⭐ (글로벌 1위)
   - Novo Nordisk가 시장 점유율 55%+
   - 차세대 신약 (CagriSema 등) 파이프라인 풍부
   - **핵심 종목:** NOVO-B.CO

2. **해상풍력** ⭐⭐⭐ (글로벌 표준)
   - Ørsted: 운영 및 개발 글로벌 1위
   - Vestas: 터빈 제조 글로벌 톱
   - **핵심 종목:** ORSTED.CO, VWS.CO

3. **친환경 해운** ⭐⭐⭐
   - Mærsk가 메탄올 추진 컨테이너선 선도
   - 2050년 탄소 중립 목표
   - **핵심 종목:** MAERSK-B.CO

4. **바이오테크 / 정밀의학** ⭐⭐
   - Genmab의 항체 의약품 플랫폼
   - Bavarian Nordic 백신 (몽키두 등)
   - Lundbeck 신경과학
   - **핵심 종목:** GMAB.CO, BAVA.CO, LUN.CO

5. **의료기기** ⭐⭐
   - Coloplast (스토마 등 헬스케어)
   - Demant, GN Store Nord (보청기)
   - Ambu (1회용 내시경)
   - **핵심 종목:** COLO-B.CO, DEMANT.CO, AMBU-B.CO

6. **물류 & 공급망 기술** ⭐⭐
   - DSV: 글로벌 물류 공룡
   - 인수합병 통한 확장
   - **핵심 종목:** DSV.CO

7. **건축 자재 (지속가능)** ⭐
   - Rockwool: 단열재 글로벌 톱
   - 친환경 건축 트렌드 수혜
   - **핵심 종목:** ROCK-B.CO

8. **금융 IT** ⭐
   - SimCorp: 자산운용 소프트웨어
   - Netcompany: 디지털 트랜스포메이션
   - **핵심 종목:** SIM.CO, NETC.CO

9. **양조 & 식음료** ⭐
   - Carlsberg: 신흥국 성장
   - **핵심 종목:** CARL-B.CO

**덴마크 투자의 매력:**
- ✅ 정치/경제 안정성 매우 높음
- ✅ ESG 우수 기업 다수
- ✅ 글로벌 시장 점유 기업 보유
- ⚠️ Novo Nordisk 한 종목 의존 → 분산 필수
- ⚠️ 시장 규모 작아 유동성 제약
""",
        },
        'en': {
            'situation': """
**🇩🇰 Denmark — Small but Mighty Nordic Power**

Denmark: 5.9M population, $400B GDP, **top 10 GDP per capita globally**.

**1. Welfare state success**: GDP/capita $68,000+. High taxes (55% max) + universal welfare. World happiness top 3.

**2. Industrial concentration**: **Novo Nordisk = 5%+ of GDP** (unusual concentration). Wind energy (Ørsted, Vestas), shipping (Mærsk), brewing (Carlsberg).

**3. EU but not Eurozone**: Own currency (DKK), pegged to EUR. Monetary independence + EU access.

**4. Green leader**: 70%+ renewable electricity, targeting 100% by 2030. Global offshore wind dominance.

**5. Stability**: Govt debt/GDP ~30%. Trade surplus persistent. Demographic stability via immigration.

**Central bank rate:** 2-3%. **FX (USD/DKK):** 6.5-7.5. **Inflation:** 2%.
""",
            'stocks': """
**📈 Denmark Stock Market — Novo Nordisk Double-Edged Sword**

OMX C25: 25 stocks. **Novo Nordisk = 30%+ of index**. Avg dividend yield 2-3%.

**Key stocks:**
- 🌟 **Novo Nordisk**: Global #1 GLP-1, market cap €500B+
- 🌪️ **Ørsted**: World #1 offshore wind (recovery from US losses)
- 🏗️ **Vestas**: Top wind turbine manufacturer
- 🚢 **Mærsk**: World #2 shipping
- 🍺 **Carlsberg**: Stable dividend, EM growth
- 🧬 **Genmab**: Antibody drugs

**Sector weights:** Healthcare 40%+ (Novo dominance), Industrials 25%, Financials 15%.

**Risk:** Concentration in Novo Nordisk requires diversification.
""",
            'forecast': """
**🔮 Denmark Economic Forecast**

**Short-term (6m):** ECB cuts → DKK weakness possible. Novo Nordisk drug data critical. Shipping rates, wind orders.

**Mid-term (1-2y):** GLP-1 market maturing. Green energy transition benefits. EU recovery boosts industrials.

**Long-term (3-5y):** Global obesity epidemic = Novo long-term growth. Offshore wind commercialization. ESG premium continues.
""",
            'industries': """
**🚀 Denmark — Promising Industries (5 years)**

1. **GLP-1/Obesity Drugs** ⭐⭐⭐ (Global #1)
   - Novo Nordisk 55%+ market share
   - **Stocks:** NOVO-B.CO

2. **Offshore Wind** ⭐⭐⭐ (Global Standard)
   - **Stocks:** ORSTED.CO, VWS.CO

3. **Green Shipping** ⭐⭐⭐
   - **Stocks:** MAERSK-B.CO

4. **Biotech / Precision Medicine** ⭐⭐
   - **Stocks:** GMAB.CO, BAVA.CO, LUN.CO

5. **Medical Devices** ⭐⭐
   - **Stocks:** COLO-B.CO, DEMANT.CO, AMBU-B.CO

6. **Logistics & Supply Chain Tech** ⭐⭐
   - **Stocks:** DSV.CO

7. **Sustainable Building Materials** ⭐
   - **Stocks:** ROCK-B.CO

8. **Financial IT** ⭐
   - **Stocks:** SIM.CO, NETC.CO

**Denmark investment appeal:** High stability, ESG leaders, global market share. Caveat: Novo concentration.
""",
        },
        'da': {
            'situation': """
**🇩🇰 Danmark — Lille men mægtig nordisk magt**

Danmark: 5,9M befolkning, $400B BNP, **top 10 BNP pr. indbygger globalt**.

**1. Velfærdsstats-succes**: BNP/indbygger $68.000+. Høje skatter (55% max) + universel velfærd. World happiness top 3.

**2. Industriel koncentration**: **Novo Nordisk = 5%+ af BNP** (usædvanlig koncentration). Vindenergi (Ørsted, Vestas), shipping (Mærsk), bryggeri (Carlsberg).

**3. EU men ikke Eurozone**: Egen valuta (DKK), bundet til EUR.

**4. Grønt lederskab**: 70%+ vedvarende elektricitet, mål 100% i 2030.

**5. Stabilitet**: Statsgæld/BNP ~30%. Handelsoverskud.

**Centralbankrente:** 2-3%. **Valuta (USD/DKK):** 6,5-7,5. **Inflation:** 2%.
""",
            'stocks': """
**📈 Danmarks aktiemarked — Novo Nordisks dobbelt-eddet sværd**

OMX C25: 25 aktier. **Novo Nordisk = 30%+ af indekset**. Gns. udbytte 2-3%.

**Nøgleaktier:**
- 🌟 **Novo Nordisk**: Global #1 GLP-1
- 🌪️ **Ørsted**: Verden #1 offshore vind
- 🏗️ **Vestas**: Top vindmølleproducent
- 🚢 **Mærsk**: Verden #2 shipping
- 🍺 **Carlsberg**: Stabil udbytteaktie
- 🧬 **Genmab**: Antistof-lægemidler

**Risiko:** Koncentration i Novo Nordisk kræver diversifikation.
""",
            'forecast': """
**🔮 Danmark økonomisk prognose**

**Kort sigt:** ECB-nedsættelser → DKK-svaghed muligt.

**Mellem sigt:** GLP-1 markedet modnes. Grøn energi-overgang gavner.

**Lang sigt:** Global fedme = Novo's langsigtede vækst. Offshore vind kommercialisering. ESG-præmie fortsætter.
""",
            'industries': """
**🚀 Danmark — Lovende industrier (5 år)**

1. **GLP-1/Fedme-lægemidler** ⭐⭐⭐ - NOVO-B.CO
2. **Offshore vind** ⭐⭐⭐ - ORSTED.CO, VWS.CO
3. **Grøn shipping** ⭐⭐⭐ - MAERSK-B.CO
4. **Biotek / Præcisionsmedicin** ⭐⭐ - GMAB.CO, BAVA.CO, LUN.CO
5. **Medicinsk udstyr** ⭐⭐ - COLO-B.CO, DEMANT.CO, AMBU-B.CO
6. **Logistik & forsyningskæde-tech** ⭐⭐ - DSV.CO
7. **Bæredygtige byggematerialer** ⭐ - ROCK-B.CO
8. **Finansiel IT** ⭐ - SIM.CO, NETC.CO

**Danmark investeringsappel:** Høj stabilitet, ESG-ledere. Forbehold: Novo-koncentration.
""",
        },
    },
}


def render_econ_forum_tab(macro, sectors, exchange_rates):
    """경제 포럼 탭 - 국가별 상세 경제 분석"""
    lang = st.session_state.get('lang', 'ko')

    st.markdown(f"## {t('econ_forum_title')}")
    st.caption(t('econ_forum_subtitle'))
    st.markdown(t('no_predict_disclaimer'))
    st.markdown("---")

    # 국가 선택 탭
    country_tabs = st.tabs([
        t('econ_global'),
        t('econ_korea'),
        t('econ_usa'),
        t('econ_denmark'),
    ])

    country_keys = ['GLOBAL', 'KR', 'US', 'DK']

    for i, country in enumerate(country_keys):
        with country_tabs[i]:
            content = get_econ_content(country, lang)
            if not content:
                st.warning(f"Content not yet available for {country} in {lang}")
                continue

            # 매크로 메트릭 (실시간 데이터)
            if country == 'KR':
                c1, c2, c3, c4 = st.columns(4)
                kospi = macro.get('^KS11', {})
                kosdaq = macro.get('^KQ11', {})
                krw = macro.get('KRW=X', {})
                c1.metric("KOSPI (1Y)", f"{kospi.get('1y_change', 0):+.1f}%")
                c2.metric("KOSDAQ (1Y)", f"{kosdaq.get('1y_change', 0):+.1f}%")
                c3.metric("KOSPI 1M", f"{kospi.get('1m_change', 0):+.1f}%")
                c4.metric("USD/KRW (1M)", f"{krw.get('1m_change', 0):+.1f}%")
            elif country == 'US':
                c1, c2, c3, c4 = st.columns(4)
                spy = macro.get('SPY', {})
                nasdaq = macro.get('^IXIC', {})
                tnx = macro.get('^TNX', {})
                vix = macro.get('^VIX', {})
                c1.metric("S&P 500 (1Y)", f"{spy.get('1y_change', 0):+.1f}%")
                c2.metric("NASDAQ (1Y)", f"{nasdaq.get('1y_change', 0):+.1f}%")
                c3.metric("US 10Y", f"{tnx.get('current', 0):.2f}%")
                c4.metric("VIX", f"{vix.get('current', 0):.1f}")
            elif country == 'DK':
                c1, c2, c3 = st.columns(3)
                omxc = macro.get('^OMXC25', {})
                dkk = macro.get('DKK=X', {})
                c1.metric("OMX C25 (1Y)", f"{omxc.get('1y_change', 0):+.1f}%")
                c2.metric("OMX C25 (1M)", f"{omxc.get('1m_change', 0):+.1f}%")
                c3.metric("USD/DKK (1M)", f"{dkk.get('1m_change', 0):+.1f}%")
            else:  # GLOBAL
                c1, c2, c3, c4 = st.columns(4)
                spy = macro.get('SPY', {})
                kospi = macro.get('^KS11', {})
                omxc = macro.get('^OMXC25', {})
                vix = macro.get('^VIX', {})
                c1.metric("S&P 500", f"{spy.get('1y_change', 0):+.1f}%")
                c2.metric("KOSPI", f"{kospi.get('1y_change', 0):+.1f}%")
                c3.metric("OMX C25", f"{omxc.get('1y_change', 0):+.1f}%")
                c4.metric("VIX", f"{vix.get('current', 0):.1f}")

            st.markdown("---")

            # 4가지 섹션
            st.markdown(f"### {t('econ_section_situation')}")
            st.markdown(content.get('situation', ''))

            st.markdown("---")
            st.markdown(f"### {t('econ_section_stocks')}")
            st.markdown(content.get('stocks', ''))

            st.markdown("---")
            st.markdown(f"### {t('econ_section_forecast')}")
            st.markdown(content.get('forecast', ''))

            st.markdown("---")
            st.markdown(f"### {t('econ_section_industries')}")
            st.markdown(content.get('industries', ''))


def render_goal_tab(user_data, stock_df, macro, exchange_rates):
    """재무 목표 달성 플래너 탭"""
    lang = st.session_state.get('lang', 'ko')
    display_curr = user_data['investment_currency']

    st.markdown(f"## {t('goal_planner_title')}")
    st.caption(t('goal_planner_subtitle'))
    st.markdown("---")

    # ──────────────────────────────────────────────────────
    # STEP 1: 목표 입력
    # ──────────────────────────────────────────────────────
    st.markdown(f"### {t('goal_step1')}")

    purpose_options = {
        'house': t('purpose_house'),
        'retirement': t('purpose_retirement'),
        'education': t('purpose_education'),
        'marriage': t('purpose_marriage'),
        'car': t('purpose_car'),
        'freedom': t('purpose_freedom'),
        'other': t('purpose_other'),
    }

    with st.form("goal_form"):
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            current_amount = user_data.get('goal_amount', 0)
            if current_amount == 0:
                # 통화별 기본값
                default_goal = {'USD': 500000, 'KRW': 500000000, 'DKK': 3500000}[display_curr]
            else:
                default_goal = current_amount
            goal_amount = st.number_input(
                t('goal_amount_label'),
                min_value=0,
                value=int(default_goal),
                step=10000 if display_curr in ['USD', 'DKK'] else 10000000,
            )
        with c2:
            goal_years = st.number_input(
                t('goal_years_label'),
                min_value=1, max_value=50,
                value=user_data.get('goal_years', 10),
            )
        with c3:
            current_purpose = user_data.get('goal_purpose', 'house')
            goal_purpose = st.selectbox(
                t('goal_purpose_label'),
                options=list(purpose_options.keys()),
                format_func=lambda x: purpose_options[x],
                index=list(purpose_options.keys()).index(current_purpose) if current_purpose in purpose_options else 0,
            )

        submitted = st.form_submit_button(t('save_goal_btn'), use_container_width=True, type="primary")
        if submitted:
            user_data['goal_amount'] = int(goal_amount)
            user_data['goal_currency'] = display_curr
            user_data['goal_years'] = int(goal_years)
            user_data['goal_purpose'] = goal_purpose
            save_user_data(user_data)
            st.session_state.user_data = user_data
            st.success(t('goal_saved'))
            st.rerun()

    # 목표 미설정 시 종료
    if user_data.get('goal_amount', 0) == 0:
        st.info(t('no_goal_yet'))
        return

    # 목표 요약 카드
    goal_amount = user_data['goal_amount']
    goal_currency = user_data.get('goal_currency', display_curr)
    goal_years = user_data['goal_years']
    goal_purpose = user_data['goal_purpose']

    # USD 환산
    goal_usd = convert_amount(goal_amount, goal_currency, 'USD', exchange_rates)
    current_invest_usd = convert_amount(
        user_data['investment_amount'], user_data['investment_currency'], 'USD', exchange_rates
    )
    monthly_salary_usd = convert_amount(
        user_data['monthly_salary'], user_data['salary_currency'], 'USD', exchange_rates
    )
    monthly_expenses_usd = convert_amount(
        user_data.get('monthly_expenses', 0), user_data['salary_currency'], 'USD', exchange_rates
    )
    monthly_save_usd = max(0, monthly_salary_usd - monthly_expenses_usd)
    if monthly_save_usd == 0:
        monthly_save_usd = monthly_salary_usd * 0.2

    st.markdown("---")

    # ──────────────────────────────────────────────────────
    # STEP 2: 진단
    # ──────────────────────────────────────────────────────
    st.markdown(f"### {t('goal_step2')}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        goal_display = convert_amount(goal_usd, 'USD', display_curr, exchange_rates)
        st.metric("🎯 " + t('goal_amount_label').replace('?', ''), fmt_money(goal_display, display_curr))
    with c2:
        st.metric("⏰ " + t('until_goal'), f"{goal_years} {t('years')}")
    with c3:
        invest_display = convert_amount(current_invest_usd, 'USD', display_curr, exchange_rates)
        st.metric(t('diag_current_assets'), fmt_money(invest_display, display_curr))
    with c4:
        save_display = convert_amount(monthly_save_usd, 'USD', display_curr, exchange_rates)
        st.metric(t('diag_monthly_save'), fmt_money(save_display, display_curr) + '/mo')

    # 단순 예금 (3%) 계산
    simple_fv = project_wealth(current_invest_usd, monthly_save_usd, goal_years, 0.03)
    required_return = calculate_required_return(current_invest_usd, monthly_save_usd, goal_years, goal_usd)

    c1, c2 = st.columns(2)
    with c1:
        simple_display = convert_amount(simple_fv, 'USD', display_curr, exchange_rates)
        gap = simple_fv - goal_usd
        gap_display = convert_amount(abs(gap), 'USD', display_curr, exchange_rates)
        if gap >= 0:
            st.success(f"**{t('diag_simple_savings_label')}**: {fmt_money(simple_display, display_curr)} ✅\n\n{t('savings_only_achieve')}")
        else:
            st.warning(f"**{t('diag_simple_savings_label')}**: {fmt_money(simple_display, display_curr)}\n\n{t('shortage_label')}: {fmt_money(gap_display, display_curr)}")
    with c2:
        if required_return < 0.05:
            label = t('diag_achievable')
            color = "success"
            note = t('diag_note_savings_ok')
        elif required_return < 0.10:
            label = t('diag_difficult')
            color = "info"
            note = t('diag_note_invest_needed')
        elif required_return < 0.20:
            label = t('diag_difficult')
            color = "warning"
            note = t('diag_note_aggressive_needed')
        else:
            label = t('diag_impossible')
            color = "error"
            note = t('diag_note_impossible_text')

        msg = f"**{t('diag_required_return')}: {required_return*100:.1f}%**\n\n{label} — {note}"
        if color == "success":
            st.success(msg)
        elif color == "warning":
            st.warning(msg)
        elif color == "error":
            st.error(msg)
        else:
            st.info(msg)

    # 해결책 (수익률이 너무 높을 때)
    if required_return >= 0.10:
        st.markdown(f"#### {t('diag_solutions_header')}")
        # 1. 월 적립 늘리기
        target_return = 0.07
        # 역산: 7% 수익률로 목표 달성하려면 월 얼마?
        # FV = PV*(1+r)^n + PMT * (((1+r)^n - 1) / r)
        # 풀이: PMT = (FV - PV*(1+r)^n) * r / ((1+r)^n - 1)
        months = goal_years * 12
        monthly_r = target_return / 12
        if monthly_r > 0:
            future_pv = current_invest_usd * ((1 + monthly_r) ** months)
            required_monthly = (goal_usd - future_pv) * monthly_r / (((1 + monthly_r) ** months) - 1)
        else:
            required_monthly = (goal_usd - current_invest_usd) / months

        # 2. 기간 늘리기 (7% 가정)
        years_needed = goal_years
        for try_years in range(goal_years, 50):
            fv = project_wealth(current_invest_usd, monthly_save_usd, try_years, 0.07)
            if fv >= goal_usd:
                years_needed = try_years
                break

        c1, c2, c3 = st.columns(3)
        with c1:
            req_monthly_display = convert_amount(max(0, required_monthly), 'USD', display_curr, exchange_rates)
            current_save_display = convert_amount(monthly_save_usd, 'USD', display_curr, exchange_rates)
            st.info(f"**{t('diag_increase_monthly')}**\n\n"
                   f"{t('diag_current_label')}: {fmt_money(current_save_display, display_curr)}{t('goal_at_pretax')}\n\n"
                   f"{t('diag_needed_label')}: {fmt_money(req_monthly_display, display_curr)}{t('goal_at_pretax')}\n\n"
                   f"{t('diag_assumed_7pct')}")
        with c2:
            st.info(f"**{t('diag_extend_years')}**\n\n"
                   f"{t('diag_current_goal')}: {goal_years} {t('years')}\n\n"
                   f"{t('diag_assumed_7pct')}: {years_needed} {t('years')}\n\n"
                   f"+{years_needed - goal_years} {t('years')}")
        with c3:
            st.info(f"**{t('diag_increase_return')}**\n\n"
                   f"{t('diag_required_return_short')}: {required_return*100:.1f}%\n\n"
                   f"{t('diag_review_aggressive')}\n\n"
                   f"{t('diag_risk_warning')}")

    st.markdown("---")

    # ──────────────────────────────────────────────────────
    # STEP 3: 3가지 시나리오 비교
    # ──────────────────────────────────────────────────────
    st.markdown(f"### {t('goal_step3')}")

    purpose_rec = get_purpose_recommendation(goal_purpose, goal_years)
    recommended_key = purpose_rec['recommended']
    scenario_name_map = {
        'conservative': t('risk_low'),
        'moderate':     t('risk_mid'),
        'aggressive':   t('risk_high'),
    }
    st.info(f"**{t('recommended_for_you')}: {scenario_name_map[recommended_key]}**\n\n{purpose_rec[f'note_{lang}']}")

    scenarios = project_goal_scenarios(current_invest_usd, monthly_save_usd, goal_years, goal_usd)

    cols = st.columns(3)
    scenario_labels = {
        'conservative': ('🛡️', t('risk_low'), '#1a7f37'),
        'moderate':     ('⚖️', t('risk_mid'), '#0969da'),
        'aggressive':   ('🚀', t('risk_high'), '#cf222e'),
    }

    for i, key in enumerate(['conservative', 'moderate', 'aggressive']):
        with cols[i]:
            emoji, label, color = scenario_labels[key]
            sc = scenarios[key]

            is_recommended = (key == recommended_key)
            border = '3px solid #1a7f37' if is_recommended else '1px solid #d0d7de'
            recommended_badge = t('recommended_badge') if is_recommended else ''

            with st.container():
                st.markdown(f"""
                <div style="border: {border}; border-radius: 10px; padding: 16px; background: #f6f8fa;">
                  <div style="color: {color}; font-weight: 700; font-size: 1.2rem;">{emoji} {label}</div>
                  <div style="color: #1a7f37; font-size: 0.85rem; font-weight: 600;">{recommended_badge}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("")
                st.metric(t('expected_return_label'), f"{sc['expected_return']*100:.1f}%")
                exp_display = convert_amount(sc['expected_fv'], 'USD', display_curr, exchange_rates)
                st.metric(t('scenario_expected'), fmt_money(exp_display, display_curr))

                gap = sc['gap_to_target']
                gap_display = convert_amount(abs(gap), 'USD', display_curr, exchange_rates)
                if gap >= 0:
                    st.metric(t('scenario_gap'), f"+{fmt_money(gap_display, display_curr)} ✅")
                else:
                    st.metric(t('scenario_gap'), f"-{fmt_money(gap_display, display_curr)} ❌")

                with st.expander(t('details_btn')):
                    worst_display = convert_amount(sc['worst_fv'], 'USD', display_curr, exchange_rates)
                    best_display = convert_amount(sc['best_fv'], 'USD', display_curr, exchange_rates)
                    st.markdown(f"**{t('scenario_worst_case')}**: {fmt_money(worst_display, display_curr)}")
                    st.markdown(f"**{t('scenario_best_case')}**: {fmt_money(best_display, display_curr)}")
                    st.markdown(f"**{t('scenario_volatility')}**: ±{sc['volatility']*100:.1f}%/yr")
                    st.markdown(f"**{t('scenario_mdd_warn')}**: {sc['mdd']*100:.1f}%")

    st.markdown("---")

    # ──────────────────────────────────────────────────────
    # STEP 4: 구체적 포트폴리오
    # ──────────────────────────────────────────────────────
    st.markdown(f"### {t('goal_step4')}")

    c1, c2, c3 = st.columns(3)
    with c1:
        selected_scenario = st.selectbox(
            t('select_scenario'),
            options=['conservative', 'moderate', 'aggressive'],
            format_func=lambda x: scenario_name_map.get(x, x),
            index=['conservative', 'moderate', 'aggressive'].index(
                user_data.get('selected_scenario', recommended_key)
                if user_data.get('selected_scenario') in ['conservative','moderate','aggressive']
                else recommended_key
            ),
        )
    with c2:
        etf_region = st.selectbox(
            t('etf_region_label'),
            options=['US', 'KR'],
            format_func=lambda x: t('etf_region_us') if x == 'US' else t('etf_region_kr'),
            index=0 if user_data.get('preferred_etf_region', 'US') == 'US' else 1,
        )
    with c3:
        core_pct = st.slider(
            t('core_satellite_ratio'),
            10, 50, 35, 5,
            help="Core (ETF) 비율. 나머지는 개별주(Satellite). 사용자 선택: 개별주 60~70%",
        )
        core_weight = core_pct / 100
        satellite_weight = 1 - core_weight

    # 저장
    if (selected_scenario != user_data.get('selected_scenario')
        or etf_region != user_data.get('preferred_etf_region')):
        user_data['selected_scenario'] = selected_scenario
        user_data['preferred_etf_region'] = etf_region
        save_user_data(user_data)
        st.session_state.user_data = user_data

    # 종목 분석 안 됐으면 안내
    if stock_df is None or stock_df.empty:
        st.warning(t('no_stock_screening_yet'))
        # ETF만 보여주기
        core_only = build_core_portfolio(selected_scenario, 1.0, etf_region)
        etf_pool = ETF_US if etf_region == 'US' else ETF_KR
        rows = []
        for ticker, weight in core_only.items():
            info = etf_pool.get(ticker, {})
            rows.append({
                'Ticker': ticker,
                'Name': info.get('name', ticker),
                'Type': 'CORE (ETF)',
                'Weight': f"{weight*100:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    # Satellite 종목 선정 (스크리닝 상위 8개)
    n_satellite = 8
    satellite_tickers = stock_df.head(n_satellite)['ticker'].tolist()
    stock_info_map = stock_df.set_index('ticker').to_dict('index')

    # 통합 포트폴리오 빌드
    portfolio_df = build_full_portfolio(
        selected_scenario, core_weight, etf_region,
        satellite_tickers, stock_info_map
    )

    # 시각화 - Core vs Satellite 도넛
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("##### Core vs Satellite")
        fig = go.Figure(data=[go.Pie(
            labels=[t('core_label'), t('satellite_label')],
            values=[core_weight, satellite_weight],
            hole=0.5,
            marker=dict(colors=['#0969da', '#cf222e']),
            textfont=dict(color='white', size=14),
        )])
        fig.update_layout(
            height=300, paper_bgcolor='white',
            font=dict(color='#000000'), margin=dict(l=10,r=10,t=10,b=10),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown(f"##### {t('stocks_by_weight')}")
        # 전체 종목 도넛
        names = portfolio_df['name'].tolist()
        weights = portfolio_df['weight'].tolist()
        colors_core = ['#0969da', '#1f6feb', '#54aeff', '#79c0ff', '#a5d6ff', '#cae8ff']
        colors_sat = ['#cf222e', '#a40e26', '#d1242f', '#ff8182', '#ffaba8', '#ffcecb', '#ffdcd7', '#fff0ee']
        type_list = portfolio_df['type'].tolist()
        colors = []
        ci, si = 0, 0
        for tp in type_list:
            if 'CORE' in tp:
                colors.append(colors_core[ci % len(colors_core)])
                ci += 1
            else:
                colors.append(colors_sat[si % len(colors_sat)])
                si += 1

        fig = go.Figure(data=[go.Pie(
            labels=names, values=weights, hole=0.4,
            marker=dict(colors=colors),
        )])
        fig.update_layout(
            height=300, paper_bgcolor='white',
            font=dict(color='#000000', size=10),
            margin=dict(l=10,r=10,t=10,b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 매월 매수 계획
    st.markdown(f"##### {t('monthly_buy_plan')}")

    rows = []
    monthly_save_user = convert_amount(monthly_save_usd, 'USD', display_curr, exchange_rates)
    total_actual = 0

    for _, row in portfolio_df.iterrows():
        if pd.isna(row['price']) or row['price'] is None or row['price'] <= 0:
            continue

        # 한 종목 월 할당액
        target_user = row['weight'] * monthly_save_user
        stock_curr = row['currency']

        # 한 종목당 매수 수량 계산
        target_stock_curr = convert_amount(target_user, display_curr, stock_curr, exchange_rates)
        shares = int(target_stock_curr / row['price'])
        actual_stock = shares * row['price']
        actual_user = convert_amount(actual_stock, stock_curr, display_curr, exchange_rates)
        total_actual += actual_user

        sym = CURRENCY_SYMBOLS.get(stock_curr, '')
        rows.append({
            'Type': row['type'],
            'Ticker': row['ticker'],
            'Name': row['name'][:25],
            'Price': f"{sym}{row['price']:,.2f}" if stock_curr != 'KRW' else f"{sym}{row['price']:,.0f}",
            'Weight': f"{row['weight']*100:.1f}%",
            'Shares/mo': str(shares),
            'Amount/mo': fmt_money(actual_user, display_curr),
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=400)

        c1, c2, c3 = st.columns(3)
        c1.metric(t('monthly_save_label'), fmt_money(monthly_save_user, display_curr))
        c2.metric(t('actual_buy_label'), fmt_money(total_actual, display_curr))
        c3.metric(t('cash_leftover'), fmt_money(monthly_save_user - total_actual, display_curr),
                  help=t('cash_leftover_help'))

        # 시뮬레이션
        st.markdown("---")
        st.markdown(f"##### {t('cumulative_simulation')}")

        years_arr = list(range(0, goal_years + 1))
        sc = scenarios[selected_scenario]

        # 3가지 케이스
        expected_arr = [project_wealth(current_invest_usd, monthly_save_usd, y, sc['expected_return']) for y in years_arr]
        worst_arr = [project_wealth(current_invest_usd, monthly_save_usd, y, sc['expected_return'] - sc['volatility']*0.5) for y in years_arr]
        best_arr = [project_wealth(current_invest_usd, monthly_save_usd, y, sc['expected_return'] + sc['volatility']*0.5) for y in years_arr]

        # 통화 변환
        expected_arr = [convert_amount(v, 'USD', display_curr, exchange_rates) for v in expected_arr]
        worst_arr = [convert_amount(v, 'USD', display_curr, exchange_rates) for v in worst_arr]
        best_arr = [convert_amount(v, 'USD', display_curr, exchange_rates) for v in best_arr]
        goal_display_arr = [convert_amount(goal_usd, 'USD', display_curr, exchange_rates)] * len(years_arr)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years_arr, y=best_arr, fill=None, mode='lines',
            line=dict(color='#1a7f37', width=1, dash='dot'),
            name=t('scenario_best_case'),
        ))
        fig.add_trace(go.Scatter(
            x=years_arr, y=worst_arr, fill='tonexty', mode='lines',
            line=dict(color='#cf222e', width=1, dash='dot'),
            fillcolor='rgba(9, 105, 218, 0.1)',
            name=t('scenario_worst_case'),
        ))
        fig.add_trace(go.Scatter(
            x=years_arr, y=expected_arr, mode='lines+markers',
            line=dict(color='#0969da', width=3),
            name=t('scenario_expected'),
        ))
        fig.add_trace(go.Scatter(
            x=years_arr, y=goal_display_arr, mode='lines',
            line=dict(color='#cf222e', width=2, dash='dash'),
            name=f"🎯 {t('goal_amount_label').replace('?', '')}",
        ))

        fig.update_layout(
            height=400, paper_bgcolor='white', plot_bgcolor='white',
            font=dict(color='#000000', family='JetBrains Mono'),
            xaxis=dict(gridcolor='#e0e0e0', title=t('years')),
            yaxis=dict(gridcolor='#e0e0e0', title=display_curr),
            margin=dict(l=20, r=20, t=20, b=20),
            hovermode='x unified',
        )
        st.plotly_chart(fig, use_container_width=True)


def render_finance_tab(user_data, exchange_rates):
    lang = st.session_state.get('lang', 'ko')
    display_curr = user_data['investment_currency']

    health = calculate_financial_health(user_data, exchange_rates)
    score = health['total_score']
    grade, color, label = get_health_grade(score)

    # 종합 점수
    st.markdown(f"### {t('financial_health')}")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
        <div style="text-align: center; padding: 24px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 10px;">
          <div style="font-size: 0.85rem; color: #57606a; text-transform: uppercase; letter-spacing: 1px;">{t('health_score')}</div>
          <div style="font-size: 4rem; font-weight: 700; color: {color}; font-family: 'JetBrains Mono',monospace; line-height: 1;">{grade}</div>
          <div style="font-size: 1.5rem; color: {color}; font-weight: 600; font-family: 'JetBrains Mono',monospace;">{score:.0f}/100</div>
          <div style="color: #57606a; margin-top: 6px; font-size: 0.9rem;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # 게이지 차트
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            number={'font': {'color': '#000000', 'family': 'JetBrains Mono', 'size': 36}},
            gauge={
                'axis': {'range': [None, 100], 'tickcolor': '#57606a'},
                'bar': {'color': color, 'thickness': 0.7},
                'steps': [
                    {'range': [0, 35], 'color': '#ffebe9'},
                    {'range': [35, 50], 'color': '#fff1cc'},
                    {'range': [50, 65], 'color': '#fff8c5'},
                    {'range': [65, 80], 'color': '#ddf4ff'},
                    {'range': [80, 100], 'color': '#dafbe1'},
                ],
                'borderwidth': 1, 'bordercolor': '#d0d7de',
            }
        ))
        fig.update_layout(
            height=280, paper_bgcolor='white',
            font=dict(color='#000000'), margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 세부 항목
    st.markdown(f"### {t('item_analysis')}")
    comps = health['components']

    c1, c2, c3 = st.columns(3)
    with c1:
        sr = comps['savings_rate']
        st.metric(
            t('savings_rate'),
            f"{sr['value']:.1f}%",
            f"{sr['score']:.0f}/100",
            help=t('help_savings_rate_detail'),
        )
    with c2:
        em = comps['emergency']
        st.metric(
            t('emergency_coverage'),
            f"{em['value']:.1f} {t('months')}",
            f"{em['score']:.0f}/100",
            help=t('help_emergency_coverage'),
        )
    with c3:
        dti = comps['dti']
        st.metric(
            t('debt_to_income'),
            f"{dti['value']:.1f}%",
            f"{dti['score']:.0f}/100",
            help=t('help_dti_detail'),
        )

    c1, c2 = st.columns(2)
    with c1:
        ret = comps['retirement']
        st.metric(
            t('retirement_track'),
            f"{ret['value']:.2f}x",
            f"{ret['score']:.0f}/100",
            help=t('help_retirement_track_detail'),
        )
    with c2:
        ir = comps['investment_ratio']
        st.metric(
            t('investment_ratio_label'),
            f"{ir['value']:.1f}%",
            f"{ir['score']:.0f}/100",
            help=t('help_investment_ratio_detail'),
        )

    # 권장 사항
    st.markdown(f"### {t('improvement_section')}")
    recommendations = []
    if comps['savings_rate']['score'] < 50:
        recommendations.append({
            'level': 'warning',
            'title': t('rec_savings_title'),
            'text': t('rec_savings_text').format(comps['savings_rate']['value']),
        })
    if comps['emergency']['score'] < 50:
        recommendations.append({
            'level': 'warning',
            'title': t('rec_emergency_title'),
            'text': t('rec_emergency_text').format(comps['emergency']['value']),
        })
    if comps['dti']['score'] < 50:
        recommendations.append({
            'level': 'warning',
            'title': t('rec_dti_title'),
            'text': t('rec_dti_text').format(comps['dti']['value']),
        })
    if comps['retirement']['score'] < 50:
        recommendations.append({
            'level': 'info',
            'title': t('rec_retirement_title'),
            'text': t('rec_retirement_text').format(comps['retirement']['value']),
        })
    if comps['investment_ratio']['score'] < 70:
        if comps['investment_ratio']['value'] < 30:
            recommendations.append({
                'level': 'info',
                'title': t('rec_invest_low_title'),
                'text': t('rec_invest_low_text'),
            })
        else:
            recommendations.append({
                'level': 'info',
                'title': t('rec_invest_high_title'),
                'text': t('rec_invest_high_text'),
            })

    if recommendations:
        for rec in recommendations:
            if rec['level'] == 'warning':
                st.warning(f"**{rec['title']}**\n\n{rec['text']}")
            else:
                st.info(f"**{rec['title']}**\n\n{rec['text']}")
    else:
        st.success(t('all_metrics_good'))

    # 50/30/20 룰 비교
    st.markdown(f"### {t('budget_rule_section')}")
    st.caption(t('budget_caption'))

    monthly_salary_disp = convert_amount(health['monthly_salary_usd'], 'USD', display_curr, exchange_rates)
    monthly_exp_disp = convert_amount(health['monthly_expenses_usd'], 'USD', display_curr, exchange_rates)
    monthly_save_disp = convert_amount(health['monthly_save_usd'], 'USD', display_curr, exchange_rates)

    if health['monthly_salary_usd'] > 0:
        actual_save_pct = health['monthly_save_usd'] / health['monthly_salary_usd']
        actual_exp_pct = health['monthly_expenses_usd'] / health['monthly_salary_usd']
        actual_needs = min(0.5, actual_exp_pct)
        actual_wants = max(0, actual_exp_pct - 0.5)

        ideal = pd.DataFrame({
            t('budget_category'): [t('budget_essentials'), t('budget_wants'), t('budget_savings_invest')],
            t('ideal_label'): [0.5, 0.3, 0.2],
            t('actual_label'): [actual_needs, actual_wants, actual_save_pct],
        })

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=t('ideal_label'), x=ideal[t('budget_category')], y=ideal[t('ideal_label')]*100,
            marker_color='#1a7f37',
        ))
        fig.add_trace(go.Bar(
            name=t('actual_label'), x=ideal[t('budget_category')], y=ideal[t('actual_label')]*100,
            marker_color='#0969da',
        ))
        fig.update_layout(
            height=300, barmode='group',
            paper_bgcolor='white', plot_bgcolor='white',
            font=dict(color='#000000'), yaxis=dict(title='%', gridcolor='#e0e0e0'),
            xaxis=dict(gridcolor='#e0e0e0'),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# UI: 사이드바
# ============================================================
def get_settings_guide(lang):
    """사이드바 설정 가이드 텍스트"""
    if lang == 'ko':
        return """
**📊 Stocks (종목 수)**

포트폴리오에 담을 종목 수입니다.

- 많을수록 ➜ 분산 ↑, 변동성 ↓, 관리 어려움 ↑
- 적을수록 ➜ 집중 투자, 좋은 종목 효과 큼, 위험 ↑
- 일반적으로 10~15개 정도면 분산 효과가 충분히 나옵니다

**추천:** 초보 10~12개 / 집중 5~7개

---

**📏 Max % (한 종목 최대 비중)**

한 종목이 차지할 수 있는 최대 비중입니다.

예: $10,000 투자, Max 25% → 한 종목 최대 $2,500까지

- 높을수록 ➜ 점수 최고 종목에 몰빵, 집중 위험 ↑
- 낮을수록 ➜ 강제 분산, 좋은 종목에도 충분히 못 베팅
- 실무 펀드는 보통 5~10% 룰 사용

**추천:** 보수 15% / 균형 25% / 공격 30~35%

---

**⚖️ Factor Weights (팩터 가중치)**

4가지 투자 스타일을 어떤 비율로 섞을지 결정합니다.

💰 **Value (가치)** — "싸게 사라"
- PER, PBR 낮은 종목 선호
- 약세장 회복기에 강함
- 성장주 광풍기엔 부진

💎 **Quality (품질)** — "좋은 회사 사라"
- ROE 높고, 부채 적고, 이익률 높은 종목
- 가장 안정적 — 거의 항상 작동
- 약세장 방어 우수

🚀 **Momentum (모멘텀)** — "오르는 거 따라가라"
- 최근 12개월 잘 오른 종목
- 강세장 강력, 시장 전환점에서 위험

🛡️ **Low Vol (저변동성)** — "안 흔들리는 거 사라"
- 가격 변동성 낮은 종목
- 의외로 장기 수익률 우수
- 잠 잘 자고 싶을 때

> **합이 1.0 안 돼도 자동으로 정규화됨**

---

**🎯 추천 가중치 조합**

| 스타일 | Value | Quality | Momentum | Low Vol |
|--------|-------|---------|----------|---------|
| 🛡️ 보수형 | 0.20 | 0.35 | 0.15 | 0.30 |
| ⚖️ 균형형 (기본) | 0.25 | 0.25 | 0.30 | 0.20 |
| 💰 가치투자 | 0.40 | 0.30 | 0.15 | 0.15 |
| 🚀 성장투자 | 0.10 | 0.20 | 0.50 | 0.20 |
| 🐻 약세장 대응 | 0.35 | 0.40 | 0.10 | 0.15 |

---

**💡 솔직히 알려드리는 점**

- 각 팩터 효과는 **장기 평균** — 단기 1~2년은 안 통할 수 있음
- 한 번 설정하면 6개월~1년은 유지 권장
- 자주 바꾸면 그냥 시장 추종이 됨
"""
    elif lang == 'en':
        return """
**📊 Stocks (number of holdings)**

Number of stocks in your portfolio.

- More ➜ better diversification, lower volatility, harder to manage
- Fewer ➜ concentrated bets, big winners matter more, more risk
- Generally 10-15 stocks gives sufficient diversification

**Recommended:** Beginners 10-12 / Concentrated 5-7

---

**📏 Max % (max weight per stock)**

Maximum weight any single stock can have.

Example: $10,000 portfolio, Max 25% → single stock capped at $2,500

- Higher ➜ algorithm can concentrate on top picks, higher risk
- Lower ➜ forced diversification, can't bet big on winners
- Most funds use 5-10% rule in practice

**Recommended:** Conservative 15% / Balanced 25% / Aggressive 30-35%

---

**⚖️ Factor Weights**

Mix of four investment styles.

💰 **Value** — "Buy cheap"
- Prefers low P/E, P/B stocks
- Works well in recoveries
- Struggles in growth manias

💎 **Quality** — "Buy good companies"
- High ROE, low debt, strong margins
- Most stable — works almost always
- Defensive in bear markets

🚀 **Momentum** — "Follow trends"
- Stocks that have risen over the past 12 months
- Strong in bull markets
- Risky at turning points

🛡️ **Low Vol** — "Buy what doesn't shake"
- Low price volatility stocks
- Surprisingly outperforms long-term
- For sleeping well at night

> **Weights auto-normalize to 1.0**

---

**🎯 Recommended combinations**

| Style | Value | Quality | Momentum | Low Vol |
|-------|-------|---------|----------|---------|
| 🛡️ Conservative | 0.20 | 0.35 | 0.15 | 0.30 |
| ⚖️ Balanced (default) | 0.25 | 0.25 | 0.30 | 0.20 |
| 💰 Value investor | 0.40 | 0.30 | 0.15 | 0.15 |
| 🚀 Growth investor | 0.10 | 0.20 | 0.50 | 0.20 |
| 🐻 Bear market | 0.35 | 0.40 | 0.10 | 0.15 |

---

**💡 Honest notes**

- Factor effects are **long-term averages** — may not work for 1-2 years
- Don't change settings often — keep 6-12 months
- Frequent changes = just chasing market
"""
    else:  # da
        return """
**📊 Stocks (antal aktier)**

Antallet af aktier i din portefølje.

- Flere ➜ bedre diversifikation, lavere volatilitet, sværere at administrere
- Færre ➜ koncentrerede væddemål, store vindere betyder mere
- Generelt giver 10-15 aktier tilstrækkelig diversifikation

**Anbefalet:** Begyndere 10-12 / Koncentreret 5-7

---

**📏 Max % (maks vægt pr. aktie)**

Maksimal vægt enkelt aktie kan have.

Eksempel: 70.000 kr portefølje, Max 25% → enkelt aktie max 17.500 kr

- Højere ➜ algoritmen kan koncentrere på topvalg, højere risiko
- Lavere ➜ tvungen diversifikation
- De fleste fonde bruger 5-10% regel i praksis

**Anbefalet:** Konservativ 15% / Balanceret 25% / Aggressiv 30-35%

---

**⚖️ Faktorvægte**

Blanding af fire investeringsstilarter.

💰 **Value (Værdi)** — "Køb billigt"
- Foretrækker lave P/E, P/B aktier
- Fungerer godt i opsving
- Kæmper i vækstmanier

💎 **Quality (Kvalitet)** — "Køb gode virksomheder"
- Høj ROE, lav gæld, stærke marginer
- Mest stabile — virker næsten altid
- Defensiv i bjørnemarkeder

🚀 **Momentum** — "Følg tendenser"
- Aktier der er steget de seneste 12 måneder
- Stærk i tyremarkeder
- Risikabel ved vendepunkter

🛡️ **Low Vol** — "Køb hvad ikke ryster"
- Aktier med lav prisvolatilitet
- Overpresterer overraskende på lang sigt
- For at sove godt om natten

> **Vægte normaliseres automatisk til 1.0**

---

**🎯 Anbefalede kombinationer**

| Stil | Value | Quality | Momentum | Low Vol |
|------|-------|---------|----------|---------|
| 🛡️ Konservativ | 0.20 | 0.35 | 0.15 | 0.30 |
| ⚖️ Balanceret (standard) | 0.25 | 0.25 | 0.30 | 0.20 |
| 💰 Værdi-investor | 0.40 | 0.30 | 0.15 | 0.15 |
| 🚀 Vækst-investor | 0.10 | 0.20 | 0.50 | 0.20 |
| 🐻 Bjørnemarked | 0.35 | 0.40 | 0.10 | 0.15 |

---

**💡 Ærlige noter**

- Faktoreffekter er **langsigtede gennemsnit** — kan ikke fungere 1-2 år
- Skift ikke indstillinger ofte — behold 6-12 måneder
- Hyppige ændringer = bare at jagte markedet
"""


def render_sidebar(user_data):
    """사이드바: 재무목표 달성 매니저 + 프로필 + 고급 분석"""
    with st.sidebar:
        # ────────── 언어 선택 ──────────
        lang_options = {'ko':'🇰🇷 한국어','en':'🇺🇸 English','da':'🇩🇰 Dansk'}
        current_lang = st.session_state.get('lang', 'ko')
        new_lang = st.selectbox(
            "🌐 Language",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(current_lang),
        )
        if new_lang != current_lang:
            st.session_state.lang = new_lang
            if user_data:
                user_data['lang'] = new_lang
                save_user_data(user_data)
            st.rerun()

        st.divider()

        # ────────── 프로필 ──────────
        if user_data:
            st.markdown(f"**👤 {user_data['name']}**")
            st.caption(f"{user_data['age']} {t('years_old')} · {user_data['nationality']}")

            with st.expander(t('edit_profile')):
                new_name = st.text_input(t('name'), value=user_data['name'], key='e_name')
                new_age = st.number_input(t('age'), 18, 100, user_data['age'], key='e_age')
                new_nat = st.selectbox(t('nationality'), ['KR','DK','US'],
                                       index=['KR','DK','US'].index(user_data['nationality']), key='e_nat')
                new_email = st.text_input(t('email'), value=user_data.get('email',''), key='e_email')
                new_salary = st.number_input(t('monthly_salary'), 0, value=user_data['monthly_salary'],
                                              step=100000 if user_data['salary_currency']=='KRW' else 100, key='e_sal')
                new_invest = st.number_input(t('investment_amount'), 0, value=user_data['investment_amount'],
                                              step=1000 if user_data['investment_currency']!='KRW' else 100000, key='e_inv')
                new_expenses = st.number_input(t('monthly_expenses'), 0, value=user_data.get('monthly_expenses',0),
                                                step=100000 if user_data['salary_currency']=='KRW' else 100, key='e_exp')
                new_emergency = st.number_input(t('emergency_fund'), 0, value=user_data.get('emergency_fund',0),
                                                 step=100000 if user_data['salary_currency']=='KRW' else 100, key='e_em')
                new_debt = st.number_input(t('total_debt'), 0, value=user_data.get('total_debt',0),
                                            step=100000 if user_data['salary_currency']=='KRW' else 100, key='e_debt')
                new_retirement = st.number_input(t('retirement_savings'), 0, value=user_data.get('retirement_savings',0),
                                                  step=100000 if user_data['salary_currency']=='KRW' else 100, key='e_ret')

                if st.button(t('save_profile'), key='save_e'):
                    user_data.update({
                        'name': new_name, 'age': new_age, 'nationality': new_nat,
                        'email': new_email, 'monthly_salary': new_salary,
                        'investment_amount': new_invest, 'monthly_expenses': new_expenses,
                        'emergency_fund': new_emergency, 'total_debt': new_debt,
                        'retirement_savings': new_retirement,
                    })
                    save_user_data(user_data)
                    st.session_state.user_data = user_data
                    st.rerun()

                if st.button(t('delete_profile'), key='del'):
                    delete_user_data()
                    st.session_state.user_data = None
                    if 'stock_df' in st.session_state:
                        del st.session_state['stock_df']
                    st.rerun()

            st.divider()

        # ────────── 🎯 재무목표 달성 매니저 ──────────
        st.markdown(f"### {t('goal_manager_title')}")

        goal_amount = user_data.get('goal_amount', 0)
        if goal_amount == 0:
            st.info(t('goal_manager_no_goal'))
        else:
            goal_currency = user_data.get('goal_currency', 'USD')
            goal_years = user_data.get('goal_years', 10)
            goal_purpose = user_data.get('goal_purpose', 'house')
            scenario = user_data.get('selected_scenario', 'moderate')
            etf_region = user_data.get('preferred_etf_region', 'US')

            # 내 목표 카드
            purpose_emojis = {
                'house': '🏠', 'retirement': '🌅', 'education': '🎓',
                'marriage': '💍', 'car': '🚗', 'freedom': '🦅', 'other': '✨',
            }
            purpose_emoji = purpose_emojis.get(goal_purpose, '✨')

            st.markdown(f"""
            <div style="background:#f6f8fa; border:1px solid #d0d7de; border-radius:8px;
                        padding:10px; margin-bottom:8px;">
              <div style="font-size:0.8rem; color:#57606a;">{t('my_goal_label')}</div>
              <div style="font-size:1.1rem; font-weight:700; color:#000;">
                {fmt_money(goal_amount, goal_currency)}
              </div>
              <div style="font-size:0.85rem; color:#57606a;">
                {goal_years} {t('years')} · {purpose_emoji}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # 시나리오 표시
            scenario_names = {
                'conservative': t('risk_low'),
                'moderate': t('risk_mid'),
                'aggressive': t('risk_high'),
            }
            sc_return = SCENARIO_PARAMS[scenario]['return'] * 100
            st.markdown(f"**{t('current_scenario')}:** {scenario_names[scenario]}  \n"
                       f"**{t('required_return_label')}:** {sc_return:.1f}%/yr")

            # ────────── 권장 자산 배분 ──────────
            st.markdown(f"#### {t('asset_allocation')}")
            allocation = PORTFOLIO_BREAKDOWN[scenario]

            # 시각화: 가로 바
            fig = go.Figure()
            asset_types = [
                ('bonds', t('asset_bonds'), '#1a7f37'),
                ('etf', t('asset_etf'), '#0969da'),
                ('stocks', t('asset_stocks'), '#cf222e'),
                ('commodities', t('asset_commodities'), '#9a6700'),
            ]
            for key, label, color in asset_types:
                fig.add_trace(go.Bar(
                    x=[allocation[key] * 100], y=[''], orientation='h',
                    name=f"{label} {allocation[key]*100:.0f}%",
                    marker_color=color,
                    text=f"{allocation[key]*100:.0f}%",
                    textposition='inside',
                    insidetextfont=dict(color='white', size=11),
                ))
            fig.update_layout(
                barmode='stack', height=80,
                paper_bgcolor='white', plot_bgcolor='white',
                showlegend=False,
                xaxis=dict(visible=False, range=[0, 100]),
                yaxis=dict(visible=False),
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

            # ────────── 채권 ──────────
            st.markdown(f"##### {t('asset_bonds')} ({allocation['bonds']*100:.0f}%)")
            bonds = BOND_RECS.get(etf_region, BOND_RECS['US'])
            lang = st.session_state.get('lang', 'ko')
            for b in bonds[:3]:
                name = b.get(f'name_{lang}', b['name_ko'])
                st.markdown(f"- {b['flag']} **{b['ticker']}** — {name}")

            # ────────── ETF ──────────
            st.markdown(f"##### {t('asset_etf')} ({allocation['etf']*100:.0f}%)")
            etfs = ETF_RECS.get(etf_region, ETF_RECS['US'])
            for e in etfs[:4]:
                name = e.get(f'name_{lang}', e['name_ko'])
                st.markdown(f"- {e['flag']} **{e['ticker']}** — {name}")

            # ────────── 개별주 ──────────
            st.markdown(f"##### {t('asset_stocks')} ({allocation['stocks']*100:.0f}%)")
            for s in STOCK_RECS[:6]:
                sector = s.get(f'sector_{lang}', s['sector_ko'])
                st.markdown(f"- {s['flag']} **{s['ticker']}** — {s['name']} ({sector})")

            # ────────── 원자재 ──────────
            st.markdown(f"##### {t('asset_commodities')} ({allocation['commodities']*100:.0f}%)")
            commodities = COMMODITY_RECS.get(etf_region, COMMODITY_RECS['US'])
            for c in commodities:
                name = c.get(f'name_{lang}', c['name_ko'])
                st.markdown(f"- {c['type']} {c['flag']} **{c['ticker']}** — {name}")
            st.caption(t('physical_gold_note'))

            # 시나리오/지역 변경 (간단히)
            with st.expander(f"⚙️ {t('change_scenario')} / {t('change_etf_region')}"):
                new_scenario = st.selectbox(
                    t('select_scenario'),
                    options=['conservative', 'moderate', 'aggressive'],
                    format_func=lambda x: scenario_names[x],
                    index=['conservative', 'moderate', 'aggressive'].index(scenario),
                    key='sb_scenario',
                )
                new_region = st.selectbox(
                    t('etf_region_label'),
                    options=['US', 'KR'],
                    format_func=lambda x: t('etf_region_us') if x == 'US' else t('etf_region_kr'),
                    index=0 if etf_region == 'US' else 1,
                    key='sb_region',
                )
                if new_scenario != scenario or new_region != etf_region:
                    user_data['selected_scenario'] = new_scenario
                    user_data['preferred_etf_region'] = new_region
                    save_user_data(user_data)
                    st.session_state.user_data = user_data
                    st.rerun()

        st.divider()

        # ────────── 🔬 고급 분석 (접이식) ──────────
        with st.expander(t('advanced_section'), expanded=False):
            st.caption(t('advanced_section_desc'))

            market_options = {
                'rec': t('market_rec'), 'us': t('market_us'),
                'kr': t('market_kr'), 'dk': t('market_dk'), 'all': t('market_all'),
            }
            market_key = st.selectbox(
                t('market_select'),
                options=list(market_options.keys()),
                format_func=lambda x: market_options[x],
                index=0,
                key='adv_market',
            )

            risk_options = {'low': t('risk_low'), 'mid': t('risk_mid'), 'high': t('risk_high')}
            # 시나리오에서 risk 매핑
            default_risk_from_scenario = scenario_to_risk(user_data.get('selected_scenario', 'moderate')) if user_data else 'mid'
            risk = st.selectbox(
                t('risk'), options=list(risk_options.keys()),
                format_func=lambda x: risk_options[x],
                index=list(risk_options.keys()).index(default_risk_from_scenario),
                key='adv_risk',
            )

            n_stocks = st.slider("Stocks", 5, 15, 10, key='adv_n')
            max_weight = st.slider("Max %", 10, 50, 25, key='adv_max') / 100

            with st.expander("Factor weights"):
                w_value = st.slider("💰 Value", 0.0, 1.0, 0.25, 0.05, key='adv_v')
                w_quality = st.slider("💎 Quality", 0.0, 1.0, 0.25, 0.05, key='adv_q')
                w_momentum = st.slider("🚀 Momentum", 0.0, 1.0, 0.30, 0.05, key='adv_m')
                w_lowvol = st.slider("🛡️ Low Vol", 0.0, 1.0, 0.20, 0.05, key='adv_lv')

            total = w_value + w_quality + w_momentum + w_lowvol
            weights = {
                'value':w_value/total,'quality':w_quality/total,
                'momentum':w_momentum/total,'low_vol':w_lowvol/total,
            }

            st.markdown("")
            analyze = st.button(t('run_analysis'), use_container_width=True, type="primary", key='adv_analyze')
            st.caption(t('analysis_time_hint'))

        # ────────── 캐시 클리어 ──────────
        if st.button(t('clear_cache_btn'), use_container_width=True, key='clear_cache'):
            st.cache_data.clear()
            for key in ['stock_df', 'full_market_df', 'rec_info', 'actual_market']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success(t('cache_cleared'))
            st.rerun()

        # ────────── 설정 가이드 ──────────
        with st.expander(t('settings_guide_title'), expanded=False):
            st.markdown(get_settings_guide(st.session_state.get('lang', 'ko')))

        return {
            'market_key': market_key, 'risk': risk,
            'n_stocks': n_stocks, 'max_weight': max_weight,
            'factor_weights': weights, 'analyze': analyze,
        }


# ============================================================
# UI: 시장 분석 탭
# ============================================================
def render_market_tab(macro, sectors, market_key, rec_info):
    lang = st.session_state.get('lang', 'ko')
    if rec_info:
        rec_market, scores = rec_info
        market_name = {'us':'🇺🇸 USA','kr':'🇰🇷 Korea','dk':'🇩🇰 Denmark'}[rec_market]
        st.success(f"✨ Recommended: **{market_name}** (US:{scores['us']:.1f} | KR:{scores['kr']:.1f} | DK:{scores['dk']:.1f})")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("VIX", f"{macro.get('^VIX',{}).get('current',0):.1f}",
                  f"{macro.get('^VIX',{}).get('1m_change',0):+.1f}%")
    with c2:
        st.metric("US 10Y", f"{macro.get('^TNX',{}).get('current',0):.2f}%")
    with c3:
        st.metric("S&P 500", f"{macro.get('SPY',{}).get('1y_change',0):+.1f}%")
    with c4:
        st.metric("NASDAQ", f"{macro.get('^IXIC',{}).get('1y_change',0):+.1f}%")
    with c5:
        st.metric("KOSPI", f"{macro.get('^KS11',{}).get('1y_change',0):+.1f}%")
    with c6:
        st.metric("KOSDAQ", f"{macro.get('^KQ11',{}).get('1y_change',0):+.1f}%")

    st.markdown("---")

    for s in generate_market_situation(macro, sectors, market_key, lang):
        st.markdown(s)
        st.markdown("")

    st.markdown("---")
    st.markdown("### 📊 Sectors (1M / 3M)")
    if not sectors.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='1M', x=sectors['Sector'], y=sectors['1M'], marker_color='#0969da'))
        fig.add_trace(go.Bar(name='3M', x=sectors['Sector'], y=sectors['3M'], marker_color='#1a7f37'))
        fig.update_layout(
            height=350, barmode='group',
            paper_bgcolor='white', plot_bgcolor='white',
            font=dict(color='#000000', family='JetBrains Mono'),
            xaxis=dict(gridcolor='#e0e0e0'), yaxis=dict(gridcolor='#e0e0e0', title='%'),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# UI: 스크리닝 탭
# ============================================================
def render_screening_tab(stock_df, n_stocks):
    if stock_df.empty:
        st.error("No data")
        return
    cols = ['ticker','name','market','sector','pe_ratio','pb_ratio','roe',
            'momentum_12_1','volatility','total_score']
    top = stock_df.head(30).copy()
    top['pe_ratio'] = top['pe_ratio'].round(1)
    top['pb_ratio'] = top['pb_ratio'].round(2)
    top['roe'] = (top['roe'] * 100).round(1).astype(str) + '%'
    top['momentum_12_1'] = (top['momentum_12_1'] * 100).round(1).astype(str) + '%'
    top['volatility'] = (top['volatility'] * 100).round(1).astype(str) + '%'
    top['total_score'] = top['total_score'].round(2)
    st.dataframe(top[cols], use_container_width=True, hide_index=True, height=600)


# ============================================================
# UI: 포트폴리오 탭
# ============================================================
def render_portfolio_tab(stock_df, user_data, user_settings, exchange_rates):
    n = user_settings['n_stocks']
    investment_usd = convert_amount(user_data['investment_amount'], user_data['investment_currency'], 'USD', exchange_rates)
    alloc = RISK_ALLOCATION[user_settings['risk']]
    stock_amount_usd = investment_usd * alloc['stocks']
    user_currency = user_data['investment_currency']

    top_tickers = stock_df.head(n)['ticker'].tolist()
    with st.spinner(t('analyzing')):
        try:
            prices = fetch_price_history(top_tickers, years=2)
            valid_tickers = list(prices.columns)
            returns = prices.pct_change().dropna()
            opt_weights = optimize_max_sharpe(returns, max_weight=user_settings['max_weight'])
        except Exception as e:
            st.error(f"Optimization failed: {e}")
            return

    ann_ret, ann_vol, sharpe = portfolio_metrics(opt_weights, returns)
    port_returns = (returns * opt_weights).sum(axis=1)
    mdd = compute_max_drawdown(port_returns)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t('expected_return'), f"{ann_ret*100:+.1f}%")
    c2.metric(t('volatility'), f"{ann_vol*100:.1f}%")
    c3.metric(t('sharpe'), f"{sharpe:.2f}")
    c4.metric(t('mdd'), f"{mdd*100:.1f}%")

    st.markdown("---")
    st.markdown("### 📈 매수 수량 / Shares to Buy")

    rows = []
    info_map = stock_df.set_index('ticker').to_dict('index')
    total_actual = 0
    for ticker, weight in zip(valid_tickers, opt_weights):
        info = info_map.get(ticker, {})
        price = info.get('current_price', np.nan)
        stock_curr = info.get('currency', 'USD')
        if pd.isna(price) or price <= 0:
            continue
        stock_amount_user = convert_amount(stock_amount_usd, 'USD', user_currency, exchange_rates)
        shares, actual_stock, actual_user = calculate_shares(
            weight, stock_amount_user, user_currency, price, stock_curr, exchange_rates)
        total_actual += actual_user
        symbol = CURRENCY_SYMBOLS[stock_curr]
        rows.append({
            'Ticker': ticker,
            'Name': info.get('name', ticker),
            'Sector': info.get('sector', 'N/A')[:18],
            'Price': f"{symbol}{price:,.2f}" if stock_curr != 'KRW' else f"{symbol}{price:,.0f}",
            'Weight': f"{weight*100:.1f}%",
            'Shares': f"{shares}" + (" 주" if stock_curr == 'KRW' else ""),
            'Amount': fmt_money(actual_user, user_currency),
        })

    portfolio_df = pd.DataFrame(rows)

    c1, c2 = st.columns([1, 1.3])
    with c1:
        weights_pct = [float(r['Weight'].replace('%','')) for r in rows]
        names = [r['Ticker'] for r in rows]
        fig = px.pie(values=weights_pct, names=names, hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(height=400, paper_bgcolor='white',
                          font=dict(color='#000000'), margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True, height=400)

    stock_amount_user = convert_amount(stock_amount_usd, 'USD', user_currency, exchange_rates)
    cash_leftover = stock_amount_user - total_actual
    c1, c2, c3 = st.columns(3)
    c1.metric("주식 할당 / Allocated", fmt_money(stock_amount_user, user_currency))
    c2.metric("실제 매수 / Purchased", fmt_money(total_actual, user_currency))
    c3.metric("남는 현금 / Leftover", fmt_money(cash_leftover, user_currency))

    st.markdown("---")
    st.markdown("### 📊 2-Year Backtest")
    cum_ret = (1 + port_returns).cumprod() - 1
    try:
        spy_returns = fetch_price_history(['SPY'], years=2).pct_change().dropna()['SPY']
        spy_cum = (1 + spy_returns).cumprod() - 1
    except:
        spy_cum = None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cum_ret.index, y=cum_ret.values*100,
                              name='Portfolio', line=dict(color='#0969da', width=2.5)))
    if spy_cum is not None:
        fig.add_trace(go.Scatter(x=spy_cum.index, y=spy_cum.values*100,
                                  name='S&P 500', line=dict(color='#8b949e', width=2, dash='dash')))
    fig.update_layout(
        height=350, paper_bgcolor='white', plot_bgcolor='white',
        font=dict(color='#000000', family='JetBrains Mono'),
        xaxis=dict(gridcolor='#e0e0e0'), yaxis=dict(gridcolor='#e0e0e0', title='Cumulative %'),
        margin=dict(l=20,r=20,t=20,b=20), hovermode='x unified',
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# UI: 미래 전망 탭
# ============================================================
def render_outlook_tab(stock_df, macro):
    lang = st.session_state.get('lang', 'ko')

    st.markdown("### 🏆 Top 10 Most Attractive Stocks")
    top10 = stock_df.head(10).copy()
    for idx, row in top10.iterrows():
        rank = idx + 1
        with st.expander(
            f"**#{rank}** {row['market']} `{row['ticker']}` — {row['name']} · Score {row['total_score']:+.2f}",
            expanded=(rank <= 3)
        ):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PER", f"{row['pe_ratio']:.1f}" if pd.notna(row['pe_ratio']) else "N/A")
            c2.metric("ROE", f"{row['roe']*100:.1f}%" if pd.notna(row['roe']) else "N/A")
            c3.metric("Momentum", f"{row['momentum_12_1']*100:+.1f}%" if pd.notna(row['momentum_12_1']) else "N/A")
            c4.metric("Vol", f"{row['volatility']*100:.1f}%" if pd.notna(row['volatility']) else "N/A")

            fd = pd.DataFrame({
                'Factor': ['Value','Quality','Momentum','Low Vol'],
                'Score': [row['value_score'], row['quality_score'], row['momentum_score'], row['low_vol_score']],
            })
            fig = go.Figure(go.Bar(
                x=fd['Score'], y=fd['Factor'], orientation='h',
                marker_color=['#1a7f37' if v>0 else '#cf222e' for v in fd['Score']],
                text=[f"{v:+.2f}" for v in fd['Score']], textposition='auto',
            ))
            fig.update_layout(height=180, paper_bgcolor='white', plot_bgcolor='white',
                              font=dict(color='#000000'), showlegend=False,
                              margin=dict(l=20,r=20,t=10,b=20))
            st.plotly_chart(fig, use_container_width=True, key=f"top_{idx}")

    st.markdown("---")
    st.markdown("### 🔮 Top 5 Future Promising (macro-fit)")
    future = identify_future_promising(stock_df, macro)
    for idx, row in future.iterrows():
        st.markdown(f"**{row['market']} `{row['ticker']}` — {row['name']}** · Score: {row['future_score']:+.2f}")
        if lang == 'ko':
            parts = ["현재 매크로 환경에 적합."]
            if row['momentum_score'] > 0.5: parts.append("🚀 강한 모멘텀")
            if row['quality_score'] > 0.5: parts.append("💎 높은 품질")
            if row['value_score'] > 0.5: parts.append("💰 저평가")
            if row['low_vol_score'] > 0.5: parts.append("🛡️ 안정적")
            reason = " · ".join(parts)
        else:
            parts = ["Macro-fit."]
            if row['momentum_score'] > 0.5: parts.append("🚀 Strong momentum")
            if row['quality_score'] > 0.5: parts.append("💎 High quality")
            if row['value_score'] > 0.5: parts.append("💰 Undervalued")
            if row['low_vol_score'] > 0.5: parts.append("🛡️ Stable")
            reason = " · ".join(parts)
        st.caption(reason)
        st.markdown("")

    st.markdown("---")
    st.markdown("### 📊 3 Future Scenarios")
    for s in generate_future_outlook(macro, lang):
        if s['color'] == 'success':
            st.success(f"**{s['name']}**\n\n{s['desc']}")
        elif s['color'] == 'warning':
            st.warning(f"**{s['name']}**\n\n{s['desc']}")
        else:
            st.info(f"**{s['name']}**\n\n{s['desc']}")


# ============================================================
# UI: 🔥 숨은 가치주 발굴 탭 (신규)
# ============================================================
def render_hidden_gems_tab(full_market_df, macro):
    """전체 시장 기준 저평가 + 미래 상승 가능성 큰 종목"""
    lang = st.session_state.get('lang', 'ko')

    st.markdown(f"### {t('hidden_gems_title')}")
    st.caption(t('hidden_gems_subtitle'))

    if full_market_df.empty:
        st.warning("전체 시장 분석을 먼저 실행해주세요. (사이드바에서 시장 = '🌍 전체' 선택 후 분석)")
        return

    gems = find_hidden_gems(full_market_df, macro, top_n=15)

    if gems.empty:
        st.warning("조건을 만족하는 종목이 없습니다.")
        return

    st.markdown("")
    st.info("""
**💎 어떻게 찾았나요?**
- 🔹 **가치 신호 (35%)**: 낮은 PER·PBR + 가치 함정 회피
- 🔹 **품질 신호 (25%)**: ROE, 부채비율, 이익률
- 🔹 **회복 신호 (20%)**: 3개월 모멘텀 > 12개월 모멘텀 (turnaround)
- 🔹 **성장 신호 (20%)**: 매출 성장, 이익 성장

이 신호들이 결합되면 **"싸지만 회복 중인 우량주"**를 찾을 수 있어요.
""")

    # 산업 분포
    industry_counts = gems['sector'].value_counts().head(8)
    if len(industry_counts) > 0:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("##### 🏭 산업 분포")
            fig = go.Figure(go.Pie(
                labels=industry_counts.index, values=industry_counts.values,
                hole=0.4,
                marker=dict(colors=['#58a6ff','#3fb950','#d29922','#a371f7','#f85149','#79c0ff','#56d364','#e3b341']),
            ))
            fig.update_layout(height=300, paper_bgcolor='white',
                              font=dict(color='#000000'),
                              margin=dict(l=10,r=10,t=10,b=10), showlegend=True,
                              legend=dict(font=dict(size=11)))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("##### 📈 발굴 점수 분포")
            fig = go.Figure(go.Bar(
                x=gems['gem_score'][:10], y=gems['ticker'][:10],
                orientation='h',
                marker_color=['#1a7f37' if v>0 else '#cf222e' for v in gems['gem_score'][:10]],
                text=[f"{v:+.2f}" for v in gems['gem_score'][:10]],
                textposition='auto',
            ))
            fig.update_layout(height=300, paper_bgcolor='white', plot_bgcolor='white',
                              font=dict(color='#000000'), showlegend=False,
                              xaxis=dict(gridcolor='#e0e0e0', title='Gem Score'),
                              yaxis=dict(autorange='reversed'),
                              margin=dict(l=20,r=20,t=10,b=20))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Top 15 Hidden Gems")

    for idx, row in gems.iterrows():
        rank = list(gems.index).index(idx) + 1
        header = (f"**#{rank}** {row['market']} `{row['ticker']}` — "
                  f"**{row['name']}** · {row['sector']} · "
                  f"💎 Gem Score: **{row['gem_score']:+.3f}**")
        with st.expander(header, expanded=(rank <= 5)):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PER", f"{row['pe_ratio']:.1f}" if pd.notna(row['pe_ratio']) else "N/A")
            c2.metric("PBR", f"{row['pb_ratio']:.2f}" if pd.notna(row['pb_ratio']) else "N/A")
            c3.metric("ROE", f"{row['roe']*100:.1f}%" if pd.notna(row['roe']) else "N/A")
            mom_3m = row.get('momentum_3m', np.nan)
            c4.metric("3M Mom.", f"{mom_3m*100:+.1f}%" if pd.notna(mom_3m) else "N/A")

            # 신호 분해
            signals_df = pd.DataFrame({
                'Signal': ['Value', 'Quality', 'Turnaround', 'Growth'],
                'Score': [
                    row['value_signal'], row['quality_signal'],
                    row['turnaround_signal'], row['growth_signal']
                ],
            })
            fig = go.Figure(go.Bar(
                x=signals_df['Score'], y=signals_df['Signal'], orientation='h',
                marker_color=['#1a7f37' if v>0 else '#cf222e' for v in signals_df['Score']],
                text=[f"{v:+.2f}" for v in signals_df['Score']], textposition='auto',
            ))
            fig.update_layout(height=200, paper_bgcolor='white', plot_bgcolor='white',
                              font=dict(color='#000000'), showlegend=False,
                              xaxis=dict(gridcolor='#e0e0e0', range=[-1.2, 1.2]),
                              margin=dict(l=20,r=20,t=10,b=20))
            st.plotly_chart(fig, use_container_width=True, key=f"gem_{idx}")

            # 코멘트 생성
            if lang == 'ko':
                parts = []
                if row['value_signal'] > 0.3:
                    parts.append(f"💰 **저평가**: PER {row['pe_ratio']:.1f}, PBR {row['pb_ratio']:.2f}로 시장 평균 이하")
                if row['quality_signal'] > 0.3:
                    parts.append(f"💎 **재무 건전**: ROE {row['roe']*100:.1f}%, 안정적인 이익 구조")
                if row['turnaround_signal'] > 0.3:
                    parts.append(f"🔄 **회복 시작**: 최근 3개월 반등 신호 — 시장이 인식 시작")
                if row['growth_signal'] > 0.3:
                    if pd.notna(row.get('revenue_growth')):
                        parts.append(f"📈 **성장 중**: 매출 +{row['revenue_growth']*100:.1f}% YoY")
                if not parts:
                    parts.append("📊 여러 신호가 균형있게 양호한 종목")
                for p in parts:
                    st.markdown(f"- {p}")
            else:
                parts = []
                if row['value_signal'] > 0.3:
                    parts.append(f"💰 **Undervalued**: PER {row['pe_ratio']:.1f}, PBR {row['pb_ratio']:.2f}")
                if row['quality_signal'] > 0.3:
                    parts.append(f"💎 **Solid quality**: ROE {row['roe']*100:.1f}%")
                if row['turnaround_signal'] > 0.3:
                    parts.append("🔄 **Turnaround**: 3-month recovery signal")
                if row['growth_signal'] > 0.3:
                    parts.append("📈 **Growing**: revenue/earnings growth")
                if not parts:
                    parts.append("📊 Balanced signals")
                for p in parts:
                    st.markdown(f"- {p}")

    # 주의사항
    st.markdown("---")
    st.warning("""
⚠️ **중요한 주의사항**
- 이 종목들은 **시장이 아직 발견하지 못한 가치**를 가질 수 있지만, **그만큼 위험**도 있습니다
- 저평가에는 **이유**가 있을 수 있어요 (회사 자체 문제, 산업 사양 등)
- 반드시 **사업보고서·뉴스·경영진**을 직접 확인하세요
- **분할 매수**로 들어가시고, 한 종목에 과도하게 베팅하지 마세요
- 이 분석은 **양적 신호만** 보여줄 뿐, **질적 판단**은 본인의 몫입니다
""")


# ============================================================
# UI: 관리 가이드 탭 (요약)
# ============================================================
def render_management_tab(user_data):
    lang = st.session_state.get('lang', 'ko')
    if lang == 'ko':
        st.markdown("""
### 📋 포트폴리오 관리 가이드

#### 1. 매수 (Buy)
- **분할 매수**: 3~5일에 걸쳐 분산
- **장 시작/마감 피하기**: 변동성 큼. 오전 10시~오후 3시 권장
- **지정가 주문** 사용

#### 2. 모니터링 (Monitor) — 주 1회
- 전체 가치 변화, 한 종목 과대 비중, 큰 뉴스

#### 3. 리밸런싱 (Rebalance) — 분기마다
- ±5%p 이상 벗어나면 조정
- 신규 자금으로 부족 종목 매수 (세금 효율)

#### 4. 세금 최적화
""")
        if user_data['nationality'] == 'KR':
            st.info("**🇰🇷 한국**: 해외주식 연 250만원 공제 후 22%. 손익 통산으로 절세.")
        elif user_data['nationality'] == 'DK':
            st.info("**🇩🇰 덴마크**: Aktieindkomst 27% (61,000 DKK까지). Aktiesparekonto 활용 검토.")
        else:
            st.info("**🇺🇸 미국**: 장기보유(>1년) 15%, 401k·IRA 활용.")

        st.markdown("""
#### 5. 위험 신호
- VIX 35 이상
- 한 종목 -20% 급락
- 10Y 금리 ±0.5% 급변
- 본인 소득 변화
""")
    else:
        st.markdown("""
### 📋 Portfolio Management
1. **Buy**: Stage over 3-5 days, use limit orders
2. **Monitor**: Weekly check
3. **Rebalance**: Quarterly, ±5%p drift threshold
4. **Tax optimize**: country-specific
5. **Red flags**: VIX>35, -20% drops, rate spikes
""")


def render_glossary_tab():
    lang = st.session_state.get('lang', 'ko')
    if lang == 'ko':
        g = {
            'PER': '주가/주당순이익. 낮을수록 저평가.',
            'PBR': '주가/주당순자산. 1 미만이면 청산가치보다 저렴.',
            'ROE': '자기자본수익률. 15% 이상 우수.',
            'Momentum': '12개월 수익률 (직전 1개월 제외).',
            'Sharpe': '위험 1단위당 수익. 1.0 이상 우수.',
            'MDD': '과거 최대 하락폭.',
            'VIX': '공포 지수. <15 평온, >25 불안.',
            'Gem Score': '숨은 가치주 발굴 점수 (가치+품질+회복+성장).',
            'Aktieindkomst': '덴마크 주식소득세. 61,000 DKK까지 27%.',
            '저축률': '월급 대비 저축 비율. 20% 이상 권장.',
            '비상금': '월 지출 6개월치 권장.',
            'DTI': '부채소득비율. 36% 이하 권장.',
        }
    else:
        g = {
            'P/E': 'Price/Earnings. Lower = undervalued.',
            'P/B': 'Price/Book. Under 1 = cheap.',
            'ROE': '>15% excellent.',
            'Momentum': '12-1 month return.',
            'Sharpe': '>1.0 excellent.',
            'Gem Score': 'Hidden value score.',
            'Savings Rate': '>20% recommended.',
        }
    for term, desc in g.items():
        with st.expander(f"**{term}**"):
            st.markdown(desc)


# ============================================================
# 메인
# ============================================================
def main():
    st.markdown(TRADER_CSS, unsafe_allow_html=True)

    # 세션 초기화
    if 'lang' not in st.session_state:
        existing = load_user_data()
        st.session_state.lang = existing.get('lang', 'ko') if existing else 'ko'
    if 'user_data' not in st.session_state:
        st.session_state.user_data = load_user_data()

    st.markdown(f"# {t('title')}")
    st.markdown(f"##### {t('subtitle')}")
    st.markdown("---")

    # 프로필 없음 → 환영 화면
    if st.session_state.user_data is None:
        render_welcome()
        return

    user_data = st.session_state.user_data
    user_settings = render_sidebar(user_data)

    with st.spinner(t('loading_macro')):
        macro = fetch_macro_data()
        exchange_rates = fetch_exchange_rates()
        sectors = fetch_sector_data()

    # 분석 실행
    if user_settings['analyze']:
        rec_info = None
        if user_settings['market_key'] == 'rec':
            try:
                rec_market, scores = recommend_market(macro)
                rec_info = (rec_market, scores)
                actual_market = rec_market
            except Exception:
                actual_market = 'us'  # fallback
        else:
            actual_market = user_settings['market_key']

        universe = get_universe_by_market(actual_market)

        # 분석 전체를 try/except로 감싸 오류 시 자동 복구
        try:
            with st.spinner(f"{t('loading_stocks')} ({len(universe)} stocks)"):
                stock_df = run_screening(user_settings['factor_weights'], universe)

            if stock_df.empty:
                st.error(t('no_data_warning'))
                if st.button(t('clear_cache_btn'), key='auto_clear_1'):
                    st.cache_data.clear()
                    st.rerun()
                return

            # 숨은 가치주는 항상 전체 시장 기준으로
            if actual_market == 'all':
                full_market_df = stock_df.copy()
            else:
                with st.spinner("Loading full market for Hidden Gems..."):
                    full_universe = get_full_universe()
                    full_market_df = run_screening(user_settings['factor_weights'], full_universe)

            st.session_state.stock_df = stock_df
            st.session_state.full_market_df = full_market_df
            st.session_state.rec_info = rec_info
            st.session_state.actual_market = actual_market

        except Exception as e:
            # 분석 중 어떤 오류든 발생하면 친절한 안내
            st.error(f"### {t('analysis_error_title')}\n\n```{str(e)[:300]}```\n\n{t('analysis_error_hint')}")
            if st.button(t('clear_cache_btn'), key='auto_clear_2', type='primary'):
                st.cache_data.clear()
                for key in ['stock_df', 'full_market_df', 'rec_info', 'actual_market']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success(t('cache_cleared'))
                st.rerun()
            return

    # 분석 안 했을 때
    if 'stock_df' not in st.session_state:
        # 대시보드 + 재무 목표 + 재무관리 + 경제 포럼 + 용어
        tabs = st.tabs([
            t('tab_dashboard'),
            t('tab_goal'),
            t('tab_finance'),
            t('tab_econ_forum'),
            t('tab_glossary'),
        ])
        with tabs[0]:
            render_personal_dashboard(user_data, macro, exchange_rates)
            st.info(t('press_analyze_hint'))
        with tabs[1]:
            render_goal_tab(user_data, None, macro, exchange_rates)
        with tabs[2]:
            render_finance_tab(user_data, exchange_rates)
        with tabs[3]:
            render_econ_forum_tab(macro, sectors, exchange_rates)
        with tabs[4]:
            render_glossary_tab()
        return

    stock_df = st.session_state.stock_df
    full_market_df = st.session_state.get('full_market_df', stock_df)
    rec_info = st.session_state.get('rec_info')
    actual_market = st.session_state.get('actual_market', 'us')

    # 전체 탭
    tabs = st.tabs([
        t('tab_dashboard'),
        t('tab_goal'),
        t('tab_finance'),
        t('tab_econ_forum'),
        t('tab_overview'),
        t('tab_screening'),
        t('tab_portfolio'),
        t('tab_outlook'),
        t('tab_hidden_gems'),
        t('tab_management'),
        t('tab_glossary'),
    ])

    with tabs[0]:
        render_personal_dashboard(user_data, macro, exchange_rates)
        st.markdown(f"### {t('recommended_portfolio')}")
        top_preview = stock_df.head(user_settings['n_stocks'])[['ticker','name','market','sector','total_score']].copy()
        top_preview['total_score'] = top_preview['total_score'].round(2)
        st.dataframe(top_preview, use_container_width=True, hide_index=True, height=400)
        st.info(t('see_portfolio_tab_hint'))

    with tabs[1]:
        render_goal_tab(user_data, stock_df, macro, exchange_rates)
    with tabs[2]:
        render_finance_tab(user_data, exchange_rates)
    with tabs[3]:
        render_econ_forum_tab(macro, sectors, exchange_rates)
    with tabs[4]:
        render_market_tab(macro, sectors, actual_market, rec_info)
    with tabs[5]:
        render_screening_tab(stock_df, user_settings['n_stocks'])
    with tabs[6]:
        render_portfolio_tab(stock_df, user_data, user_settings, exchange_rates)
    with tabs[7]:
        render_outlook_tab(stock_df, macro)
    with tabs[8]:
        render_hidden_gems_tab(full_market_df, macro)
    with tabs[9]:
        render_management_tab(user_data)
    with tabs[10]:
        render_glossary_tab()


if __name__ == "__main__":
    main()
