import json
import requests
import numpy as m
import os
import Tech_Calculator.tech_calc as tech_calc
import Tech_Calculator._BackendFiles.setup as setup
import math

playerTestList = [2769016623220259,76561198059961776,76561198072855418,76561198075923914,76561198255595858,76561198404774259, 
    76561198225048252, 76561198110147969, 76561198081152434, 76561198204808809, 76561198072431907, 76561198989311828, 76561198960449289, 
    76561199104169308, 3225556157461414, 76561198410971373, 76561198153101808, 76561197995162898, 2169974796454690, 76561198166289091, 
    76561198285246326, 76561198802040781]

# playerTestList = [76561198285246326, 76561198802040781]

def searchDiffIndex(diffNum, diffList):
    for f in range(0, len(diffList)):
        if diffList[f]['value'] == diffNum:
            return f
def convertSpeed(listOfMods):
    speed = 1
    if 'FS' in listOfMods:
        speed = 1.2
    if 'SF' in listOfMods:
        speed = 1.5
    if 'SS' in listOfMods:
        speed = 0.85
    return speed
def getKey(JSON):
    key = JSON['leaderboard']['song']['id']
    key = key.replace('x', '')
    return key
def curveAccMulti(acc):
    pointList = [[1,      7],[0.999,  5.8],[0.9975, 4.7],[0.995,  3.76],[0.9925, 3.17],[0.99,   2.73],[0.9875, 2.38],[0.985,  2.1],
    [0.9825, 1.88],[0.98,   1.71],[0.9775, 1.57],[0.975,  1.45],[0.9725, 1.37],[0.97,   1.31],[0.965,  1.20],[0.96,   1.11],
    [0.955,  1.045],[0.95,   1],[0.94,   0.94],[0.93,   0.885],[0.92,   0.835],[0.91,   0.79],[0.9,    0.75],[0.875,  0.655],
    [0.85,   0.57],[0.825,  0.51],[0.8,    0.47],[0.75,   0.40],[0.7,    0.34],[0.65,   0.29],[0.6,    0.25],[0.0,    0.0]]
    for i in range(0, len(pointList)):
        if pointList[i][0] <= acc:
            break
    
    if i == 0:
        i = 1
    
    middle_dis = (acc - pointList[i-1][0]) / (pointList[i][0] - pointList[i-1][0])

    return pointList[i-1][1] + middle_dis * (pointList[i][1] - pointList[i-1][1])
def curveReverseAccMulti(multi):
    pointList = [[7, 1], [5.8, 0.999], [4.7, 0.9975], [3.76, 0.995], [3.17, 0.9925], [2.73, 0.99], 
    [2.38, 0.9875], [2.1, 0.985], [1.88, 0.9825], [1.71, 0.98], [1.57, 0.9775], [1.45, 0.975], 
    [1.37, 0.9725], [1.31, 0.97], [1.2, 0.965], [1.11, 0.96], [1.045, 0.955], [1, 0.95], [0.94, 0.94], 
    [0.885, 0.93], [0.835, 0.92], [0.79, 0.91], [0.75, 0.9], [0.655, 0.875], [0.57, 0.85], [0.51, 0.825], 
    [0.47, 0.8], [0.4, 0.75], [0.34, 0.7], [0.29, 0.65], [0.25, 0.6], [0.0, 0.0]]
    for i in range(0, len(pointList)):
        if pointList[i][0] <= multi:
            break

    if i == 0:
        i = 1

    middle_dis = (multi - pointList[i-1][0]) / (pointList[i][0] - pointList[i-1][0])

    return pointList[i-1][1] + middle_dis * (pointList[i][1] - pointList[i-1][1])

