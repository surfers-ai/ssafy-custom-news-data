import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import time
from datetime import datetime
from wordcloud import WordCloud

def set_page_config():
    """
    페이지 설정
    """
    st.set_page_config(
        page_title="Ssafy News Dashboard",
        page_icon="📰",
        layout="wide"
    )

def apply_styles():
    """
    스타일 적용
    """
    st.markdown("""
        <style>
            .main {
                padding: 1rem;
            }
            .stAlert {
                margin-top: 1rem;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=5)
def load_parquet(filename):
    """
    Parquet 파일 로드
    """
    return pd.read_parquet(filename, engine='pyarrow')

@st.cache_data
def generate_wordcloud(text_data):
    """
    워드클라우드 생성
    """
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color='white',
        font_path="NanumGothic-Regular.ttf"
    ).generate(text_data)
    return wordcloud

def display_metrics(df):
    """
    총 기사 수, 카테고리 수, 작성자 수, 오늘의 기사 수 표시
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 기사 수", len(df))
    with col2:
        st.metric("카테고리 수", df['category'].nunique())
    with col3:
        st.metric("작성자 수", df['writer'].nunique())
    with col4:
        st.metric("오늘의 기사", len(df[df['write_date'].dt.date == datetime.now().date()]))

def display_trend_analysis(df):
    """
    시간대별 기사 발행 트렌드
    """
    st.subheader("시간대별 기사 발행 트렌드")
    daily_counts = df.resample('D', on='write_date')['title'].count()
    fig_trend = px.line(daily_counts, 
                        title="일별 기사 수",
                        labels={'value': '기사 수', 'write_date': '날짜'})
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.subheader("주요 키워드 워드클라우드")
    all_keywords = ' '.join(df['keywords'].dropna())
    wordcloud = generate_wordcloud(all_keywords)
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

def display_category_analysis(df):
    """
    카테고리별 기사 분포 시각화
    """
    st.subheader("카테고리별 기사 분포")
    category_counts = df['category'].value_counts()
    fig_cat = px.pie(values=category_counts.values, 
                     names=category_counts.index,
                     title="카테고리별 기사 비율")
    st.plotly_chart(fig_cat, use_container_width=True)
    
    st.subheader("카테고리별 시간대 분포")
    df['hour'] = df['write_date'].dt.hour
    category_hour = pd.crosstab(df['category'], df['hour'])
    fig_heat = px.imshow(category_hour,
                         labels=dict(x="시간", y="카테고리", color="기사 수"),
                         title="카테고리별 시간대 히트맵")
    st.plotly_chart(fig_heat, use_container_width=True)

def display_detailed_data(df):
    """
    기사 데이터 검색
    """
    st.subheader("기사 데이터 검색")
    search_term = st.text_input("검색어를 입력하세요")
    
    if search_term:
        filtered_df = df[df['title'].str.contains(search_term, na=False) | 
                         df['content'].str.contains(search_term, na=False)]
    else:
        filtered_df = df
    
    st.dataframe(
        filtered_df[['title', 'write_date', 'category', 'writer', 'url']],
        use_container_width=True,
        height=400
    )

def display_footer(refresh_rate):
    """
    푸터 표시
    """
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.write(f"다음 업데이트까지: {refresh_rate}초")

def run_dashboard():
    set_page_config()
    apply_styles()
    
    st.title("📰 Ssafy News Dashboard")
    st.markdown("### 뉴스 기사 크롤링 실시간 데이터 분석 및 시각화")
    
    with st.sidebar:
        st.header("필터 옵션")
        refresh_rate = st.slider("새로고침 주기 (초)", 5, 60, 10)
        
    try:
        df = load_parquet('realtime.parquet')
        df['write_date'] = pd.to_datetime(df['write_date'])
        
        # 메트릭 표시
        display_metrics(df)
        
        # 탭 생성
        tab1, tab2, tab3 = st.tabs(["📈 트렌드 분석", "📊 카테고리 분석", "🔍 상세 데이터"])
        
        with tab1:
            # 트렌드 분석
            display_trend_analysis(df)
            
        with tab2:
            # 카테고리 분석
            display_category_analysis(df)
            
        with tab3:
            # 상세 데이터 검색
            display_detailed_data(df)
        
        # 푸터 표시
        display_footer(refresh_rate)
        
        # 새로고침
        time.sleep(refresh_rate)
        st.rerun()
        
    except Exception as e:
        # 오류 발생 시 오류 메시지 표시
        st.error(f"데이터 로딩 중 오류 발생: {str(e)}")
        st.error("자동으로 재시도합니다...")
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    run_dashboard()