import math
import sys
sys.path.insert(0, 'Tech_Calculator')
sys.path.insert(0, '_BackendFiles')
import _BackendFiles.setup as setup
from packaging.version import parse
import numpy as np
from scipy.special import comb
import time
import copy
from collections import deque


# Works for both V2 and V3
# Easy = 1, Normal = 3, Hard = 5, Expert = 7, Expert+ = 9
# b = time, x and y = grid location from bottom left, a = angle offset, c = left or right respectively, d = direction
cut_direction_index = [90, 270, 180, 0, 135, 45, 225, 315, 270]
right_handed_angle_strain_forehand = 247.5  # Most comfortable angle to aim for right hand 270 - 45 or 247.5
left_handed_angle_strain_forehand = 292.5  # 270 + 45 or 292.5


def average(lst, setLen=0):  # Returns the averate of a list of integers
    if len(lst) > 0:
        if setLen == 0:
            return sum(lst) / len(lst)
        else:
            return sum(lst) / setLen
    else:
        return 0


def bernstein_poly(i, n, t):
    return comb(n, i) * (t ** (n - i)) * (1 - t) ** i


def bezier_curve(points, nTimes=1000):
    nPoints = len(points)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])
    t = np.linspace(0.0, 1.0, nTimes)
    polynomial_array = np.array([bernstein_poly(i, nPoints - 1, t) for i in range(0, nPoints)])
    return list(np.dot(xPoints, polynomial_array)), list(np.dot(yPoints, polynomial_array))


def TimeFromBeat(beat):
    if len(bpmEvents) == 0:
        return RawTimeFromBeat(beat, BPM)
    lastChange = [bpm for bpm in bpmEvents if bpm['b'] < beat]
    return lastChange[-1]['t'] + RawTimeFromBeat(beat - lastChange[-1]['b'], lastChange[-1]['m'])


def BeatFromTime(time):
    if len(bpmEvents) == 0:
        return RawBeatFromTime(time, BPM)
    lastChange = [bpm for bpm in bpmEvents if bpm['t'] < time]
    return lastChange[-1]['b'] + RawBeatFromTime(time - lastChange[-1]['t'], lastChange[-1]['m'])


def RawTimeFromBeat(beat, bpm):
    if bpm <= 0:
        return 0
    return beat / bpm * 60


def RawBeatFromTime(time, bpm):
    if bpm <= 0:
        return 0
    return time / 60 * bpm


def findBPM(beat):
    lastChange = [bpm for bpm in bpmEvents if bpm['b'] < beat]
    return lastChange[-1]['m']


def handleBPM(mapData: list, bpm):
    global BPM
    BPM = bpm
    global bpmEvents
    bpmEvents = []
    if 'bpmEvents' not in mapData:
        newEvent = {'b': -1, 'm': BPM, 't': -1}
        bpmEvents.append(newEvent)
        block = [block for block in mapData['colorNotes']]
        for i in range(0, len(block)):
            block[i]['t'] = TimeFromBeat(block[i]['b'])
        return mapData
    bpmEvents = [bpm for bpm in mapData['bpmEvents']]
    newEvent = {'b': -1, 'm': BPM, 't': -1}
    bpmEvents.append(newEvent)
    if len(bpmEvents) > 1:
        bpmEvents.sort(key=lambda b: b['b'])
        currentTime = 0
        for i in range(1, len(bpmEvents)):
            currentTime += RawTimeFromBeat(bpmEvents[i]['b'] - bpmEvents[i - 1]['b'], bpmEvents[i - 1]['m'])
            bpmEvents[i]['t'] = currentTime

    block = [block for block in mapData['colorNotes']]
    for i in range(0, len(block)):
        block[i]['t'] = TimeFromBeat(block[i]['b'])

    return mapData


def V2_to_V3(V2mapData: dict):  # Convert V2 JSON to V3
    newMapData = {'colorNotes': [], 'bombNotes': [],
                  'obstacles': [], 'bpmEvents': []}  # I have to initialize this beforehand or python gets grumpy
    for i in range(0, len(V2mapData['_notes'])):
        if V2mapData['_notes'][i]['_type'] in [0, 1]:
            # In V2, Bombs and Notes were stored in the same _type key. The "if" just separates them
            newMapData['colorNotes'].append({'b': V2mapData['_notes'][i][
                '_time']})  # Append to make a new entry into the list to store the dictionary
            newMapData['colorNotes'][-1]['x'] = V2mapData['_notes'][i]['_lineIndex']
            newMapData['colorNotes'][-1]['y'] = V2mapData['_notes'][i]['_lineLayer']
            newMapData['colorNotes'][-1]['a'] = 0  # Angle offset didn't exist in V2. will always be 0
            newMapData['colorNotes'][-1]['c'] = V2mapData['_notes'][i]['_type']
            newMapData['colorNotes'][-1]['d'] = V2mapData['_notes'][i]['_cutDirection']
        elif V2mapData['_notes'][i]['_type'] == 3:  # Bombs
            newMapData['bombNotes'].append({'b': V2mapData['_notes'][i]['_time']})
            newMapData['bombNotes'][-1]['x'] = V2mapData['_notes'][i]['_lineIndex']
            newMapData['bombNotes'][-1]['y'] = V2mapData['_notes'][i]['_lineLayer']
    for i in range(0, len(V2mapData['_obstacles'])):
        newMapData['obstacles'].append({'b': V2mapData['_obstacles'][i]['_time']})
        newMapData['obstacles'][-1]['x'] = V2mapData['_obstacles'][i]['_lineIndex']
        if V2mapData['_obstacles'][i]['_type']:  # V2 wall type defines crouch or full walls
            newMapData['obstacles'][-1]['y'] = 2
            newMapData['obstacles'][-1]['h'] = 3
        else:
            newMapData['obstacles'][-1]['y'] = 0
            newMapData['obstacles'][-1]['h'] = 5
        newMapData['obstacles'][-1]['d'] = V2mapData['_obstacles'][i]['_duration']
        newMapData['obstacles'][-1]['w'] = V2mapData['_obstacles'][i]['_width']
    for i in range(0, len(V2mapData['_events'])):
        if V2mapData['_events'][i]['_type'] == 100:
            newMapData['bpmEvents'].append({'b': V2mapData['_events'][i]['_time']})
            newMapData['bpmEvents'][-1]['m'] = V2mapData['_events'][i]['_floatValue']
    return newMapData


