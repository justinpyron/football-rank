import streamlit as st
from datetime import datetime
from football_rank import FootballRank


today = datetime.now()
DATA_YEAR_BEGIN = 2005 # 1872 is first available year
DATA_YEAR_END = today.year if today.month >= 9 else today.year-1 # Reset when done testing


st.set_page_config(
    page_title='FootballRank',
    page_icon='🏈',
    layout='wide',
)
st.title('FootballRank 🏈')


@st.cache_data
def initialize_ranker(
    data_year_begin:int,
    data_year_end: int,
):
    return FootballRank(data_year_begin, data_year_end)

ranker = initialize_ranker(DATA_YEAR_BEGIN, DATA_YEAR_END)

with st.container():
    col1, col2, col3 = st.columns(3, gap='large')
    with col1:
        year = st.slider(
            label='Year',
            value=DATA_YEAR_END,
            min_value=DATA_YEAR_BEGIN,
            max_value=DATA_YEAR_END,
        )
    with col2:
        week = st.slider(
            label='Week',
            value=16,
            min_value=1,
            max_value=16,
        )
    with col3:
        only_fbs = st.radio(
            label='Games to consider when computing ranking',
            options=[
                'FBS only',
                'FBS & FCS',
            ],
            index=0,
        )
        only_fbs = True if only_fbs == 'FBS only' else False

with st.container():
    col1, col2 = st.columns(spec=[4,11], gap='medium')
    with col1:
        st.markdown('#### FootballRank Rankings')
        rankings = ranker.football_rank(
            year,
            week,
            only_fbs,
            alpha=0.95,
        )
        st.dataframe(
            rankings,
            hide_index=True,
            use_container_width=True
        )
    with col2:
        st.markdown('#### Win-Loss Statistics')
        stats = ranker.statistics(year, week, only_fbs)
        st.dataframe(stats, use_container_width=True)

with st.container():
    st.markdown('#### Schedules')
    team = st.selectbox(
        label='Team',
        options=rankings['Team'].sort_values(),
        index=0,
    )
    schedule_data = ranker.schedule(team.lower(), year, only_fbs)
    st.dataframe(schedule_data, use_container_width=True)

