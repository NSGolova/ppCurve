import json
import requests
import numpy as m
import os
import Tech_Calculator.tech_calc as tech_calc
import Tech_Calculator._BackendFiles.setup as setup

playerTestList = [2769016623220259,76561198059961776,76561198072855418,76561198075923914,76561198255595858,76561198404774259, 
    76561198225048252, 76561198110147969, 76561198081152434, 76561198204808809, 76561198072431907, 76561198989311828, 76561198960449289, 
    76561199104169308, 3225556157461414, 76561198410971373, 76561198153101808, 76561197995162898, 2169974796454690, 76561198166289091, 
    76561198285246326, 76561198802040781]

# playerTestList = [76561198285246326, 76561198802040781]

def searchDiffNum(diffNum, diffList):
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
    key = JSON['data'][i]['leaderboard']['song']['id']
    key = key.replace('x', '')
    return key

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
            diffIndex = searchDiffNum(diffNum, playerJSON['data'][i]['leaderboard']['song']['difficulties'])
            key = getKey(playerJSON)
            if playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['status'] == 3:
                speed = convertSpeed(playerJSON['data'][i]['modifiers'].split(','))
                songStats = setup.load_Song_Stats(playerJSON['data'][i], speed, key, retest, versionNum)

                AIStar = songStats['AIstats']['balanced']

                playerACC = playerJSON['data'][i]['accuracy']
                # tech = max(min(-30 * (AiJSON['expected_acc'] - 1.00333), 2.5), 1)
                tech = songStats['lackStats']['tech']
                

                
                AIpp = (passPP + accPP)

                
                newStats[i]['name'] = playerJSON['data'][i]['leaderboard']['song']['name']
                newStats[i]['diff'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['difficultyName']
                newStats[i]['newStar'] = AIStar
                newStats[i]['oldStar'] = playerJSON['data'][i]['leaderboard']['song']['difficulties'][diffIndex]['stars']
                newStats[i]['Modifiers'] = playerJSON['data'][i]['modifiers']
                newStats[i]['oldPP'] = playerJSON['data'][i]['pp']
                newStats[i]['acc'] = playerACC
                newStats[i]['tech'] = tech
                newStats[i]['AIpp'] = AIpp


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