def mapPrep(mapData):
    try:
        mapVersion = parse(mapData['version'])
    except KeyError:
        try:
            mapVersion = parse(mapData['_version'])
        except KeyError:
            try:
                mapData['_notes']
                mapVersion = parse('2.0.0')
            except KeyError:
                try:
                    mapData['colorNotes']
                    mapVersion = parse('3.0.0')
                except KeyError:
                    print("Unknown Map Type. Exiting")
                    exit()
    if mapVersion < parse('3.0.0'):  # Try to figure out if the map is the V2 or V3 format
        newMapData = V2_to_V3(mapData)  # Convert to V3
    else:
        newMapData = mapData
    return newMapData


def splitMapData(mapData: dict, leftOrRight: int):  # False or 0 = Left, True or 1 = Right, 2 = Bombs
    if leftOrRight == 0:
        blockList = [block for block in mapData['colorNotes'] if block['c'] == 0]
    elif leftOrRight == 1:
        blockList = [block for block in mapData['colorNotes'] if block['c'] == 1]
    else:
        blockList = [bomb for bomb in mapData['bombNotes']]
    return blockList


def calculateBaseEntryExit(cBlockP, cBlockA):
    entry = [cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667,
             cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
    exit = [cBlockP[0] * 0.333333 + math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667,
            cBlockP[1] * 0.333333 + math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
    return entry, exit


def isSameDirection(pBlockA, cBlockA):
    pBlockA = mod(pBlockA, 360)
    cBlockA = mod(cBlockA, 360)
    if abs(pBlockA - cBlockA) <= 180:
        if abs(pBlockA - cBlockA) < 67.5:
            return True
    else:
        if 360 - abs(pBlockA - cBlockA) < 67.5:
            return True
    return False


def reverseCutDirection(angle):
    if angle >= 180:
        return angle - 180
    else:
        return angle + 180


def swapPositions(lis: list, pos1, pos2):
    lis[pos1], lis[pos2] = lis[pos2], lis[pos1]
    return lis


def mod(x, m):
    return (x % m + m) % m


def toString(direction):
    if 67.5 < direction <= 112.5:
        return "Up"
    elif 247.5 < direction <= 292.5:
        return "Down"
    elif 157.5 < direction <= 202.5:
        return "Left"
    elif 0 <= direction <= 22.5 or 337.5 < direction < 360:
        return "Right"
    elif 112.5 < direction <= 157.5:
        return "Up-Left"
    elif 22.5 < direction <= 67.5:
        return "Up-Right"
    elif 202.5 < direction <= 247.5:
        return "Down-Left"
    elif 292.5 < direction <= 337.5:
        return "Down-Right"
    return False


# Try to find if placement match for slider
def isSlider(prev, next, direction, dot):
    if dot is True:
        if prev['x'] == next['x'] and prev['y'] == next['y']:
            return True
    if 67.5 < direction <= 112.5:
        if prev['y'] < next['y']:
            return True
    elif 247.5 < direction <= 292.5:
        if prev['y'] > next['y']:
            return True
    elif 157.5 < direction <= 202.5:
        if prev['x'] > next['x']:
            return True
    elif 0 <= direction <= 22.5 or 337.5 < direction < 360:
        if prev['x'] < next['x']:
            return True
    elif 112.5 < direction <= 157.5:
        if prev['y'] < next['y']:
            return True
        if prev['x'] > next['x']:
            return True
    elif 22.5 < direction <= 67.5:
        if prev['y'] < next['y']:
            return True
        if prev['x'] < next['x']:
            return True
    elif 202.5 < direction <= 247.5:
        if prev['y'] > next['y']:
            return True
        if prev['x'] > next['x']:
            return True
    elif 292.5 < direction <= 337.5:
        if prev['y'] > next['y']:
            return True
        if prev['x'] < next['x']:
            return True
    return False


# Find next angle by using last known position, next position and a guide angle
def findAngleViaPosition(mapSplitData: list, i, h, guideAngle, pattern):
    if pattern is True:
        pBlockP = [mapSplitData[h]['x'], mapSplitData[h]['y']]
    else:
        pBlockP = simulateSwingPos(mapSplitData[h]['x'], mapSplitData[h]['y'], guideAngle)
    cBlockP = [mapSplitData[i]['x'], mapSplitData[i]['y']]
    currentAngle = reverseCutDirection(mod(math.degrees(math.atan2(pBlockP[1] - cBlockP[1],
                                                                   pBlockP[0] - cBlockP[0])), 360))
    if isSameDirection(currentAngle, guideAngle) is False and pattern is True:
        currentAngle = reverseCutDirection(currentAngle)
    if isSameDirection(currentAngle, guideAngle) is True and pattern is False:
        currentAngle = reverseCutDirection(currentAngle)
    return currentAngle


def simulateSwingPos(x, y, direction):
    return x + 5 * math.cos(math.radians(direction)), y + 5 * math.sin(math.radians(direction))


# Find pattern note if possible and then swap element for them to be in order
def handlePattern(mapSplitData: list):
    length = 0
    for n in range(0, len(mapSplitData) - 2):
        if length > 0:
            length = length - 1
            continue
        if mapSplitData[n]['b'] == mapSplitData[n + 1]['b']:  # Pattern found
            length = len([no for no in mapSplitData if no['b'] == mapSplitData[n]['b']]) - 1  # Get length of pattern
            Arrow = [dir for dir in mapSplitData if (dir['d'] != 8 and dir['b'] == mapSplitData[n]['b'])]
            if len(Arrow) == 0:  # Handle case if there's no direction available
                # Check for a previous direction, get last known arrow and simulate flow
                foundArrow = [a for a in mapSplitData if a['d'] != 8 and a['b'] > mapSplitData[n]['b']]
                if len(foundArrow) > 0:
                    direction = reverseCutDirection(mod(cut_direction_index[foundArrow[0]['d']] +
                                                        foundArrow[0]['a'], 360))
                    for i in range(mapSplitData.index(foundArrow[0]) - 1, n, -1):
                        if mapSplitData[i + 1]['b'] - mapSplitData[i]['b'] >= 0.25:
                            direction = reverseCutDirection(direction)
                else:  # Can't find anything that could help, just going to ignore that pattern
                    continue
            else:
                direction = reverseCutDirection(mod(cut_direction_index[Arrow[-1]['d']] + Arrow[-1]['a'], 360))
            pos = simulateSwingPos(mapSplitData[n - 1]['x'], mapSplitData[n - 1]['y'], direction)
            distance = []
            for i in range(n, n + length + 1):  # Find all the distance
                distance.append(math.sqrt((pos[1] - mapSplitData[i]['y']) ** 2 + (pos[0] - mapSplitData[i]['x']) ** 2))
            for i in range(0, len(distance)):
                for j in range(n, n + length):  # We want the closest distance to be the head
                    if distance[j - n + 1] < distance[j - n]:
                        mapSplitData = swapPositions(mapSplitData, j, j + 1)
                        distance = swapPositions(distance, j - n + 1, j - n)
    return mapSplitData


# Find angle in degree for each note
# Proceed to fix some possible issue afterward
# Also detect bomb "reset"
def flowDetector(mapSplitData: list, bombData: list, leftOrRight):
    if len(mapSplitData) < 2:
        return mapSplitData
    if leftOrRight:
        testValue = -45
    else:
        testValue = 45
    mapSplitData = sorted(mapSplitData, key=lambda d: d['b'])
    handlePattern(mapSplitData)
    # Fill the list preemptively
    for i in range(0, len(mapSplitData)):
        mapSplitData[i]['bomb'] = False
        mapSplitData[i]['pattern'] = False
        mapSplitData[i]['head'] = False
    # Find the first note
    if mapSplitData[0]['d'] == 8:
        if mapSplitData[1]['d'] != 8 and mapSplitData[1]['b'] - mapSplitData[0]['b'] <= 0.125:
            mapSplitData[0]['dir'] = mod(cut_direction_index[mapSplitData[1]['d']] + mapSplitData[1]['a'], 360)
        else:
            # Use the first arrow found to reverse search the direction
            tempList = [a for a in mapSplitData if a['d'] != 8]
            if len(tempList) > 0:
                found = tempList[0]
                foundAngle = mod(cut_direction_index[found['d']] + found['a'], 360)
                for i in range(mapSplitData.index(found), 0, -1):
                    if mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] >= 0.25:
                        mapSplitData[0]['dir'] = reverseCutDirection(foundAngle)
            elif mapSplitData[0]['y'] >= 2:  # Otherwise, use position instead
                mapSplitData[0]['dir'] = 90  # Assume up for top row
            else:
                mapSplitData[0]['dir'] = 270  # Otherwise down
    else:
        mapSplitData[0]['dir'] = mod(cut_direction_index[mapSplitData[0]['d']] + mapSplitData[0]['a'], 360)
    # Find the second note
    if mapSplitData[1]['d'] == 8:
        # Pattern?
        if (mapSplitData[1]['b'] - mapSplitData[0]['b'] <= 0.25
            and isSlider(mapSplitData[0], mapSplitData[1], mapSplitData[0]['dir'], True)) \
                or mapSplitData[1]['b'] - mapSplitData[0]['b'] <= 0.125:
            mapSplitData[1]['dir'] = findAngleViaPosition(mapSplitData, 1, 0, mapSplitData[0]['dir'], True)
            if mapSplitData[0]['d'] == 8:
                mapSplitData[0]['dir'] = mapSplitData[1]['dir']
            mapSplitData[1]['pattern'] = True
            mapSplitData[0]['pattern'] = True
            mapSplitData[0]['head'] = True
        else:
            # Bomb stuff
            bomb = [b['y'] for b in bombData if mapSplitData[0]['b'] < b['b'] <= mapSplitData[1]['b']
                    and mapSplitData[1]['x'] == b['x']]
            if len(bomb) > 0:  # Bomb found between the two notes, apply a direction based on bomb position
                if bomb[-1] <= 0:
                    mapSplitData[1]['dir'] = 270
                elif bomb[-1] == 1:
                    if mapSplitData[1]['y'] == 0:
                        mapSplitData[1]['dir'] = 90
                    else:
                        mapSplitData[1]['dir'] = 270
                elif bomb[-1] >= 2:
                    mapSplitData[i]['dir'] = 90
                mapSplitData[i]['bomb'] = True
            else:
                mapSplitData[1]['dir'] = findAngleViaPosition(mapSplitData, 1, 0, mapSplitData[0]['dir'], False)
    else:
        if (mapSplitData[1]['b'] - mapSplitData[0]['b'] <= 0.25
            and isSlider(mapSplitData[0], mapSplitData[1], mapSplitData[0]['dir'], False)) \
                or mapSplitData[1]['b'] - mapSplitData[0]['b'] <= 0.125:
            mapSplitData[0]['head'] = True
            mapSplitData[0]['pattern'] = True
            mapSplitData[1]['pattern'] = True
        mapSplitData[1]['dir'] = mod(cut_direction_index[mapSplitData[1]['d']] + mapSplitData[1]['a'], 360)
    # Analyze the rest of the notes
    for i in range(2, len(mapSplitData) - 1):
        if mapSplitData[i]['d'] == 8:  # Dot note
            # If under 0.25 and placement matches, probably a pattern
            if (mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] <= 0.25
                and isSlider(mapSplitData[i - 1], mapSplitData[i], mapSplitData[i - 1]['dir'], True)) \
                    or mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] <= 0.125:
                mapSplitData[i]['dir'] = findAngleViaPosition(mapSplitData, i, i - 1, mapSplitData[i - 1]['dir'], True)
                if mapSplitData[i - 1]['d'] == 8:
                    mapSplitData[i - 1]['dir'] = mapSplitData[i]['dir']
                mapSplitData[i]['bomb'] = mapSplitData[i - 1]['bomb']
                mapSplitData[i]['pattern'] = True
                # Mark the head of the pattern
                if mapSplitData[i - 1]['pattern'] is False:
                    mapSplitData[i - 1]['head'] = True
                    mapSplitData[i - 1]['pattern'] = True
                continue
            else:
                # Bomb stuff
                bomb = [b['y'] for b in bombData if mapSplitData[i - 1]['b'] < b['b'] <= mapSplitData[i]['b']
                        and mapSplitData[i]['x'] == b['x']]
                if len(bomb) > 0:  # Bomb found between the two notes, apply a direction based on bomb position
                    if bomb[-1] <= 0:
                        mapSplitData[i]['dir'] = 270
                    elif bomb[-1] == 1:
                        if mapSplitData[i]['y'] == 0:
                            mapSplitData[i]['dir'] = 90
                        else:
                            mapSplitData[i]['dir'] = 270
                    elif bomb[-1] >= 2:
                        mapSplitData[i]['dir'] = 90
                    mapSplitData[i]['bomb'] = True
                    continue
                mapSplitData[i]['dir'] = findAngleViaPosition(mapSplitData, i, i - 1, mapSplitData[i - 1]['dir'], False)
            # Check if the direction found work, otherwise check with the testValue
            if isSameDirection(mapSplitData[i - 1]['dir'], mapSplitData[i]['dir']) is False:
                if mapSplitData[i + 1]['d'] != 8:
                    nextDir = mod(cut_direction_index[mapSplitData[i + 1]['d']] + mapSplitData[i + 1]['a'], 360)
                    # Verify next note if possible (not a dot)
                    if isSameDirection(mapSplitData[i]['dir'], nextDir):
                        if isSameDirection(mapSplitData[i]['dir'] + testValue, nextDir) is False:
                            mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] + testValue, 360)
                            continue
                        elif isSameDirection(mapSplitData[i]['dir'] - testValue, nextDir) is False:
                            mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] - testValue, 360)
                            continue
                continue
                # Try with + testValue
            if isSameDirection(mapSplitData[i - 1]['dir'], mapSplitData[i]['dir'] + testValue) is False:
                mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] + testValue, 360)
                continue
                # Try with - testValue
            elif isSameDirection(mapSplitData[i - 1]['dir'], mapSplitData[i]['dir'] - testValue) is False:
                mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] - testValue, 360)
                continue
                # Maybe the note before (dot) is wrong? Attempt to fix here
            if mapSplitData[i - 1]['d'] == 8 and isSameDirection(mapSplitData[i - 2]['dir'],
                                                                 mapSplitData[i - 1]['dir'] + testValue) is False:
                lastDir = mod(mapSplitData[i - 1]['dir'] + testValue, 360)
                if isSameDirection(lastDir, mapSplitData[i]['dir'] + testValue * 2) is False:
                    mapSplitData[i - 1]['dir'] = mod(mapSplitData[i - 1] + testValue, 360)
                    mapSplitData[i]['dir'] = mod(mapSplitData[i] + testValue * 2, 360)
            elif mapSplitData[i - 1]['d'] == 8 and isSameDirection(mapSplitData[i - 2]['dir'],
                                                                   mapSplitData[i - 1]['dir'] - testValue) is False:
                lastDir = mod(mapSplitData[i - 1]['dir'] - testValue, 360)
                if isSameDirection(lastDir, mapSplitData[i]['dir'] - testValue * 2) is False:
                    mapSplitData[i - 1]['dir'] = mod(mapSplitData[i - 1] - testValue, 360)
                    mapSplitData[i]['dir'] = mod(mapSplitData[i] - testValue * 2, 360)
        else:  # Arrow note
            mapSplitData[i]['dir'] = mod(cut_direction_index[mapSplitData[i]['d']] + mapSplitData[i]['a'], 360)
            if (mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] <= 0.25
                and isSlider(mapSplitData[i - 1], mapSplitData[i], mapSplitData[i - 1]['dir'], False)) \
                    or mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] <= 0.125:
                mapSplitData[i]['pattern'] = True
                mapSplitData[i]['bomb'] = mapSplitData[i - 1]['bomb']
                if mapSplitData[i - 1]['pattern'] is False:
                    mapSplitData[i - 1]['pattern'] = True
                    mapSplitData[i - 1]['head'] = True
            bomb = [b['y'] for b in bombData if mapSplitData[i - 1]['b'] < b['b'] <= mapSplitData[i]['b']
                    and mapSplitData[i]['x'] == b['x']]
            if len(bomb) > 0:  # Bomb found between the two notes
                mapSplitData[i]['bomb'] = True
                continue
    for i in range(2, len(mapSplitData) - 2):
        # Not a pattern and the note parity only work from before or after
        if mapSplitData[i]['d'] == 8 and mapSplitData[i]['b'] - mapSplitData[i - 1]['b'] >= 0.125:
            if (isSameDirection(mapSplitData[i]['dir'], mapSplitData[i - 1]['dir']) is True and mapSplitData[i]['bomb']
                is False and isSameDirection(mapSplitData[i]['dir'], mapSplitData[i + 1]['dir']) is False) or \
                    ((isSameDirection(mapSplitData[i]['dir'], mapSplitData[i - 1]['dir']) is False and
                      isSameDirection(mapSplitData[i]['dir'], mapSplitData[i + 1]['dir']) is True and
                      mapSplitData[i + 1]['bomb'] is False)):
                #  Attempt to fix the direction using testValue
                if (isSameDirection(mapSplitData[i]['dir'] + testValue, mapSplitData[i - 1]['dir']) is False and
                        isSameDirection(mapSplitData[i]['dir'] + testValue, mapSplitData[i + 1]['dir']) is False):
                    mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] + testValue, 360)
                elif (isSameDirection(mapSplitData[i]['dir'] - testValue, mapSplitData[i - 1]['dir']) is False and
                      isSameDirection(mapSplitData[i]['dir'] - testValue, mapSplitData[i + 1]['dir']) is False):
                    mapSplitData[i]['dir'] = mod(mapSplitData[i]['dir'] - testValue, 360)
    # Handle the last note
    if mapSplitData[-1]['d'] == 8:
        # Pattern?
        if (mapSplitData[-1]['b'] - mapSplitData[-2]['b'] <= 0.25
            and isSlider(mapSplitData[-2], mapSplitData[-1], mapSplitData[-2]['dir'], True)) \
                or mapSplitData[-1]['b'] - mapSplitData[-2]['b'] <= 0.125:
            mapSplitData[-1]['dir'] = findAngleViaPosition(mapSplitData, len(mapSplitData) - 1,
                                                           len(mapSplitData) - 2, mapSplitData[0]['dir'], True)
            if mapSplitData[-2]['d'] == 8:
                mapSplitData[-2]['dir'] = mapSplitData[1]['dir']
            mapSplitData[-1]['pattern'] = True
            # Mark the head
            if mapSplitData[-2]['pattern'] is False:
                mapSplitData[-2]['head'] = True
                mapSplitData[-2]['pattern'] = True
        else:
            # Bomb stuff
            bomb = [b['y'] for b in bombData if mapSplitData[-2]['b'] < b['b'] <= mapSplitData[-1]['b']
                    and mapSplitData[-1]['x'] == b['x']]
            if len(bomb) > 0:  # Bomb found between the two notes, apply a direction based on bomb position
                if bomb[-1] <= 0:
                    mapSplitData[-1]['dir'] = 270
                elif bomb[-1] == 1:
                    if mapSplitData[-1]['y'] == 0:
                        mapSplitData[-1]['dir'] = 90
                    else:
                        mapSplitData[-1]['dir'] = 270
                elif bomb[-1] >= 2:
                    mapSplitData[-1]['dir'] = 90
                mapSplitData[-1]['bomb'] = True
            else:
                mapSplitData[-1]['dir'] = reverseCutDirection(mapSplitData[-2]['dir'])
    else:
        mapSplitData[-1]['dir'] = mod(cut_direction_index[mapSplitData[-1]['d']] + mapSplitData[-1]['a'], 360)
        if (mapSplitData[-1]['b'] - mapSplitData[-2]['b'] <= 0.25
            and isSlider(mapSplitData[-2], mapSplitData[-1], mapSplitData[-2]['dir'], False)) \
                or mapSplitData[-1]['b'] - mapSplitData[-2]['b'] <= 0.125:
            mapSplitData[-1]['pattern'] = True
            mapSplitData[-1]['bomb'] = mapSplitData[-2]['bomb']
            if mapSplitData[-2]['pattern'] is False:
                mapSplitData[-2]['head'] = True
                mapSplitData[-2]['pattern'] = True
        bomb = [b['y'] for b in bombData if mapSplitData[-2]['b'] < b['b'] <= mapSplitData[-1]['b']
                and mapSplitData[-1]['x'] == b['x']]
        if len(bomb) > 0:  # Bomb found between the two notes, apply a direction based on bomb position
            mapSplitData[-1]['bomb'] = True
    return mapSplitData


