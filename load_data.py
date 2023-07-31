import numpy as np
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import re
import click


REQUEST_WAIT_TIME_SECONDS = 4


def scrape_data(year: int) -> list[str]:
    '''
    Scrape html from sports-reference.com for a single season year.
    
    Take note of sports-reference.com's bot policy:
    "Currently we will block users sending requests to
    our sites more often than twenty requests in a minute"
    https://www.sports-reference.com/bot-traffic.html
    '''
    time.sleep(REQUEST_WAIT_TIME_SECONDS)
    url = f'https://www.sports-reference.com/cfb/years/{year}-schedule.html'
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    rows = list()
    for tr in soup.find_all('tr'):
        new_row = [td.get_text() for td in tr.find_all('td')]
        if len(new_row) > 0:
            rows.append(new_row)
    return rows


def load_data_single_year(year: int) -> pd.DataFrame:
    '''Scrapes game result data from www.sports-reference.com for a specific season year'''

    # Scrape data
    scraped_rows = scrape_data(year)

    # Define DataFrame schemas; sports-reference.com schema changed beginning 2013 season
    columns_pre_2012 = [
        'week',
        'date',
        'day',
        'winner',
        'points_winner',
        'location',
        'loser',
        'points_loser',
        'notes'
    ]
    columns_post_2012 = [
        'week',
        'date',
        'time',
        'day',
        'winner',
        'points_winner',
        'location',
        'loser',
        'points_loser',
        'notes'
    ]

    # Create DataFrame + process
    df = pd.DataFrame(
        scraped_rows,
        columns=columns_pre_2012 if year <= 2012 else columns_post_2012
    )
    df = df[(df['points_winner'] != '') & (df['points_loser'] != '')]
    regex_fn = lambda x: re.sub('[(][0-9]+[)]\xa0', '', x).lower()
    df['winner'] = df['winner'].apply(regex_fn)
    df['loser'] = df['loser'].apply(regex_fn)
    df = df[columns_pre_2012] # Format choice: use pre-2012 for all years
    df = df.drop_duplicates(
        subset=[c for c in columns_pre_2012 if c != 'notes']
    ) # Sometimes columns are duplicates but with different 'notes' columns
    df['week'] = df['week'].astype('int')
    df['points_winner'] = df['points_winner'].astype('int')
    df['points_loser'] = df['points_loser'].astype('int')
    df['date'] = pd.to_datetime(df['date'])
    df['season_year'] = df.apply(
        lambda x: x['date'].year if x['date'].month >= 8 else x['date'].year-1,
        axis=1,
    ) # January bowl games belong to previous year's season

    return df


def load_data(
    year_start: int,
    year_end: int,
) -> pd.DataFrame:
    '''Loads DataFrame containing data for all years'''
    if year_end < year_start:
        raise ValueError('year_end must be greater than or equal to year_start')
    if year_start < 1872:
        raise ValueError('Earliest year available is 1872')
    data = pd.concat([
        load_data_single_year(year)
        for year in range(year_start, year_end+1)
    ], axis=0)
    return data.reset_index(drop=True)


@click.command()
@click.argument('year_start')
@click.argument('year_end')
@click.argument('filename')
def main(year_start, year_end, filename):
    df = load_data(int(year_start), int(year_end))
    df.to_csv(filename, index=False)


if __name__ == '__main__':
    main()