def load_Song_Stats(dataJSON, speed, key, retest=False, versionNum=-1):
    s = requests.Session()
    diffNum = dataJSON['leaderboard']['difficulty']['value']
    diffIndex = searchDiffIndex(diffNum, dataJSON['leaderboard']['song']['difficulties'])
    hash = dataJSON['leaderboard']['song']['hash'].upper()
    AiJSON = {}
    try:
        with open(f"_AIcache/{hash}/{diffNum} {speed}.json", encoding='ISO-8859-1') as score_json:
            AiJSON = json.load(score_json)
        print("Cache Hit")
        try:
            cacheVNum = AiJSON['versionNum']
        except:
            cacheVNum = -1
        finally:
            if retest and cacheVNum != versionNum:
                infoData = setup.loadInfoData(key, False)
                mapData = setup.loadMapData(key, diffNum, False)
                bpm = infoData['_beatsPerMinute']
                AiJSON['lackStats'] = tech_calc.mapCalculation(mapData, bpm, False, False)
                AiJSON['versionNum'] = versionNum
                # result = s.get(
                #     f"https://bs-replays-ai.azurewebsites.net/json/{hash}/{diffNum}/time-scale/{speed}")
                # if result.text == 'Not found':
                #     AiJSON['AIstats'] = {}
                #     AiJSON['AIstats']['balanced'] = 0
                #     AiJSON['AIstats']['expected_acc'] = 0
                #     AiJSON['AIstats']['passing_difficulty'] = 0
                #     # AiJSON['expected_acc'] = 1
                # else:
                #     AiJSON['AIstats'] = json.loads(result.text)
                try:
                    os.mkdir(f"_AIcache/{hash}")
                except:
                    print("Existing Folder")
                with open(f"_AIcache/{hash}/{diffNum} {speed}.json", 'w') as score_json:
                    json.dump(AiJSON, score_json, indent=4)

    except:
        print("Requesting from AI and Calculator")
        result = s.get(
            f"https://bs-replays-ai.azurewebsites.net/json/{hash}/{diffNum}/time-scale/{speed}")
        if result.text == 'Not found':
            newStar = dataJSON['leaderboard']['song']['difficulties'][diffIndex]['stars']
            AiJSON['AIstats'] = {}
            AiJSON['AIstats']['balanced'] = 0
            AiJSON['AIstats']['expected_acc'] = 0
            AiJSON['AIstats']['passing_difficulty'] = 0
            # AiJSON['expected_acc'] = 1
        else:
            AiJSON['AIstats'] = json.loads(result.text)
        infoData = setup.loadInfoData(key, False)
        mapData = setup.loadMapData(key, diffNum, False)
        bpm = infoData['_beatsPerMinute']
        if mapData != None:
            AiJSON['lackStats'] = tech_calc.mapCalculation(mapData, bpm, False, False)
        else:
            AiJSON['lackStats'] = {'tech': 0, 'passing_difficulty': 0}
        try:
            os.mkdir(f"_AIcache/{hash}")
        except:
            print("Existing Folder")
        with open(f"_AIcache/{hash}/{diffNum} {speed}.json", 'w') as score_json:
            json.dump(AiJSON, score_json, indent=4)
    
    return AiJSON



def newPlayerStats(userID, scoreCount, retest=False, versionNum=-1):
    s = requests.Session()
    songStats = {}
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
            diffIndex = searchDiffIndex(diffNum, playerJSON['data'][i]['leaderboard']['song']['difficulties'])
            key = getKey(playerJSON['data'][i])
            if playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['status'] == 3:
                speed = convertSpeed(playerJSON['data'][i]['modifiers'].split(','))
                songStats = load_Song_Stats(playerJSON['data'][i], speed, key, retest, versionNum)

                AIStar = songStats['AIstats']['balanced']
                AIPassStar = songStats['AIstats']['passing_difficulty']
                AIacc = songStats['AIstats']['expected_acc']
                playerACC = playerJSON['data'][i]['accuracy']
                # tech = max(min(-30 * (AiJSON['expected_acc'] - 1.00333), 2.5), 1)
                tech = songStats['lackStats']['tech']

                AIaccPP = curveAccMulti(AIacc) * AIStar * 30
                AIpassPP = AIPassStar * 20
                AIpp = (AIpassPP + AIaccPP)
                if AIStar == 0:
                    AI600Star = 0
                else:
                    AI600AccStar = AIStar * 600 / AIpp * ((-(math.e**(-AIStar))) + 1)
                    AI600PassStar = AIPassStar * 600 / AIpp * ((-(math.e**(-AIStar))) + 1)



                
                newStats[i]['name'] = playerJSON['data'][i]['leaderboard']['song']['name']
                newStats[i]['diff'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['difficultyName']
                newStats[i]['AIStar'] = AIStar
                newStats[i]['oldStar'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['stars']
                newStats[i]['Modifiers'] = playerJSON['data'][i]['modifiers']
                newStats[i]['oldPP'] = playerJSON['data'][i]['pp']
                newStats[i]['acc'] = playerACC
                newStats[i]['tech'] = tech
                newStats[i]['AIpp'] = AIpp
                newStats[i]['AI600AccStar'] = AI600AccStar
                newStats[i]['AI600PassStar'] = AI600PassStar


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









if __name__ == "__main__":
    print("Re-test tech calculator? y/n")
    retest = input()
    if retest.lower() == 'y':
        retest = True
        try:
            f = open('Tech_Calculator/_BackendFiles/techversion.txt', 'r') # Use This to try and find an existing file
            versionNum = int(f.read()) + 1
            f = open('Tech_Calculator/_BackendFiles/techversion.txt', 'w')
            f.write(str(versionNum))
            f.close()
        except FileNotFoundError:
            try:
                f = open('_BackendFiles/techversion.txt', 'r')  # Use This to try and find an existing file
                versionNum = int(f.read()) + 1
                f = open('Tech_Calculator/_BackendFiles/techversion.txt', 'w')
                f.write(str(versionNum))
                f.close()
            except FileNotFoundError:
                try:
                    f = open('Tech_Calculator/_BackendFiles/techversion.txt', 'w')
                except:
                    f = open('_BackendFiles/techversion.txt', 'w')
                f.write(str(0))
                versionNum = 0
        finally:
            f.close()
    else:
        retest = False
        versionNum = -1

    for i in range(0, len(playerTestList)):
        newPlayerStats(playerTestList[i], 500, retest, versionNum)
        print(f"Finished {playerTestList[i]}")
    print("done")
    print("Press Enter to Exit")
    input()