# Convert notes and patterns into swing data
def processSwing(mapSplitData: list):
    swingData = []
    if len(mapSplitData) < 2:
        return swingData
    # First note
    swingData.append({'time': mapSplitData[0]['b'], 'angle': mapSplitData[0]['dir']})
    swingData[-1]['entryPos'], swingData[-1]['exitPos'] = \
        calculateBaseEntryExit((mapSplitData[0]['x'], mapSplitData[0]['y']), mapSplitData[0]['dir'])
    for i in range(1, len(mapSplitData)):
        # Previous note
        pBlockA = swingData[-1]['angle']
        # Current note
        cBlockB = mapSplitData[i]['b']
        cBlockA = mapSplitData[i]['dir']
        cBlockP = [mapSplitData[i]['x'], mapSplitData[i]['y']]
        if mapSplitData[i]['pattern'] is False or mapSplitData[i]['head'] is True:
            swingData.append({'time': cBlockB, 'angle': cBlockA})
            swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
        elif mapSplitData[i]['pattern']:  # Modify the angle and entry or exit position, doesn't create a new swing data
            # Find possible angle based on head placement
            for f in range(i, 0, -1):
                if mapSplitData[f]['head'] is True:
                    cBlockA = findAngleViaPosition(mapSplitData, i, f, pBlockA, True)
                    break
            if isSameDirection(cBlockA, pBlockA) is False:  # Fix angle is necessary
                cBlockA = reverseCutDirection(cBlockA)
            swingData[-1]['angle'] = cBlockA  # Modify last angle saved
            xtest = (swingData[-1]['entryPos'][0] - (
                    cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667)) * math.cos(
                math.radians(cBlockA))
            ytest = (swingData[-1]['entryPos'][1] - (
                    cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.166667)) * math.sin(
                math.radians(cBlockA))
            if xtest <= 0.001 <= ytest:
                swingData[-1]['entryPos'] = [
                    cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667,
                    cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
            else:
                swingData[-1]['exitPos'] = [
                    cBlockP[0] * 0.333333 + math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667,
                    cBlockP[1] * 0.333333 + math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
    return swingData


def swingAngleStrainCalc(swingData: list, leftOrRight):
    strainAmount = 0
    for i in range(0, len(swingData)):
        if swingData[i]['forehand']:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(
                    abs(right_handed_angle_strain_forehand - swingData[i]['angle']) - 180)) / 180) ** 2)
            else:
                strainAmount += 2 * (((180 - abs(
                    abs(left_handed_angle_strain_forehand - swingData[i]['angle']) - 180)) / 180) ** 2)
        else:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(
                    abs(right_handed_angle_strain_forehand - 180 - swingData[i]['angle']) - 180)) / 180) ** 2)
            else:
                strainAmount += 2 * (((180 - abs(
                    abs(left_handed_angle_strain_forehand - 180 - swingData[i]['angle']) - 180)) / 180) ** 2)
    return strainAmount


