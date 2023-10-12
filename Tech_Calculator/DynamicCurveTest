import json
import requests
import os
import Tech_Calculator.tech_calc as tech_calc
import Tech_Calculator._BackendFiles.setup as setup
import numpy as np
import matplotlib.pyplot as plt


def searchDiffIndex(diffNum, diffList):
    for f in range(0, len(diffList)):
        if diffList[f]['value'] == diffNum:
            return f


def newCurve(diff, tech, pattern):
    pointList = [[1.0, 7.424],
                 [0.999, 6.241],
                 [0.9975, 5.158],
                 [0.995, 4.010],
                 [0.9925, 3.241],
                 [0.99, 2.700],
                 [0.9875, 2.303],
                 [0.985, 2.007],
                 [0.9825, 1.786],
                 [0.98, 1.618],
                 [0.9775, 1.490],
                 [0.975, 1.392],
                 [0.9725, 1.315],
                 [0.97, 1.256],
                 [0.965, 1.167],
                 [0.96, 1.094],
                 [0.955, 1.039],
                 [0.95, 1.000],
                 [0.94, 0.931],
                 [0.93, 0.867],
                 [0.92, 0.813],
                 [0.91, 0.768],
                 [0.9, 0.729],
                 [0.875, 0.650],
                 [0.85, 0.581],
                 [0.825, 0.522],
                 [0.8, 0.473],
                 [0.75, 0.404],
                 [0.7, 0.345],
                 [0.65, 0.296],
                 [0.6, 0.256],
                 [0.0, 0.000]]
    # Nerf curve by 5% globally
    nerf = 0.95
    # Buff based on pass rating
    passbuff = 0.0025
    for i in range(0, len(pointList)):
        pointList[i][1] = pointList[i][1] * nerf
        pointList[i][1] = pointList[i][1] * (1 + passbuff * diff)

    # Buff accvalue% and upper based on tech rating
    # accvalue based on pass rating?
    if diff >= 10:
        accvalue = 0.94
    elif diff >= 5:
        accvalue = 0.95
    else:
        accvalue = 0.96
    techbuff = 0.0025
    for i in range(0, len(pointList)):
        if pointList[i][0] >= accvalue:
            pointList[i][1] = pointList[i][1] * (1 + techbuff * tech)

    # Nerf accvalue% and lower based on pattern rating
    # Cap at 1
    if pattern > 1:
        pattern = 1
    patternnerf = 0.05
    patternbuff = 0.05
    for i in range(0, len(pointList)):
        if pointList[i][0] < accvalue:
            pointList[i][1] = pointList[i][1] * (1 - patternnerf * pattern)
        if pointList[i][0] >= accvalue:
            pointList[i][1] = pointList[i][1] * (1 + patternbuff * pattern)

    # Curve dump here
    print(F"{pointList}")
    # Plotting the Graph
    pointX = []
    pointY = []
    for i in range(0, len(pointList)):
        pointX.append(pointList[i][0])
        pointY.append(pointList[i][1])
    x = np.array(pointX)
    y = np.array(pointY)
    plt.plot(x, y)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()


def load_Song_Stats(speed, key, hash):
    s = requests.Session()
    AiJSON = {}

    infoData = setup.loadInfoData(key, False)
    mapData = setup.loadMapData(key, diffNum, False)
    bpm = infoData['_beatsPerMinute'] * speed
    AiJSON['lackStats'] = tech_calc.mapCalculation(mapData, bpm, False, False)
    AiJSON['versionNum'] = -1
    result = s.get(
        f"https://api.beatleader.xyz/leaderboards/hash/{hash}")
    if result.text == 'Not found':
        AiJSON['AIstats'] = {}
        AiJSON['AIstats']['balanced'] = 0
        AiJSON['AIstats']['expected_acc'] = 0
        AiJSON['AIstats']['passing_difficulty'] = 0
        # AiJSON['expected_acc'] = 1
    else:
        AiJSON['AIstats'] = json.loads(result.text)
    try:
        os.mkdir(f"_AIcache/{hash}")
    except:
        print("Existing Folder")
    with open(f"_AIcache/{hash}/{diffNum} {speed}.json", 'w') as score_json:
        json.dump(AiJSON, score_json, indent=4)

    return AiJSON


def requestCurveData(mapHash, diffNum, key):
    s = requests.Session()
    songStats = load_Song_Stats(1, key, mapHash)

    result = s.get(
        f"https://api.beatleader.xyz/map/hash/{mapHash}/")
    mapData = json.loads(result.text)

    print(f"{mapData['name']}:")
    diff = searchDiffIndex(diffNum, mapData['difficulties'])
    passRating = mapData['difficulties'][diff]['passRating']
    tech = mapData['difficulties'][diff]['techRating']
    pattern = songStats['lackStats']['avg_pattern_rating']
    newCurve(passRating, tech, pattern)


if __name__ == "__main__":
    print("input map key")
    mapKey = input()
    mapKey = mapKey.replace("!bsr ", "")
    infoData = setup.loadInfoData(mapKey)
    availableDiffs = setup.findStandardDiffs(setup.findSongPath(mapKey))
    if len(availableDiffs) > 1:
        print(f'Choose Diff num: {availableDiffs}')
        diffNum = int(input())
    else:
        diffNum = availableDiffs[0]
        print(f'autoloading {diffNum}')
    # TODO: Automate hash fetching
    print("input map hash")
    mapHash = input()
    requestCurveData(mapHash, diffNum, mapKey)
