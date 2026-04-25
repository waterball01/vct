import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

BASE_URL = 'https://www.vlr.gg'


def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def get_events():
    events = []
    for i in range(1, 15):
        soup = get_soup(f'{BASE_URL}/events/?page={i}')
        for event in soup.select('a.wf-card'):
            event_url = BASE_URL + event['href']
            event_name = event.select_one('div.event-item-title').text.strip()
            events.append({'name': event_name, 'url': event_url})
    return events


def gather_performance_stats(match_url, game_id):
    performance_url = f"{match_url}?game={game_id}&tab=performance"
    print(f"Gathering performance stats from: {performance_url}")
    soup = get_soup(performance_url)
    performance_stats = []

    # Assuming the table has headers we can use to map column indices
    soup = soup.select_one('div.vm-stats-game.mod-active')
    div = soup.find_all('div', recursive=False)
    if len(div) > 1:
        div = div[1]
    else:
        return
    for player_row in div.select('table tr'):
        player_stat = {}
        cols = player_row.find_all('td')
        if cols: 
            player_stat['player_name'] = cols[0].text.strip().split('\n')[0].replace('\t','')
            player_stat['2K'] = int(cols[2].text.strip().split('\t')[0]) if cols[2].text.strip().split('\t')[0] else 0
            player_stat['3K'] = int(cols[3].text.strip().split('\t')[0]) if cols[3].text.strip().split('\t')[0] else 0
            player_stat['4K'] = int(cols[4].text.strip().split('\t')[0]) if cols[4].text.strip().split('\t')[0] else 0
            player_stat['5K'] = int(cols[5].text.strip().split('\t')[0]) if cols[5].text.strip().split('\t')[0] else 0
            player_stat['1v1'] = int(cols[6].text.strip().split('\t')[0]) if cols[6].text.strip().split('\t')[0] else 0
            player_stat['1v2'] = int(cols[7].text.strip().split('\t')[0]) if cols[7].text.strip().split('\t')[0] else 0
            player_stat['1v3'] = int(cols[8].text.strip().split('\t')[0]) if cols[8].text.strip().split('\t')[0] else 0
            player_stat['1v4'] = int(cols[9].text.strip().split('\t')[0]) if cols[9].text.strip().split('\t')[0] else 0
            player_stat['1v5'] = int(cols[10].text.strip().split('\t')[0]) if cols[10].text.strip().split('\t')[0] else 0
            player_stat['econ'] = int(cols[11].text.strip()) if cols[11].text.strip().isdigit() else 0
            player_stat['plants'] = int(cols[12].text.strip()) if cols[12].text.strip().isdigit() else 0
            player_stat['defuses'] = int(cols[13].text.strip()) if cols[13].text.strip().isdigit() else 0
            
            # Calculate multikills and clutches
            player_stat['multikills'] = player_stat['2K'] + player_stat['3K'] + player_stat['4K'] + player_stat['5K']
            player_stat['clutches'] = player_stat['1v1'] + player_stat['1v2'] + player_stat['1v3'] + player_stat['1v4'] + player_stat['1v5']
            performance_stats.append(player_stat)

    return performance_stats

def gather_overview_stats(match_url, game_id):
    overview_url = f"{match_url}?game={game_id}&tab=overview"
    print(f"Gathering overview stats from: {overview_url}")
    soup = get_soup(overview_url)
    player_stats = []

    soup = soup.select_one('div.vm-stats-game.mod-active')
    if not soup:
        return []
    for player_row in soup.select('table tbody tr'):
        player_stat = {}
        cols = player_row.find_all('td')
        if cols:
            player_stat['player_name'] = cols[0].text.strip().replace('\t','').replace('\n','').split(' ')[0]
            player_stat['rating'] = float(cols[2].text.strip().split('\n')[0]) if cols[2].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['acs'] = int(cols[3].text.strip().split('\n')[0]) if cols[3].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['kills'] = int(cols[4].text.strip().split('\n')[0]) if cols[4].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['deaths'] = int(cols[5].text.strip().split('\n')[2]) if cols[5].text.strip().split('\n')[2].isnumeric() else 0
            player_stat['assists'] = int(cols[6].text.strip().split('\n')[0]) if cols[6].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['k/d_ratio'] = int(cols[7].text.strip().split('\n')[0]) if cols[7].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['kast'] = float(cols[8].text.strip().split('\n')[0].strip('%'))/100 if cols[8].text.strip().split('\n')[0].strip('%').isnumeric() else 0
            player_stat['adr'] = int(cols[9].text.strip().split('\n')[0]) if cols[9].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['hs%'] = float(cols[10].text.strip().split('\n')[0].strip('%'))/100 if cols[10].text.strip().split('\n')[0].strip('%').isnumeric() else 0
            player_stat['first_kills'] = int(cols[11].text.strip().split('\n')[0]) if cols[11].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['first_deaths'] = int(cols[12].text.strip().split('\n')[0]) if cols[12].text.strip().split('\n')[0].isnumeric() else 0
            player_stat['fk/fd'] = int(cols[13].text.strip().split('\n')[0]) if cols[13].text.strip().split('\n')[0].isnumeric() else 0
            
            # Add performance stats
            player_stats.append(player_stat)
    performance_stats = gather_performance_stats(match_url, game_id)
    if not performance_stats:
        return
    for player_stat in player_stats:
        performance_stat = next((ps for ps in performance_stats if ps['player_name'] == player_stat['player_name']), {})
        player_stat.update(performance_stat)
    return player_stats

def get_match_results(event_url):
    event = event_url.split('/event')
    matches_url = event[0] + '/event/matches' + event[1]
    print(f"Matches URL: {matches_url}")
    soup = get_soup(matches_url)
    matches = []
    for card in soup.select('div.wf-card'):
        for match in card.select('a.wf-module-item'):
            match_url = BASE_URL + match['href']
            match_soup = get_soup(match_url)
            games = {}
            for game in match_soup.select('div.vm-stats-gamesnav-item'):
                games[re.sub("[0-9]",'',game.text.strip().replace('\t','').replace('\n',''))] = game['data-game-id']
            for game in games:
                players = gather_overview_stats(match_url, games[game])
                if not players:
                    return
                for player in players:
                    matches.append({'event': event[1], 'match_url': match_url, 'game': game, **player})
    return matches

def main():
    events = get_events()
    all_match_results = []
    events = events[70:]
    for event in events:
        match_results = get_match_results(event['url'])
        if not match_results:
            continue
        for match in match_results:
            match['event'] = event['name']
        all_match_results.extend(match_results)

    match_results_df = pd.DataFrame(all_match_results)

    print(match_results_df.head())

    match_results_df.to_csv('match_results.csv', index=False)

if __name__ == '__main__':
    main()