def bezierAngleStrainCalc(angleData: list, forehand, leftOrRight):
    strainAmount = 0
    for i in range(0, len(angleData)):
        if forehand:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(
                    abs(right_handed_angle_strain_forehand - angleData[i]) - 180)) / 180) ** 2)
            else:
                strainAmount += 2 * (((180 - abs(
                    abs(left_handed_angle_strain_forehand - angleData[i]) - 180)) / 180) ** 2)
        else:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(
                    abs(right_handed_angle_strain_forehand - 180 - angleData[i]) - 180)) / 180) ** 2)
            else:
                strainAmount += 2 * (((180 - abs(
                    abs(left_handed_angle_strain_forehand - 180 - angleData[i]) - 180)) / 180) ** 2)
    return strainAmount


# Split the long list of dictionaries into smaller lists of patterns containing lists of dictionaries
def patternSplitter(swingData: list):
    if len(swingData) < 2:
        return []
    for i in range(0, len(swingData)):  # Swing Frequency Analyzer
        if i > 0 and i + 1 < len(swingData):  # Checks done so we don't try to access data that doesn't exist
            SF = 2 / (swingData[i + 1]['time'] - swingData[i - 1]['time'])  # Swing Frequency
        else:
            SF = 0
        swingData[i]['frequency'] = SF
    patternFound = False
    SFList = [freq['frequency'] for freq in swingData]
    SFmargin = average(SFList) / 32
    patternList = []  # Pattern List
    tempPlist = []  # Temp Pattern List
    for i in range(0, len(swingData)):
        if i > 0:
            # Tries to find Patterns within margin
            if (1 / (swingData[i]['time'] - swingData[i - 1]['time'])) - swingData[i]['frequency'] <= SFmargin:
                if not patternFound:  # Found a pattern and it's the first one?
                    patternFound = True
                    del tempPlist[-1]
                    if len(tempPlist) > 0:  # We only want to store lists with stuff
                        patternList.append(tempPlist)
                    tempPlist = [swingData[i - 1]]  # Store the 1st block of the pattern
                tempPlist.append(swingData[i])  # Store the block we're working on
            else:
                if len(tempPlist) > 0 and patternFound:
                    tempPlist.append(swingData[i])
                    patternList.append(tempPlist)
                    tempPlist = []
                else:
                    patternFound = False
                    tempPlist.append(swingData[i])
        else:
            tempPlist.append(swingData[0])
    return patternList


