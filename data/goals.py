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


def get_goals_df_from_scorebox(df, verbose=False):
    """
    Get the goals df by extracting the scorebox.

    Args:
        df:
        verbose: print the goals df to std out

    Returns:

    """
    url = "https://fbref.com" + df["Match Report"].iloc[0]
    soup = get_html_from_url(url)

    total_home_goals = df["Home Goals"].iloc[0]
    if total_home_goals != 0:
        event_home = soup.find("div", class_="event", id="a").find_all(
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

        home_team = df["Home"].iloc[0]
        squad = [home_team] * len(goals)
    else:
        goals = []
        squad = []

    total_away_goals = df["Away Goals"].iloc[0]
    if total_away_goals != 0:
        event_away = soup.find("div", class_="event", id="b").find_all(
            "div", recursive=False
        )
        away_goals = [
            event.get_text().replace("&rsquor", "")
            for event in event_away
            if event.find(
                "div",
                class_=[
                    "event_icon goal",
                    "event_icon own_goal",
                    "event_icon penalty_goal",
                ],
            )
            is not None
        ]
        goals.extend(away_goals)

        away_team = df["Away"].iloc[0]
        squad.extend([away_team] * len(away_goals))

    goals_df = pd.DataFrame({"Squad": squad, "Goals": goals})
    if verbose:
        print(goals_df)

    assert (
        len(goals_df) == total_home_goals + total_away_goals
    ), f"URL: {url} Actual goals: {len(goals_df)}, Expected goals: {total_home_goals + total_away_goals}"
    return goals_df


if __name__ == "__main__":
    matches_df = pd.read_csv("1920PL_matches.csv")

    # exclude matches which have no goals
    goals_matches_df = matches_df.loc[
        ~((matches_df["Home Goals"] == 0) & (matches_df["Away Goals"] == 0))
    ]
    goals_df = goals_matches_df.groupby(["Wk", "Home", "Away"]).apply(
        get_goals_df_from_scorebox, verbose=True
    )
