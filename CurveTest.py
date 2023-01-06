import json
import requests
import numpy as m
import os
import Tech_Calculator.tech_calc as tech_calc

playerTestList = [2769016623220259,76561198059961776,76561198072855418,76561198075923914,76561198255595858,76561198404774259, 
    76561198225048252, 76561198110147969, 76561198081152434, 76561198204808809, 76561198072431907, 76561198989311828, 76561198960449289, 
    76561199104169308, 3225556157461414, 76561198410971373, 76561198153101808, 76561197995162898, 2169974796454690, 76561198166289091, 
    76561198285246326, 76561198802040781]

# playerTestList = [76561198285246326, 76561198802040781]

def searchDiffNum(diffNum, diffList):
    for f in range(0, len(diffList)):
        if diffList[f]['value'] == diffNum:
            return f

def newPlayerStats(userID, scoreCount, retest=False):
    s = requests.Session()
    AiJSON = {}
    newStats = []

    result = s.get(
        f"https://api.beatleader.xyz/player/{userID}/scores?sortBy=pp&order=desc&page=1&count={scoreCount}")
    playerJSON = json.loads(result.text)

    result = s.get(f"https://api.beatleader.xyz/player/{userID}/")
    playerName = json.loads(result.text)['name']
    if retest:
        print("Will recalulate and update tech data")
    for i in range(0, len(playerJSON['data'])):
        newStats.append({})
        if playerJSON['data'][i]['pp'] != 0:
            diffNum = playerJSON['data'][i]['leaderboard']['difficulty']['value']
            diffIndex = searchDiffNum(diffNum, playerJSON['data'][i]['leaderboard']['song']['difficulties'])
            key = playerJSON['data'][i]['leaderboard']['song']['id']
            key = key.replace('x', '')
            if playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['status'] == 3:
        
                speed = 1
                if 'FS' in playerJSON['data'][i]['modifiers'].split(','):
                    speed = 1.2
                if 'SF' in playerJSON['data'][i]['modifiers'].split(','):
                    speed = 1.5
                if 'SS' in playerJSON['data'][i]['modifiers'].split(','):
                    speed = 0.85
                
                try:
                    with open(f"_AIcache/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}/{playerJSON['data'][i]['leaderboard']['difficulty']['value']} {speed}.json", encoding='ISO-8859-1') as score_json:
                        AiJSON = json.load(score_json)
                    print("Cache Hit")
                    if retest:
                        mapData = tech_calc.loadMapData(key, diffNum, False)
                        AiJSON['tech'] = max(tech_calc.techCalculation(mapData, False) + 0.75, 1)
                        try:
                            os.mkdir(f"_AIcache/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}")
                        except:
                            print("Existing Folder")
                        with open(f"_AIcache/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}/{playerJSON['data'][i]['leaderboard']['difficulty']['value']} {speed}.json", 'w') as score_json:
                            json.dump(AiJSON, score_json, indent=4)

                except:
                    print("Requesting from AI and Calculator")
                    result = s.get(
                        f"https://bs-replays-ai.azurewebsites.net/json/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}/{playerJSON['data'][i]['leaderboard']['difficulty']['value']}/time-scale/{speed}")
                    if result.text == 'Not found':
                        newStar = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['stars']
                        AiJSON['balanced'] = newStar
                        # AiJSON['expected_acc'] = 1
                    else:
                        AiJSON = json.loads(result.text)
                    mapData = tech_calc.loadMapData(key, diffNum, False)
                    AiJSON['tech'] = max(tech_calc.techCalculation(mapData, False) + 0.75, 1)
                    try:
                        os.mkdir(f"_AIcache/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}")
                    except:
                        print("Existing Folder")
                    with open(f"_AIcache/{playerJSON['data'][i]['leaderboard']['song']['hash'].upper()}/{playerJSON['data'][i]['leaderboard']['difficulty']['value']} {speed}.json", 'w') as score_json:
                        json.dump(AiJSON, score_json, indent=4)

                n = AiJSON['balanced']
                if n <= 5:
                    newStar = -3.71 * m.cos(n * m.pi / 6.25) + 3.71
                else:
                    newStar = m.pi * m.sin(m.pi / 1.25) / 2.5 * n + 3.025


                acc = playerJSON['data'][i]['accuracy']
                # tech = max(min(-30 * (AiJSON['expected_acc'] - 1.00333), 2.5), 1)
                tech = AiJSON['tech']
                passPP = 20 * newStar
                accPP = 30 * acc ** tech + \
                    min((tech * (2 * tech + newStar)) / (-1 * acc + 1.01 - (tech / 250)), 1600 * newStar)
                newPP = (passPP + accPP)

                
                newStats[i]['name'] = playerJSON['data'][i]['leaderboard']['song']['name']
                newStats[i]['diff'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['difficultyName']
                newStats[i]['newStar'] = newStar
                newStats[i]['oldStar'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['stars']
                newStats[i]['Modifiers'] = playerJSON['data'][i]['modifiers']
                newStats[i]['oldPP'] = playerJSON['data'][i]['pp']
                newStats[i]['acc'] = acc
                newStats[i]['tech'] = tech
                newStats[i]['newPP'] = newPP


    newStats = sorted(newStats, key=lambda x: x.get('newPP', 0), reverse=True)
    playerName = playerName.replace("|", "")

    filePath = f'_playerStats/{playerName}'

    try:
        with open(f'{filePath}/dataNewPP.json', 'w') as data_json:
            json.dump(newStats, data_json, indent=4)
    except FileNotFoundError:
        os.mkdir(str(f'{filePath}'))
        with open(f'{filePath}/dataNewPP.json', 'w') as data_json:
            json.dump(newStats, data_json, indent=4)
    
    newStats = sorted(newStats, key=lambda x: x.get('newStar', 0), reverse=True)
    with open(f'{filePath}/dataStar.json', 'w') as data_json:
        json.dump(newStats, data_json, indent=4)

    newStats = sorted(newStats, key=lambda x: x.get('acc', 0), reverse=True)
    with open(f'{filePath}/dataAcc.json', 'w') as data_json:
        json.dump(newStats, data_json, indent=4)

    newStats = sorted(newStats, key=lambda x: x.get('tech', 0), reverse=True)
    with open(f'{filePath}/dataTech.json', 'w') as data_json:
        json.dump(newStats, data_json, indent=4)

    newStats = sorted(newStats, key=lambda x: x.get('oldPP', 0), reverse=True)
    with open(f'{filePath}/dataOldPP.json', 'w') as data_json:
        json.dump(newStats, data_json, indent=4)











print("Re-test tech calculator? y/n")
retest = input()
if retest.lower() == 'y':
    retest = True
else:
    retest = False

for i in range(0, len(playerTestList)):
    newPlayerStats(playerTestList[i], 500, retest)
    print(f"Finished {playerTestList[i]}")


print("done")
print("Press Enter to Exit")
input()