# Test parity with angle strain
# Apply best swing angle strain
# Set if the swing is a reset (or bomb) or is forehand
def parityPredictor(patternData: list, leftOrRight):
    newPatternData = []
    if len(patternData) == 0:
        return newPatternData
    for p in range(0, len(patternData)):
        testData1 = patternData[p]
        testData2 = copy.deepcopy(patternData[p])
        for i in range(0, len(testData1)):  # Build Forehand TestData Build
            if i > 0:
                if isSameDirection(testData1[i - 1]['angle'], testData1[i]['angle']) is True:
                    testData1[i]['reset'] = True
                    testData1[i]['forehand'] = testData1[i - 1]['forehand']
                else:
                    testData1[i]['reset'] = False
                    testData1[i]['forehand'] = not testData1[i - 1]['forehand']
            else:
                testData1[0]['reset'] = False
                testData1[0]['forehand'] = True
        for i in range(0, len(testData2)):  # Build Banckhand TestData
            if i > 0:
                if isSameDirection(testData2[i - 1]['angle'], testData2[i]['angle']) is True:
                    testData2[i]['reset'] = True
                    testData2[i]['forehand'] = testData2[i - 1]['forehand']
                else:
                    testData2[i]['reset'] = False
                    testData2[i]['forehand'] = not testData2[i - 1]['forehand']
            else:
                testData2[0]['reset'] = False
                testData2[0]['forehand'] = False
        forehandTest = swingAngleStrainCalc(testData1, leftOrRight)
        backhandTest = swingAngleStrainCalc(testData2, leftOrRight)
        if forehandTest <= backhandTest:
            newPatternData += testData1
        elif forehandTest > backhandTest:
            newPatternData += testData2
    for i in range(0, len(newPatternData)):
        newPatternData[i]['angleStrain'] = swingAngleStrainCalc([newPatternData[i]], leftOrRight) * 2
    return newPatternData


