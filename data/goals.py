from functools import partial
from multiprocessing.pool import ThreadPool
from typing import List, Tuple

import pandas as pd

import requests
from bs4 import BeautifulSoup, Comment


def get_html_from_url(url):
    # get response page from url
    page = requests.get(url)
    # parse the html code
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def get_goals_df_from_shots(df, verbose=False):
    """
    Get the goals df by finding the shots table and filtering for goals.

    Note: This method will exclude own goals since own goals are not part of shots.

    Args:
        df: Dataframe which has the match report url column
        verbose: print the goals df to std out

    Returns: goals df with the following columns ["Minute", "Player", "Squad"]
    """
    url = "https://fbref.com" + df["Match Report"].iloc[0]
    soup = get_html_from_url(url)

    all_shots_tag = soup.find(id="all_shots_all")
    comments = all_shots_tag.find(string=lambda text: isinstance(text, Comment))
    df = pd.read_html(str(comments), flavor="bs4")[0]
    df.columns = df.columns.droplevel()
    df = df.iloc[:, :4]
    goals_df = df.loc[df["Outcome"] == "Goal", ["Minute", "Player", "Squad"]]
    if verbose:
        print(goals_df)
    return goals_df


def get_goals_from_scorebox(soup, id: str, team: str) -> Tuple[List, List]:
    """
    Identify and scrape the score box for goals.

    Args:
        soup:
        id: A str of id used by fbref website to identify home team and away team
        team: A str of team name

    Returns: A Tuple of two Lists (goals, squads).

    """
    event_home = soup.find("div", class_="event", id=id).find_all(
        "div", recursive=False
    )
    goals = [
        event.get_text().replace("&rsquor", "")
        for event in event_home
        if event.find(
            "div",
            class_=[
                "event_icon goal",
                "event_icon own_goal",
                "event_icon penalty_goal",
            ],
        )
    ]
    squad = [team] * len(goals)
    return goals, squad


get_home_goals = partial(get_goals_from_scorebox, id="a")
get_away_goals = partial(get_goals_from_scorebox, id="b")


def get_goals_df_from_scorebox(key:Tuple, df, verbose=False):
    """
    Get the goals df by extracting the scorebox.

    Args:
        key: Tuple of (week, home_team, away_team)
        df: A single row DataFrame with columns ["Match Report", "Home Goals", "Away Goals"]
        verbose: print the goals df to std out

    Returns:

    """
    week, home_team, away_team = key
    url = "https://fbref.com" + df["Match Report"].iloc[0]
    soup = get_html_from_url(url)

    total_home_goals = df["Home Goals"].iloc[0]
    if total_home_goals != 0:
        home_goals, home_squad = get_home_goals(soup, team=home_team)
    else:
        home_goals, home_squad = [], []

    total_away_goals = df["Away Goals"].iloc[0]
    if total_away_goals != 0:
        away_goals, away_squad = get_away_goals(soup, team=away_team)
    else:
        away_goals, away_squad = [], []

    goals_df = pd.DataFrame({"Squad": home_squad + away_squad, "Goals": home_goals+away_goals, "Week":week, "Home":home_team, "Away":away_team})
    if verbose:
        print(goals_df)

    assert (
        len(goals_df) == total_home_goals + total_away_goals
    ), f"URL: {url} Actual goals: {len(goals_df)}, Expected goals: {total_home_goals + total_away_goals}"
    return goals_df


def _get_goals_df_from_scorebox(args:Tuple):
    # Utility funciton to unpack Tuple into individual arguments
    return get_goals_df_from_scorebox(*args)


if __name__ == "__main__":
    matches_df = pd.read_csv("1920PL_matches.csv")

    # exclude matches which have no goals
    goals_matches_df = matches_df.loc[
        ~((matches_df["Home Goals"] == 0) & (matches_df["Away Goals"] == 0))
    ]

    # multithreading to speed up
    goals_matches_df_grouped = goals_matches_df.groupby(["Wk", "Home", "Away"])
    threads = min(10, len(goals_matches_df))
    with ThreadPool(threads) as pool:
        # map results are ordered
        result = pool.map(_get_goals_df_from_scorebox, goals_matches_df_grouped)
    goals_df = pd.concat(result)

    # post processing
    goals_df[["Player", "Time"]] = goals_df["Goals"].str.split("·").to_list()
    goals_df["Player"] = goals_df["Player"].str.strip()
    goals_df["Time"] = goals_df["Time"].str.strip()
    goals_df.drop(columns="Goals", inplace=True)

    goals_df.to_csv("1920PL_goals.csv", index=False)