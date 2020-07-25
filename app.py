import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm
from datetime import datetime
import os

leagues = ['EPL','La_liga', 'Bundesliga', 'Serie_A', 'Ligue_1', 'RFPL']
seasons = ['2014', '2015', '2016', '2017', '2018', '2019', 'Etc...']

print('='*50)
print('Choose a season: ', seasons)
season = input('Enter Here: ')
print('='*50)
print('Choose a League: ', leagues)
league = input('Enter Here: ')
print('='*50)

base_url = 'https://understat.com/league'
leagues = ['EPL','La_liga', 'Bundesliga', 'Serie_A', 'Ligue_1', 'RFPL']
seasons = ['2014', '2015', '2016', '2017', '2018', '2019']

#get the url
url = base_url + '/' + league + '/' + season
res = requests.get(url)
soup = BeautifulSoup(res.content, 'lxml')
script = soup.find_all('script')

#look for the data
string_json_obj = ''
for el in script:
    if 'teamsData' in str(el):
        string_json_obj = str(el).strip()

ind_start = string_json_obj.index("('")+2
ind_end = string_json_obj.index("')")

#get the json
json_data = string_json_obj[ind_start:ind_end]
json_data = json_data.encode('utf8').decode('unicode_escape')
data = json.loads(json_data)

#get team names
teams = {}
for i in data.keys():
    teams[i] = data[i]['title']

#create dataframes for all the teams
teams_dataframe = {}

#pull the data per team
for i in tqdm(data.keys(), desc='Pulling the data per team'):
    columns = list(data[i]['history'][0].keys())
    team_name = data[i]['title']
    team_data = []
    for row in data[i]['history']:
        team_data.append(list(row.values()))
        df = pd.DataFrame(team_data, columns=columns)
        teams_dataframe[team_name] = df
#get the coef of ppda
for team, df in teams_dataframe.items():
    teams_dataframe[team]['ppda_coef'] = teams_dataframe[team]['ppda'].apply(lambda x: x['att']/ x['def'] if x['def'] != 0 else 0)
    teams_dataframe[team]['oppda_coef'] = teams_dataframe[team]['ppda_allowed'].apply(lambda x: x['att']/ x['def'] if x['def'] != 0 else 0)

#get the sum and mea
cols_to_sum = ['xG', 'xGA', 'npxG', 'npxGA', 'deep', 'deep_allowed', 'scored', 'missed', 'xpts', 'wins', 'draws', 'loses', 'pts', 'npxGD']
cols_to_mean = ['ppda_coef', 'oppda_coef']
frames = []

for team, df in tqdm(teams_dataframe.items(), desc = 'Preparing the Data'):
    sum_df = pd.DataFrame(df[cols_to_sum].sum()).T
    mean_df = pd.DataFrame(df[cols_to_mean].mean()).T
    final_df = sum_df.join(mean_df)
    final_df['team'] = team
    final_df['matches'] = len(df)
    frames.append(final_df)
    
full_stats = pd.concat(frames)
full_stats = full_stats[['team', 'matches', 'wins', 'draws', 'loses', 'scored', 'missed', 'pts', 'xG', 'npxG', 'xGA', 'npxGA', 'npxGD', 'ppda_coef', 'oppda_coef', 'deep', 'deep_allowed', 'xpts']]

#sort teams by wins
full_stats = full_stats.sort_values('wins', ascending=False)

sub_folder = str(datetime.now())
os.makedirs(sub_folder)
full_stats.to_csv(sub_folder + '/' +league+season + '.csv')

print('Data Succesfully Extracted')
print('Folder Name: ', sub_folder )