def swingCurveCalc(swingData: list, leftOrRight, isuser=True):
    if len(swingData) < 2:
        return [], []
    swingData[0]['pathStrain'] = 0  # First Note cannot really have any path strain
    swingData[0]['positionComplexity'] = 0
    swingData[0]['preDistance'] = 0
    swingData[0]['curveComplexity'] = 0
    swingData[0]['pathAngleStrain'] = 0
    testData = []
    for i in range(1, len(swingData)):
        point0 = swingData[i - 1]['exitPos']  # Curve Beginning
        point1x = point0[0] + 1 * math.cos(math.radians(swingData[i - 1]['angle']))
        point1y = point0[1] + 1 * math.sin(math.radians(swingData[i - 1]['angle']))
        point1 = [point1x, point1y]  # Curve Control Point
        point3 = swingData[i]['entryPos']  # Curve Ending
        point2x = point3[0] - 1 * math.cos(math.radians(swingData[i]['angle']))
        point2y = point3[1] - 1 * math.sin(math.radians(swingData[i]['angle']))
        point2 = [point2x, point2y]  # Curve Control Point
        points = [point0, point1, point2, point3]
        xvals, yvals = bezier_curve(points, nTimes=25)
        xvals.reverse()
        yvals.reverse()
        positionComplexity = 0
        angleChangeList = []
        angleList = []
        distance = 0
        for f in range(1, min(len(xvals), len(yvals))):
            angleList.append(mod(math.degrees(math.atan2(yvals[f] - yvals[f - 1], xvals[f] - xvals[f - 1])), 360))
            distance += math.sqrt((yvals[f] - yvals[f - 1]) ** 2 + (xvals[f] - xvals[f - 1]) ** 2)
            if f > 1:
                angleChangeList.append(180 - abs(abs(angleList[-1] - angleList[-2]) - 180))
        distance -= 0.75
        if i > 1:  # Three swings
            simHandCurPos = swingData[i]['entryPos']
            if swingData[i]['reset'] is False and swingData[i - 1]['reset'] is False:
                simHandPrePos = swingData[i - 2]['entryPos']  # Normal flow
            elif swingData[i]['reset'] is False and swingData[i - 1]['reset'] is True:
                simHandPrePos = swingData[i - 1]['entryPos']  # Reset into normal flow
            elif swingData[i]['reset'] is True:  # Normal flow into reset
                simHandPrePos = swingData[i - 1]['entryPos']
            else:  # Should technically never happen
                simHandPrePos = simHandCurPos
            positionComplexity = math.sqrt(
                (simHandCurPos[1] - simHandPrePos[1]) ** 2 + (simHandCurPos[0] - simHandPrePos[0]) ** 2) ** 2
        lengthOfList = len(angleChangeList) * 0.6
        if swingData[i]['reset']:  # If the pattern is a reset, look less far back
            pathLookback = 0.9
            first = 0.5
            last = 1
        else:
            pathLookback = 0.5
            first = 0.2
            last = 0.8
        pathLookbackIndex = int(len(angleList) * pathLookback)
        firstIndex = int(len(angleChangeList) * first) - 1
        lastIndex = int(len(angleChangeList) * last) - 1
        curveComplexity = abs((lengthOfList * average(angleChangeList[firstIndex:lastIndex]) - 180) / 180)
        # The more the angle difference changes from 180, the more complex the path, /180 to normalize between 0 - 1
        pathAngleStrain = (bezierAngleStrainCalc(angleList[pathLookbackIndex:],
                                                 swingData[i]['forehand'], leftOrRight) / len(angleList)) * 2
        testData.append({'curveComplexityStrain': curveComplexity, 'pathAngleStrain': pathAngleStrain,
                         'positionComplexity': positionComplexity})
        swingData[i]['positionComplexity'] = positionComplexity
        swingData[i]['preDistance'] = distance
        swingData[i]['curveComplexity'] = curveComplexity
        swingData[i]['pathAngleStrain'] = pathAngleStrain
        swingData[i]['pathStrain'] = curveComplexity + pathAngleStrain + positionComplexity
    avehitAngleStrain = average([Stra['angleStrain'] for Stra in swingData])
    avepositionComplexity = average([Stra['positionComplexity'] for Stra in testData])
    avecurveComplexityStrain = average([Stra['curveComplexityStrain'] for Stra in testData])
    avepathAngleStrain = average([Stra['pathAngleStrain'] for Stra in testData])
    returnDict = {'hitAngleStrain': avehitAngleStrain, 'positionComplexity': avepositionComplexity,
                  'curveComplexityStrain': avecurveComplexityStrain, 'pathAngleStrain': avepathAngleStrain}
    if leftOrRight:
        hand = 'Right Handed'
    else:
        hand = 'Left Handed'
    if isuser:
        print(f"Average {hand} angleStrain {round(avehitAngleStrain, 2)}")
        print(f"Average {hand} positionComplexity {round(avepositionComplexity, 2)}")
        print(f"Average {hand} curveComplexityStrain {round(avecurveComplexityStrain, 2)}")
        print(f"Average {hand} pathAngleStrain {round(avepathAngleStrain, 2)}")
    return swingData, returnDict


