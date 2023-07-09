import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import networkx as nx
import matplotlib.pyplot as plt
import re
from typing import Callable


# Algorithm parameters
TIEBREAKER_POINTS = 0.5

# Conferences
ACC = ['boston college', 'florida state', 'georgia tech', 'clemson', 'north carolina', 'duke', 'louisville', 'north carolina state', 'syracuse', 'wake forest', 'miami (fl)', 'pittsburgh', 'virginia', 'virginia tech']
BIG10 = ['penn state', 'rutgers', 'ohio state', 'maryland', 'michigan', 'michigan state', 'indiana', 'purdue', 'illinois', 'northwestern', 'wisconsin', 'minnesota', 'nebraska', 'iowa']
BIG12 = ['texas', 'texas christian', 'baylor', 'texas tech', 'kansas', 'kansas state', 'oklahoma', 'oklahoma state', 'iowa state', 'west virginia']
PAC = ['arizona', 'arizona state', 'southern california', 'ucla', 'california', 'stanford', 'utah', 'colorado', 'oregon', 'oregon state', 'washington', 'washington state']
SEC = ['alabama', 'auburn', 'arkansas', 'louisiana state', 'mississippi', 'mississippi state', 'texas a&m', 'kentucky', 'tennessee', 'vanderbilt', 'south carolina', 'georgia', 'missouri', 'florida']
INDEPENDENT = ['army', 'brigham young', 'navy', 'notre dame']
AAC = ['central florida', 'cincinnati', 'connecticut', 'east carolina', 'houston', 'memphis', 'south florida', 'southern methodist', 'temple', 'tulane', 'tulsa']
MOUNTAIN_WEST = ['air force', 'boise state', 'fresno state', 'colorado state', 'nevada', 'nevada-las vegas', 'new mexico', 'san diego state', 'san jose state', 'utah state', 'wyoming']
C_USA = ['alabama-birmingham', 'florida atlantic', 'florida international', 'louisiana tech', 'marshall', 'middle tennessee state', 'charlotte', 'north texas', 'old dominion', 'rice', 'southern mississippi', 'texas-el paso', 'texas-san antonio', 'western kentucky']
SUN_BELT = ['appalachian state', 'arkansas state', 'coastal carolina', 'georgia southern', 'georgia state', 'louisiana', 'louisiana-monroe', 'south alabama', 'texas state', 'troy']
MAC = ['akron', 'bowling green state', 'buffalo', 'kent state', 'miami (oh)', 'ohio', 'ball state', 'central michigan', 'eastern michigan', 'northern illinois', 'toledo', 'western michigan']

# Conference groupings
POWER_5 = ACC + BIG10 + BIG12 + PAC + SEC + INDEPENDENT
GROUP_OF_5 = AAC + MOUNTAIN_WEST + C_USA + SUN_BELT + MAC
FBS = POWER_5 + GROUP_OF_5


