"""
This script has functions for getting NBA player stat tables from
basketball reference and displaying it in the terminal.
"""
import argparse
import sys
import requests

import pandas as pd
from rich.console import Console
from rich.table import Table

def create_player_url(first_name: str, last_name: str, n: int = 1) -> str:
    """The format of basketball-reference.com player overview pages."""
    url = 'https://www.basketball-reference.com/players'
    return f'{url}/{last_name[0]}/{last_name[0:5]}{first_name[0:2]}{str.zfill(str(n), 2)}.html'

def get_tables(url):
    """Read in all the <table> tags from page into dfs

    Not sure why the default player page only returns 6 tables when
    there are clearly more on the page...
    """
    page = requests.get(url)

    if page.status_code != 200:
        print("ERROR status code:", page.status_code)
        sys.exit()

    return pd.read_html(page.content)

def remove_rows(df):
    """
    Remove rows that aren't actual stat seasons or career summaries.
    """
    df.drop(df.index[df['Lg'] != 'NBA'], inplace=True)  # Overseas seasons
    df.drop(df.index[df['Season'].astype(str).str.contains('season')], inplace=True)  # Team summary rows
    df.drop(df.index[df['Season'].isna()], inplace=True)  # There is a row all NaNs after career

def remove_stats(df):
    """Remove stats I don't care about, mostly to better fit data in
    terminal printing.  I.e. we remove the "makes" (2P, 3P, FT) for
    shooting since we can easily infer from the attempts numbers and
    the percentages.
    """
    drop_cols = [
        '2P',
        '3P',
        'DRB',
        'FG',
        'FT',
        'Lg',
    ]
    drop_cols += [col for col in df.columns if 'Unnamed:' in col]
    for col in drop_cols:
        if col in df.columns:
            df.drop(columns=col, axis=1, inplace=True)

def get_player_stats(first_name, last_name, stats='avg', playoffs=False, n=1):
    """
    args:
    - stats can be 'avg' | 'total' | 'adv
    - n is a number that is used to differentiate players with same name (WIP)
    """
    url = create_player_url(first_name, last_name, n)
    tables = get_tables(url)

    # This comes from the html page layout on bball reference
    table_map = {'avg': 0, 'tot': 2, 'adv': 4}
    table_idx = table_map[stats] + int(playoffs)  # add 1 for playoff version
    df = tables[table_idx]

    # Clean up the data
    remove_rows(df)
    remove_stats(df)

    return df

def pprint_df(df, first_name, last_name, stats, playoffs, **kwargs):
    """Pretty print tables to terminal using Rich library."""
    title = f'{first_name.capitalize()} {last_name.capitalize()} {"Regular Season" if not playoffs else "Playoffs"} {stats}'
    table = Table(title=title)
    rows = df.values.tolist()
    rows = [[str(e) for e in row] for row in rows]
    columns = df.columns.tolist()

    for column in columns:
        table.add_column(column)

    for i, row in enumerate(rows):
        if row[0] == 'Career':
            table.add_row(*row, style='steel_blue1')
        elif i % 2 == 0:
            table.add_row(*row, style='bright_cyan')
        else:
            table.add_row(*row, style='light_cyan1')

    console = Console()
    console.print(table)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('first_name', type=str, help="Player first name")
    parser.add_argument('last_name', type=str, help="Player last name")
    parser.add_argument('-s', '--stats', type=str, default='avg', choices=['avg', 'tot', 'adv'], help="Type of stats table", metavar='')
    parser.add_argument('-p', '--playoffs', action='store_true', help="Playoffs or regular season")
    parser.add_argument('-n', '--n', type=int, default=1, help="Increment this if the wrong player with the same name is returned", metavar='')
    return vars(parser.parse_args())

def main():
    args = get_args()
    df = get_player_stats(**args)
    pprint_df(df, **args)

if __name__ == '__main__':
    main()