def calcSwingDiff(swingData, hand, isuser=True):
    if len(swingData) == 0:
        return
    data = []
    swingData[0]['swingDiff'] = 0
    for i in range(1, len(swingData)):
        bps = findBPM(swingData[i]['time']) / 60
        distanceDiff = swingData[i]['preDistance'] / (swingData[i]['preDistance'] + 3) + 1
        data.append({'swingSpeed': swingData[i]['frequency'] * distanceDiff * bps})
        if swingData[i]['reset']:
            data[-1]['swingSpeed'] *= 2
        xHitDist = swingData[i]['entryPos'][0] - swingData[i]['exitPos'][0]
        yHitDist = swingData[i]['entryPos'][1] - swingData[i]['exitPos'][1]
        data[-1]['hitDistance'] = math.sqrt((xHitDist ** 2) + (yHitDist ** 2))
        data[-1]['hitDiff'] = data[-1]['hitDistance'] / (data[-1]['hitDistance'] + 2) + 1
        data[-1]['stress'] = (swingData[i]['angleStrain'] + swingData[i]['pathStrain']) * data[-1]['hitDiff']
        swingData[i]['swingDiff'] = data[-1]['swingSpeed'] * (-1.4 ** (-data[-1]['swingSpeed']) + 1) * \
                                    (data[-1]['stress'] / (data[-1]['stress'] + 2) + 1)
    if isuser:
        peakSS = [temp['swingSpeed'] for temp in data]
        peakSS.sort(reverse=True)
        print(f"peak {hand} hand speed {round(average(peakSS[:int(len(peakSS) / 16)]), 2)}")
        print(f"average {hand} hand stress {round(average([temp['stress'] for temp in data]), 2)}")


def diffToPass(swingData, WINDOW):
    if len(swingData) == 0:
        return 0
    qDIFF = deque()
    difficultyIndex = []
    for i in range(0, len(swingData)):
        if i > WINDOW:
            qDIFF.popleft()
        qDIFF.append(swingData[i]['swingDiff'])
        tempList = sorted(qDIFF, reverse=True)
        if i >= WINDOW:
            windowDiff = average(tempList) * 0.85
            difficultyIndex.append(windowDiff)
    if len(difficultyIndex) > 0:
        difficultyIndex = sorted(difficultyIndex, reverse=True)
        averageDiff = average(difficultyIndex[:int(len(difficultyIndex) * 0.25)])
        burstDiff = average(difficultyIndex[:int(len(difficultyIndex) * 0.125)])
        return max(difficultyIndex) * (averageDiff / burstDiff)
    else:
        return 0


def isInLinearPath(prev, curr, next):
    dxc = next['entryPos'][0] - prev['entryPos'][0]
    dyc = next['entryPos'][1] - prev['entryPos'][1]
    dxl = curr['entryPos'][0] - prev['entryPos'][0]
    dyl = curr['entryPos'][1] - prev['entryPos'][1]
    cross = dxc * dyl - dyc * dxl
    if cross == 0:
        return True
    else:
        return False


def detectLinear(data: list):
    if len(data) < 2:
        return data
    data[0]['linear'] = True
    data[1]['linear'] = True
    for i in range(2, len(data)):
        if isInLinearPath(data[i - 2], data[i - 1], data[i]) is True:
            data[i]['linear'] = True
        else:
            data[i]['linear'] = False
    return data


