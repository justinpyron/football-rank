import streamlit as st
from datetime import datetime
from football_rank import FootballRank


# DATA_YEAR_BEGIN = 1872
DATA_YEAR_BEGIN = 2017
# DATE_YEAR_END = datetime.now().year
DATE_YEAR_END = 2022


st.set_page_config(
	page_title='FootballRank',
	page_icon='🏈',
	layout='wide',
)
st.title('FootballRank 🏈')


@st.cache_data
def initialize_ranker(
	data_year_begin:int,
	date_year_end: int,
):
	return FootballRank(data_year_begin, date_year_end, only_fbs=True)


ranker = initialize_ranker(DATA_YEAR_BEGIN, DATE_YEAR_END)

year = int(st.text_input(label='Year', value=datetime.now().year))
week = int(st.text_input(label='Week'))

st.markdown('#### FootballRank Rankings')
rankings = ranker.football_rank(year, week, alpha=0.9)
st.dataframe(rankings, hide_index=True)

st.markdown('#### Win-Loss Statistics')
stats = ranker.statistics(year, week)
st.dataframe(stats, hide_index=True)