class FootballRank:

    def __init__(
        self,
        start_year: int,
        end_year: int,
        only_fbs: bool = True,
    ) -> None:
        if end_year < start_year:
            raise ValueError('end_year must be greater than or equal to start_year')
        if start_year < 1872:
            raise ValueError('Earliest year available is 1872')
        self.data = self.load_data(start_year, end_year)
        if only_fbs:
            in_fbs_mask = self.data.apply(
                lambda x: x['winner'] in FBS and x['loser'] in FBS,
                axis=1,
            )
            self.data = self.data[in_fbs_mask]


    def scrape_data(
        self,
        year: int,
    ) -> list[str]:
        '''Scrape and process html from sports-reference.com'''
        url = f'https://www.sports-reference.com/cfb/years/{year}-schedule.html'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        rows = list()
        for tr in soup.find_all('tr'):
            new_row = [td.get_text() for td in tr.find_all('td')]
            if len(new_row) > 0:
                rows.append(new_row)
        return rows


    def load_data_single_year(
        self,
        year: int,
    ) -> pd.DataFrame:
        '''Scrapes game result data from www.sports-reference.com for a specific year'''

        # Define DataFrame schemas
        columns_pre_2012 = ['week', 'date', 'day', 'winner', 'points_winner', 'location', 'loser', 'points_loser', 'notes']
        columns_post_2012 = ['week', 'date', 'time', 'day', 'winner', 'points_winner', 'location', 'loser', 'points_loser', 'notes']
        columns = columns_pre_2012 if year <= 2012 else columns_post_2012 # Data schema changed in 2013 season

        # Scrape data
        scraped_rows = self.scrape_data(year)

        # Create DataFrame + process
        df = pd.DataFrame(scraped_rows, columns=columns)
        df = df[(df['points_winner'] != '') & (df['points_loser'] != '')]
        regex = lambda x: re.sub('[(][0-9]+[)]\xa0', '', x).lower()
        df['winner'] = df['winner'].apply(regex)
        df['loser'] = df['loser'].apply(regex)
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
        self,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        data = pd.concat([
            self.load_data_single_year(year) \
            for year in range(start_year, end_year+1)
        ], axis=0)
        return data.reset_index(drop=True)


    def build_matrix(
        self,
        graph_data: pd.DataFrame,
        margin_scaling_func: Callable[[float], float] = lambda x: x,
    ) -> tuple[np.array, np.array]:
        '''Constructs core matrix of PageRank equation'''

        # Compute list of teams
        teams = np.sort(pd.concat([
            graph_data['winner'],
            graph_data['loser'],
        ]).unique())
        n_teams = len(teams)
        map_team_to_index = dict(zip(teams, range(n_teams)))
        
        # Populate matrix
        matrix = np.zeros((n_teams, n_teams))
        for _, row in graph_data.iterrows():
            winner, loser, points_winner, points_loser = row[[
                'winner',
                'loser',
                'points_winner',
                'points_loser',
            ]]
            winner_idx = map_team_to_index[winner]
            loser_idx = map_team_to_index[loser]
            margin = points_winner - points_loser if points_winner > points_loser else TIEBREAKER_POINTS
            # Break ties by declaring away team the winner by TIEBREAKER_POINTS
            # For ties, raw data source labels the away team the winner
            matrix[winner_idx, loser_idx] += margin_scaling_func(margin)  # Don't reassign; add to, in case teams play twice

        # Normalize (outgoing PageRank normalized by total outgoing PageRank)
        column_sums = matrix.sum(axis=0)
        matrix /= np.where(column_sums==0, 1, column_sums)

        # Normalize for number of games played (hit each row with a scalar)
        n_wins = (matrix > 0).sum(axis=1)
        n_losses = (matrix > 0).sum(axis=0)
        n_games = n_wins + n_losses
        matrix = (matrix.T / n_games).T

        return matrix, teams


    def page_rank(
        self,
        matrix: np.array,
        alpha: float = 0.8,
    ) -> np.array:
        '''Solves PageRank system of equations and returns PageRank vector'''
        n = matrix.shape[0]
        rhs = np.eye(n) - alpha*matrix
        lhs = (1-alpha) * np.ones(n) / n
        # NOTE: Giving lhs non-uniform values drastically alters results
        if np.abs(np.linalg.det(rhs)) < 1e-4:
            raise ValueError('PageRank matrix is not invertible!')
        page_rank_vector = np.linalg.solve(rhs, lhs)
        return page_rank_vector


    # def football_rank(
    #     self,
    #     data: pd.DataFrame,
    #     alpha=0.8,
    #     margin_scaling_func=lambda x: x
    # ) -> pd.DataFrame:
    #     '''Computes FootballRank rankings'''
    #     matrix, teams = self.build_matrix(data, margin_scaling_func)
    #     rank_vector = self.page_rank(matrix, alpha)
    #     rankings = pd.DataFrame({'team': teams, 'FootballRank': rank_vector})
    #     rankings = rankings.sort_values(by='FootballRank', ascending=False)
    #     rankings = rankings.reset_index(drop=True)
    #     rankings['rank'] = (rankings.index + 1).tolist()
    #     return rankings[['rank', 'team', 'FootballRank']]


    def football_rank(
        self,
        year: int,
        week: int,
        alpha: float = 0.8,
        margin_scaling_func: Callable[[float], float] = lambda x: x,
        use_last_12months: bool = False,
    ) -> pd.DataFrame:
        '''Computes FootballRank rankings'''

        # Prepare input data
        this_year = self.data[
            (self.data['season_year'] == year) &\
            (self.data['week'] <= week)
        ]
        last_year = self.data[
            (self.data['season_year'] == year-1) &\
            (self.data['week'] > week)
        ]
        data = pd.concat([this_year, last_year]) if use_last_12months else this_year

        # Compute rankings
        matrix, teams = self.build_matrix(data, margin_scaling_func)
        rank_vector = self.page_rank(matrix, alpha)

        # Package inside DataFrame
        rankings = pd.DataFrame({'Team': teams, 'FootballRank Score': rank_vector})
        rankings = rankings.sort_values(by='FootballRank Score', ascending=False)
        rankings = rankings.reset_index(drop=True)
        rankings['Rank'] = (rankings.index + 1).tolist()
        return rankings[['Rank', 'Team', 'FootballRank Score']]


    def statistics(
        self,
        year: int,
        week: int,
    ) -> pd.DataFrame:
        '''
        Compute win-loss statistics for each team through specified week of 
        specified season. For example, statistics(2018,7) computes statistics 
        in 2018 through week 7.
        '''
        this_season = self.data[
            (self.data['season_year'] == year) & (self.data['week'] <= week)
        ]
        last_season = self.data[
            (self.data['season_year'] == year-1) & (self.data['week'] > week)
        ]
        both_seasons = pd.concat([this_season, last_season], axis=0)
        
        teams = np.sort(pd.concat([
            this_season['winner'],
            this_season['loser'],
        ]).unique()).tolist()
        wins = [(this_season['winner'] == x).sum() for x in teams]
        losses = [(this_season['loser'] == x).sum() for x in teams]
        last_12months_wins = [(both_seasons['winner'] == x).sum() for x in teams]
        last_12months_losses = [(both_seasons['loser'] == x).sum() for x in teams]
        
        stats = pd.DataFrame({
            'team': teams,
            'wins': wins,
            'losses': losses,
            'last_12months_wins': last_12months_wins,
            'last_12months_losses': last_12months_losses,
        })
        stats['games_played'] = stats['wins'] + stats['losses']
        stats['win_pct'] = stats['wins'] / stats['games_played']
        stats['last_12months_games'] = stats['last_12months_wins'] + stats['last_12months_losses']
        stats['last_12months_win_pct'] = stats['last_12months_wins'] / stats['last_12months_games']

        return stats[[
            'team',
            'wins',
            'losses',
            'games_played',
            'win_pct',
            'last_12months_wins',
            'last_12months_losses',
            'last_12months_games',
            'last_12months_win_pct',
        ]].sort_values(by='win_pct', ascending=False).reset_index(drop=True)
    

    def schedule(
        self,
        team: str,
        year: int,
        week: int,
    ) -> pd.DataFrame:
        '''Returns a team's schedule through specified week of specified year'''
        return self.data[
            (self.data['season_year'] == year) &\
            (self.data['week'] <= week) &\
            ((self.data['winner'] == team) | (self.data['loser'] == team))
        ].sort_values(by='week').reset_index(drop=True)