def combineAndSortList(array1, array2, key):
    combinedArray = array1 + array2
    combinedArray = sorted(combinedArray, key=lambda x: x[f'{key}'])  # once combined, sort by time
    return combinedArray


line_mirror_index = [3, 2, 1, 0]
cut_mirror_index = [0, 1, 3, 2, 5, 4, 7, 6, 8]
color_mirror_index = [1, 0, 2]


def mirrorMap(mapData: list):
    newData = copy.deepcopy(mapData)
    for i in range(0, len(newData)):
        newData[i]['x'] = line_mirror_index[newData[i]['x']]
        newData[i]['d'] = cut_mirror_index[newData[i]['d']]
        newData[i]['c'] = color_mirror_index[newData[i]['c']]
        newData[i]['a'] = -newData[i]['a']
    return newData


def mirrorBomb(bombData: list):
    newData = copy.deepcopy(bombData)
    for i in range(0, len(newData)):
        newData[i]['x'] = line_mirror_index[newData[i]['x']]
    return newData


def techOperations(mapData, bpm, isuser=True, verbose=True):
    mapData = handleBPM(mapData, bpm)
    LeftMapData = splitMapData(mapData, 0)
    RightMapData = splitMapData(mapData, 1)
    BombData = splitMapData(mapData, 2)
    LeftSwingData = []
    leftVerbose = {'hitAngleStrain': 0, 'positionComplexity': 0, 'curveComplexityStrain': 0, 'pathAngleStrain': 0}
    RightSwingData = []
    rightVerbose = {'hitAngleStrain': 0, 'positionComplexity': 0, 'curveComplexityStrain': 0, 'pathAngleStrain': 0}

    # Analyze the map
    if LeftMapData is not None:
        LeftMapData = flowDetector(LeftMapData, BombData, False)
        LeftSwingData = processSwing(LeftMapData)
        LeftPatternData = patternSplitter(LeftSwingData)
        LeftSwingData = parityPredictor(LeftPatternData, False)
        LeftSwingData, leftVerbose = swingCurveCalc(LeftSwingData, False, isuser)
        LeftSwingData = detectLinear(LeftSwingData)
    if RightMapData is not None:
        RightMapData = flowDetector(RightMapData, BombData, True)
        RightSwingData = processSwing(RightMapData)
        RightPatternData = patternSplitter(RightSwingData)
        RightSwingData = parityPredictor(RightPatternData, True)
        RightSwingData, rightVerbose = swingCurveCalc(RightSwingData, True, isuser)
        RightSwingData = detectLinear(RightSwingData)

    SwingData = combineAndSortList(LeftSwingData, RightSwingData, 'time')
    StrainList = [strain['angleStrain'] + strain['pathStrain'] for strain in SwingData]
    StrainList.sort()
    tech = average(StrainList[int(len(StrainList) * 0.25):])
    LinearList = [linear['linear'] for linear in SwingData if linear['linear'] is True]
    linear = 1
    if len(SwingData) != 0:
        linear = len(LinearList) / len(SwingData)
        linear = linear ** (2 * linear + 1) / (linear - 3 ** (2 * linear)) + 1.05
    windowA = 50
    windowB = 8
    calcSwingDiff(LeftSwingData, 'left', isuser)
    passDiffLeftA = diffToPass(LeftSwingData, windowA)
    passDiffLeftB = diffToPass(LeftSwingData, windowB)
    calcSwingDiff(RightSwingData, 'right', isuser)
    passDiffRightA = diffToPass(RightSwingData, windowA)
    passDiffRightB = diffToPass(RightSwingData, windowB)
    weightA = 50
    weightB = 8
    passDiffLeft = (weightA * passDiffLeftA + weightB * passDiffLeftB) / (weightA + weightB)
    passDiffRight = (weightA * passDiffRightA + weightB * passDiffRightB) / (weightA + weightB)
    passNum = max(passDiffLeft, passDiffRight)
    balanced_pass = max(passDiffLeft, passDiffRight) * linear
    balanced_tech = tech * (-1.4 ** (-passNum) + 1) * 10
    low_note_nerf = 1 / (
            1 + math.e ** (-0.6 * (len(SwingData) / 100 + 1.5)))  # https://www.desmos.com/calculator/povnzsoytj

    if verbose:
        returnDict = {'left': leftVerbose, 'right': rightVerbose, 'tech': tech, 'passing_difficulty': passNum,
                      'balanced_tech': balanced_tech, 'balanced_pass_diff': balanced_pass,
                      'low_note_nerf': low_note_nerf}
    else:
        returnDict = {'balanced_tech': balanced_tech, 'balanced_pass_diff': balanced_pass,
                      'low_note_nerf': low_note_nerf}
    if isuser:
        print(f"Calculacted Tech = {round(tech, 2)}")  # Put Breakpoint here if you want to see
        print(f"Calculated linear = {round(linear, 2)}")
        print(f"Calculated nerf = {round(low_note_nerf, 2)}")
        print(f"Calculated pass diff = {round(passNum, 2)}")
        print(f"Calculated balanced tech = {round(balanced_tech, 2)}")
        print(f"Calculated balanced pass diff = {round(balanced_pass, 2)}")

    return returnDict


def mapCalculation(mapData, bpm, isuser=True, verbose=True):
    t0 = time.time()
    newMapData = mapPrep(mapData)
    t1 = time.time()
    data = techOperations(newMapData, bpm, isuser, verbose)
    if isuser:
        print(f'Execution Time = {t1 - t0}')
    return data


if __name__ == "__main__":
    print("input map key")
    mapKey = input()
    mapKey = mapKey.replace("!bsr ", "")
    infoData = setup.loadInfoData(mapKey)
    bpm = infoData['_beatsPerMinute']
    availableDiffs = setup.findStandardDiffs(setup.findSongPath(mapKey))
    if len(availableDiffs) > 1:
        print(f'Choose Diff num: {availableDiffs}')
        diffNum = int(input())
    else:
        diffNum = availableDiffs[0]
        print(f'autoloading {diffNum}')
    mapData = setup.loadMapData(mapKey, diffNum)
    mapCalculation(mapData, bpm, True, True)
    print("Done")
    input()
