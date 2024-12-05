import streamlit as st
from football_rank import FootballRank

what_is_this_app = """
FootballRank is a method for ranking college football teams.

Not all college football conferences are equal.
So rather than rank teams solely on win-loss record, I developed FootballRank.
It is inspired by Google’s PageRank algorithm, but is adapted to rank Football teams instead of webpages.
See more details [here](https://github.com/justinpyron/football-rank).

I get score data from [sports-reference.com](https://www.sports-reference.com/cfb/years/2024-schedule.html).

Source code 👉 [GitHub](https://github.com/justinpyron/football-rank).
"""

st.set_page_config(
    page_title='FootballRank',
    page_icon='🏈',
    layout='wide',
)
st.title('FootballRank 🏈')
with st.expander("What is this app?"):
    st.markdown(what_is_this_app)

@st.cache_data
def initialize_ranker():
    return FootballRank()

ranker = initialize_ranker()

with st.container():
    col1, col2, col3 = st.columns(spec=[4,3,2], gap='large')
    with col1:
        most_recent_year = int(ranker.data["season_year"].max())
        year = st.slider(
            label='Year',
            value=most_recent_year,
            min_value=1970, # 1872 is first available year
            max_value=most_recent_year,
        )
    with col2:
        number_of_weeks = int(ranker.data[ranker.data["season_year"] == year]["week"].max())
        week = st.slider(
            label='Week',
            value=1,
            min_value=number_of_weeks,
            max_value=number_of_weeks,
        )
    with col3:
        only_fbs = st.radio(
            label='Opponents to consider',
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
        st.markdown('#### Standings')
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
