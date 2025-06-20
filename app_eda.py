import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("👥 Population Trends EDA")

        # 파일 업로드
        uploaded = st.file_uploader("📂 population_trends.csv 업로드", type="csv")
        if not uploaded:
            st.warning("population_trends.csv 파일을 업로드해주세요.")
            return

        # 전처리
        df = pd.read_csv(uploaded)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df.loc[(df['지역'] == '세종') & (df[col] == '-'), col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        region_translation = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
            '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
            '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
        }

        tabs = st.tabs([
            "1. 결측치 및 중복 확인",
            "2. 연도별 추이",
            "3. 지역별 인구 변화량 순위",
            "4. 증감률 상위 지역 및 연도 도출",
            "5. 누적영역그래프 등 적절한 시각화"
        ])

        # 1. 결측치 및 중복 확인
        with tabs[0]:  # "1. 결측치 및 중복 확인"
            st.header("📈 Missing Values and Duplicates Check")
            
            # Using the already uploaded 'df' instead of re-uploading
            pop_df = df.copy() 

            # ---------------- 기본 정보 출력 ----------------
            st.subheader("🧾 데이터 구조 (df.info())")
            buf = io.StringIO()
            pop_df.info(buf=buf)
            st.text(buf.getvalue())

            st.subheader("📊 기초 통계량 (df.describe())")
            st.dataframe(pop_df.describe())

            st.subheader("🚨 결측값 및 중복 확인")
            st.write("결측값 개수:")
            st.dataframe(pop_df.isnull().sum())
            st.write(f"중복 행 수: {pop_df.duplicated().sum()}개")

            # ---------------- 연도별 추이 ----------------
            st.subheader("📆 연도별 전체 인구 추이")
            yearly = pop_df.groupby('연도')['인구'].sum().reset_index()
            fig1, ax1 = plt.subplots()
            sns.lineplot(data=yearly, x='연도', y='인구', marker='o', ax=ax1)
            ax1.set_title("Total Population Trend by Year")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Population")
            st.pyplot(fig1)

            # ---------------- 변화량 분석 ----------------
            st.subheader("📍 지역별 인구 변화량 (증감)")
            # Exclude '전국' (National) from region-specific analysis if it exists
            regional_df = pop_df[pop_df['지역'] != '전국']
            pivot = regional_df.pivot(index='연도', columns='지역', values='인구')
            
            # Ensure there are enough years for delta calculation
            if pivot.shape[0] >= 2:
                delta = pivot.iloc[-1] - pivot.iloc[0]
                top_delta = delta.sort_values(ascending=False)
                fig_delta, ax_delta = plt.subplots(figsize=(10, 6))
                sns.barplot(x=top_delta.values, y=top_delta.index, ax=ax_delta, palette='viridis')
                ax_delta.set_title("Population Change by Region (First to Last Year)")
                ax_delta.set_xlabel("Population Change")
                ax_delta.set_ylabel("Region")
                st.pyplot(fig_delta)
            else:
                st.info("Not enough years in the data to calculate population change.")

            st.subheader("📈 증감률(%) 상위 지역")
            if pivot.shape[0] >= 2:
                # Handle division by zero for regions with 0 initial population
                initial_population = pivot.iloc[0].replace(0, np.nan) 
                rate_change = ((pivot.iloc[-1] - pivot.iloc[0]) / initial_population) * 100
                rate_df = rate_change.sort_values(ascending=False).dropna()
                st.dataframe(rate_df.head(10))
            else:
                st.info("Not enough years in the data to calculate growth rate.")


            # ---------------- 시각화 ----------------
            st.subheader("🌈 누적 영역 그래프 (전국 제외)")
            # Exclude '전국' from the stacked area chart
            pivot_for_stacked_area = pop_df[pop_df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')
            fig2, ax2 = plt.subplots(figsize=(12, 7))
            pivot_for_stacked_area.fillna(0).T.plot.area(ax=ax2)
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Population")
            ax2.set_title("Stacked Area Chart of Regional Population by Year (Excluding National)")
            ax2.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), title="Region") # Adjust legend position
            st.pyplot(fig2)

        with tabs[1]:  # "2. 연도별 추이"
            st.header("📈 National Population Trend & 2035 Forecast")
            # Using the already uploaded 'df'
            pop_df_tab2 = df.copy()

            # 전국 데이터 필터링
            nat_df = pop_df_tab2[pop_df_tab2['지역'] == '전국'].copy()
            nat_df.sort_values(by='연도', inplace=True)

            if not nat_df.empty:
                # Plotting national population trend
                fig_nat_pop, ax_nat_pop = plt.subplots(figsize=(10, 6))
                sns.lineplot(data=nat_df, x='연도', y='인구', marker='o', ax=ax_nat_pop)
                ax_nat_pop.set_title("National Population Trend")
                ax_nat_pop.set_xlabel("Year")
                ax_nat_pop.set_ylabel("Population")
                st.pyplot(fig_nat_pop)

                st.subheader("👶 Births and Deaths Trend")
                fig_birth_death, ax_birth_death = plt.subplots(figsize=(10, 6))
                sns.lineplot(data=nat_df, x='연도', y='출생아수(명)', marker='o', label='Births', ax=ax_birth_death)
                sns.lineplot(data=nat_df, x='연도', y='사망자수(명)', marker='o', label='Deaths', ax=ax_birth_death)
                ax_birth_death.set_title("National Births and Deaths Trend")
                ax_birth_death.set_xlabel("Year")
                ax_birth_death.set_ylabel("Number of People")
                ax_birth_death.legend()
                st.pyplot(fig_birth_death)

                # Recent natural increase (births - deaths)
                if len(nat_df) >= 3:
                    recent_years_data = nat_df.tail(3)
                    avg_natural_increase = (recent_years_data['출생아수(명)'] - recent_years_data['사망자수(명)']).mean()
                    st.markdown(f"""
                    ### 💡 Forecasting Insights
                    - The average natural increase (births - deaths) over the last 3 available years is approximately **{avg_natural_increase:,.0f}**.
                    - This value could be used for a simple linear forecast, assuming the trend continues.
                    """)
                else:
                    st.info("Not enough data to calculate the average natural increase over the last 3 years.")

            else:
                st.info("No '전국' (National) data found in the uploaded file for this tab.")

        with tabs[2]:
            st.header("📊 Population Change by Region (Last 5 Years)")
            # Using the already uploaded 'df'
            pop_df_tab3 = df.copy()

            # 최근 5년 기준 계산
            max_year = pop_df_tab3['연도'].max()
            min_year = max_year - 5

            df_recent = pop_df_tab3[pop_df_tab3['연도'].isin([min_year, max_year])]
            df_recent = df_recent[df_recent['지역'] != '전국']  # 전국 제외

            if not df_recent.empty and len(df_recent['연도'].unique()) == 2:
                pivot = df_recent.pivot(index='지역', columns='연도', values='인구')
                
                # Check if both min_year and max_year columns exist after pivoting
                if min_year in pivot.columns and max_year in pivot.columns:
                    pivot['change'] = (pivot[max_year] - pivot[min_year]) / 1000  # 단위: 천 명
                    # Handle division by zero for initial populations of 0
                    pivot['rate'] = ((pivot[max_year] - pivot[min_year]) / pivot[min_year].replace(0, np.nan)) * 100  # 비율 %

                    # 영어 지역명으로 변환
                    pivot = pivot.reset_index()
                    pivot['region_en'] = pivot['지역'].map(region_translation)

                    # 변화량 정렬
                    pivot_sorted = pivot.sort_values('change', ascending=False)

                    # ---- 변화량 그래프 (단위: 천 명) ----
                    fig1, ax1 = plt.subplots(figsize=(10, 7))
                    sns.barplot(data=pivot_sorted, y='region_en', x='change', ax=ax1, palette='Blues_d')

                    for i, val in enumerate(pivot_sorted['change']):
                        ax1.text(val + 1, i, f"{val:.1f}", va='center')

                    ax1.set_title("Population change over 5 years (in thousands)", fontsize=14)
                    ax1.set_xlabel("Change (thousands)")
                    ax1.set_ylabel("Region")
                    st.pyplot(fig1)

                    # ---- 변화율 그래프 (%) ----
                    pivot_sorted_rate = pivot.sort_values('rate', ascending=False).dropna(subset=['rate']) # Drop NaN rates
                    
                    if not pivot_sorted_rate.empty:
                        fig2, ax2 = plt.subplots(figsize=(10, 7))
                        sns.barplot(data=pivot_sorted_rate, y='region_en', x='rate', ax=ax2, palette='Greens_d')

                        for i, val in enumerate(pivot_sorted_rate['rate']):
                            ax2.text(val + 0.5, i, f"{val:.1f}%", va='center')

                        ax2.set_title("Population growth rate over 5 years (%)", fontsize=14)
                        ax2.set_xlabel("Rate (%)")
                        ax2.set_ylabel("Region")
                        st.pyplot(fig2)
                    else:
                        st.info("No regions with calculable growth rates over the last 5 years.")

                    # ---- 해설 ----
                    st.markdown("### 🔍 Interpretation")
                    if not pivot_sorted.empty and not pivot_sorted_rate.empty:
                        top_region = pivot_sorted.iloc[0]['region_en']
                        bottom_region = pivot_sorted.iloc[-1]['region_en']
                        top_rate_region = pivot_sorted_rate.iloc[0]['region_en']
                        bottom_rate_region = pivot_sorted_rate.iloc[-1]['region_en']

                        st.markdown(f"""
                        - Over the past 5 years, **{top_region}** experienced the **largest population increase** in absolute terms.
                        - On the other hand, **{bottom_region}** saw the **most significant population decrease**.
                        - In terms of **growth rate**, **{top_rate_region}** grew the fastest, while **{bottom_rate_region}** declined the most.
                        - The chart above shows clear regional imbalances in demographic trends.
                        """)
                    else:
                        st.info("Insufficient data to provide a full interpretation for population change and growth rates.")
                else:
                    st.info(f"Data for both years ({min_year} and {max_year}) is required to calculate population change.")
            else:
                st.info(f"Please ensure data for both {min_year} and {max_year} exists, and '전국' is excluded.")


        with tabs[3]:  # 탭 4: 증감률 상위 지역 및 연도 도출
            st.header("📊 Top 100 Population Changes by Region and Year")
            # Using the already uploaded 'df'
            pop_df_tab4 = df.copy()

            # 전국 제외
            pop_df_tab4 = pop_df_tab4[pop_df_tab4['지역'] != '전국'].copy()

            # 연도 정렬
            pop_df_tab4 = pop_df_tab4.sort_values(['지역', '연도'])

            # 지역별 인구 변화량(diff) 계산
            pop_df_tab4['change'] = pop_df_tab4.groupby('지역')['인구'].diff()

            # 상위 100개 (증감 절댓값 기준)
            top_changes = pop_df_tab4.dropna(subset=['change']).copy() # Drop NaN from 'change' column
            if not top_changes.empty:
                top_changes = top_changes.reindex(top_changes['change'].abs().sort_values(ascending=False).index)
                top100 = top_changes.head(100).copy()

                # 숫자 포맷 적용 (천 단위 콤마)
                def format_number(n):
                    return f"{int(n):,}"

                top100['population_fmt'] = top100['인구'].apply(format_number)

                # 시각화용 데이터프레임
                display_df = top100[['연도', '지역', 'population_fmt', 'change']].rename(columns={
                    '연도': 'Year',
                    '지역': 'Region',
                    'population_fmt': 'Population',
                    'change': 'Change'
                }).reset_index(drop=True)

                # 컬러 스타일링 함수
                def highlight_change(val):
                    color = 'background-color: '
                    if val > 0:
                        return f"{color}#d0e8ff"  # light blue
                    elif val < 0:
                        return f"{color}#ffd6d6"  # light red
                    return ''

                st.markdown("### 🔍 Top 100 largest yearly changes (excluding national total)")

                styled_df = display_df.style.format({
                    "Change": "{:,.0f}"
                }).applymap(highlight_change, subset=["Change"])

                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("No data available to calculate population changes or top 100 changes.")


        with tabs[4]:  # 탭 5: 누적영역그래프 등 적절한 시각화
            st.header("📊 Stacked Area Chart of Regional Populations")
            # Using the already uploaded 'df'
            pop_df_tab5 = df.copy()

            # 전국 제외
            pop_df_tab5 = pop_df_tab5[pop_df_tab5['지역'] != '전국'].copy()

            # 지역명을 영문으로 변환
            pop_df_tab5['region_en'] = pop_df_tab5['지역'].map(region_translation)

            # 피벗 테이블 생성: 연도 = 행, 지역 = 열
            pivot_df = pop_df_tab5.pivot_table(index='연도', columns='region_en', values='인구', aggfunc='sum')
            pivot_df = pivot_df.fillna(0).sort_index()

            if not pivot_df.empty:
                # 시각화
                fig, ax = plt.subplots(figsize=(12, 6))

                # 누적 영역 그래프
                ax.stackplot(pivot_df.index, pivot_df.T.values, labels=pivot_df.columns,
                             alpha=0.9, edgecolor='gray')

                ax.set_title("Stacked Area Chart of Population by Region", fontsize=14)
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), title="Region")
                ax.grid(True)

                st.pyplot(fig)
            else:
                st.info("No regional population data available for the stacked area chart.")


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()