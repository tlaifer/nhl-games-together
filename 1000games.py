from itertools import combinations
import requests
import json
import datetime
import os

def write_record_books():
    urls = [
        'https://records.nhl.com/site/api/skater-career-scoring-regular-plus-playoffs?cayenneExp=gamesPlayed',
        'https://records.nhl.com/site/api/skater-career-scoring-regular-season?cayenneExp=gamesPlayed'
    ]

    for url in urls:
        r = requests.get(url=url)
        record_book = r.json()
        fp = 'data/' + url.split('api/')[1].split('?')[0] + '.json'
        with open(fp, 'w') as f:
            json.dump(record_book, f, indent=2)

def find_1000_gamers() -> None:
    players = {}
    with open('data/skater-career-scoring-regular-season.json', 'r') as f:
        player_data = json.load(f)
    for player in player_data['data']:
        if player['gamesPlayed'] >= 1000:
            k = player['playerId']
            v = player['firstName'] + ' ' + player['lastName']
            players[k] = v
    fp = 'data/1000-game-players.json'
    with open(fp, 'w') as f:
        json.dump(players, f, indent=2)

def write_gamelog() -> None:
    '''
    ### schedule 
    https://statsapi.web.nhl.com/api/v1/schedule?startDate=2020-01-01&endDate=2022-12-23
    '''
    gamelog = open('data/games.csv', 'w')
    gamelog.write('pk,date_str,season,gameType,link\n')
    start = datetime.datetime(1916,1,1)
    end = datetime.datetime.now()
    while (start < end):
        this_end = datetime.datetime(start.year+1, 12, 31)
        start_str = start.strftime("%Y-%m-%d")
        end_str = this_end.strftime("%Y-%m-%d")
        start = datetime.datetime(start.year + 2,1,1)

        url = f'https://statsapi.web.nhl.com/api/v1/schedule?startDate={start_str}&endDate={end_str}'
        print(url)
        r = requests.get(url=url)
        r_json = r.json()
        dates = r_json['dates']        
        for date in dates:
            date_str = date['date']
            for game in date['games']:
                season = game['season']
                pk = game['gamePk']
                link = game['link']
                gameType = game['gameType']
                row = ','.join(str(elem) for elem in [pk,date_str,season,gameType,link])
                gamelog.write(row + '\n')

def write_games() -> None:
    '''
    https://statsapi.web.nhl.com/api/v1/game/1990020374/feed/live?site=en_nhl
    '''
    gamelog = open('data/games.csv', 'r')
    for line in gamelog.readlines():
        link = line.split(',')[4].rstrip('\n')
        if (link == 'link'):
            continue
        
        url = 'https://statsapi.web.nhl.com' + link
        print(url)
        r = requests.get(url=url)
        r_json = r.json()

        game_data = r_json['gameData']
        game      = game_data['game']
        season    = str(game['season'])
        game_type = str(game['type'])
        pk        = str(game['pk'])
        
        dir = 'data/' + season + '_' + game_type
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        fp = dir + '/' + pk + '.json'
        with open(fp, 'w') as fp:
            json.dump(r_json, fp, indent=True)

# write_record_books()
find_1000_gamers()
# print(players)
# write_gamelog()
# write_games()

totals = dict()
def key_to_string(k) -> str:
    k    = k.split('_')
    p1   = players_with_1000[k[0]]
    p2   = players_with_1000[k[1]]
    team = k[2]
    return f'{p1} - {p2} ({team})'    

totals = dict()
def process_game(fp):
    f = open(fp, 'r')
    game = json.load(f)
    # data = game['gameData']
    boxscore = game['liveData']['boxscore']
    for t in ['home', 'away']:
        team_data = boxscore['teams'][t]
        team_id = team_data['team']['id']
        players = team_data['goalies'] + team_data['skaters']
        thousand_gamers = []
        for player in players:
            
            if str(player) in players_with_1000:
                thousand_gamers.append(player)
        pairs = list(combinations(thousand_gamers, 2))
        for p in pairs:
            p = sorted(p)
            key = f'{str(p[0])}_{str(p[1])}_{team_id}'
            totals[key] = totals.setdefault(key, 0) + 1

players_with_1000 = json.load(open('data/1000-game-players.json'))
reg_season_files = []
playoff_files = []

for root, dirs, files in os.walk('.', topdown=False):
    for name in files:  
        fp = os.path.join(root, name)
        if '_PR' in fp:
            continue
        if '_R' in fp:
            reg_season_files.append(fp)
        if '_P' in fp:
            playoff_files.append(fp)

for file in playoff_files:
    process_game(file)

print(totals)