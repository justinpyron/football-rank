# Introduction
_FootballRank_ is a method for ranking college football teams inspired by Google’s PageRank algorithm.

### Why is ranking college football teams so difficult?
Because the college football universe consists of 130+ teams scattered throughout 10 conferences. Although some cross-pollination exists via non-conference games, the distinct conferences are mostly isolated from one another. This is in strong contrast to professional sports leagues, which have relatively few teams with significant interaction.

As a result, it is difficult to make relative judgments about two teams playing in different conferences. The two teams will likely have never played each other. And, in most cases, they will never have *even played a common opponent*.

The common solution to this problem is to simply compare win-loss records. However, significant variation in conference quality frustrates such an approach. For example, a team in the baby-NFL SEC is likely far superior to a team in the (not-so-formidable) MAC with the same record. As a result, final rankings are an amalgam of win-loss records and subjective judgement.

This is the problem FootballRank is designed to solve. In particular, FootballRank models the college football universe as one interconnected system, and leverages non-conference games to ascertain information about differences in conference quality. The result is a ranking algorithm that avoids the hand-wavvy and subjective judgements of most other ranking methods.

For the mathematical details, see the appendix below.


# Installation
This project uses [Poetry](https://python-poetry.org/docs/) to manage its Python environment.

1. Install Poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies
```
poetry install
```

# Usage
A Streamlit web app provides an interface with the FootballRank logic. The app uses FootballRank to generate rankings as a function of two items: the season year, and the week in the season.

The web app can be accessed at https://football-rank.streamlit.app/.

Alternatively, the app can be run locally with
```
poetry run streamlit run app.py
```

# Project Organization
```
├── app.py              <- Streamlit app interface
├── football_rank.py    <- Logic for computing FootballRank rankings
├── README.md           <- Description of repo
├── pyproject.toml      <- Poetry config specifying environment dependencies
├── poetry.lock         <- Locked dependencies to ensure consistent installs
```


# Appendix: Underlying Math
The main idea of the _PageRank_ algorithm is that webpages which receive links from important webpages are important. 
Mathematically (in a simplified version), the PageRank $x_i \in \mathbb{R}_+$ of webpage $i$ is
$$
x_i = \sum_{j \in B_i} \frac{x_j}{N_j}
$$
where 
* $B_i = \text{the set of webpages that link to webpage } i$
* $N_j = \text{number of webpages to which webpage } j \text{ links}$

In words, the PageRank of a webpage is the sum of the PageRank of all webpages that link to it, normalized by how many links each linking page gives out.

**_FootballRank_** adapts this idea to football, by replacing webpages with teams and links with victories. Mathematically, the FootballRank $x_i \in \mathbb{R}_+$ of team $i$ is

$$
x_i = (1 - \alpha) + \frac{\alpha}{g_i} \sum_{j \in B_i} \frac{m_{ji}}{\theta_j} x_j
$$

where
* $\alpha \in (0,1)$ is a parameter necessary to prevent a noninvertible matrix when solving
* $g_i = \text{the number of games played by team } i$
* $B_i = \text{the set of all teams defeated by team } i$
* $m_{ji} = \text{the margin of victory of team } i \text{ over team } j$
* $\theta_j = \sum_{\ell \in \{ k: \ell \in B_k \}} m_{j\ell}$ = sum of margin of defeat for team $j$ across all its games

In words, the _FootballRank_ of a team is the sum of the _FootballRank_ of all teams that it defeated, normalized by how abnormal the margin of defeat was for the losing team.
