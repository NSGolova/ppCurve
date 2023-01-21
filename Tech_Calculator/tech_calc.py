import os
import json
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
# b = time, x and y = grid location from bottom left, a = angle offset, c = left or right respectively, d = cur direction
cut_direction_index = [90, 270, 180, 0, 135, 45, 225, 315, 270] #UP, DOWN, LEFT, RIGHT, TOPLEFT, TOPRIGHT, BOTTOMLEFT, BOTTOMRIGHT, DOT
right_handed_angle_strain_forehand = 247.5      # Most comfortable angle to aim for right hand (BOTTOM LEFT) 270 - 45 or 247.5
left_handed_angle_strain_forehand = 292.5       # 270 + 45 or 292.5
# 
# 

def average(lst):   # Returns the averate of a list of integers
    if len(lst) > 0:
        return sum(lst) / len(lst)
    else:
        return 0
def bernstein_poly(i, n, t):    # For later
    """
     The Bernstein polynomial of n, i as a function of t
    """
    return comb(n, i) * ( t**(n-i) ) * (1 - t)**i
def bezier_curve(points, nTimes=1000):   # For later
    """
       Given a set of control points, return the
       bezier curve defined by the control points.

       points should be a list of lists, or list of tuples
       such as [ [1,1], 
                 [2,3], 
                 [4,5], ..[Xn, Yn] ]
        nTimes is the number of time steps, defaults to 1000

        See http://processingjs.nihongoresources.com/bezierinfo/
    """

    nPoints = len(points)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])

    t = np.linspace(0.0, 1.0, nTimes)

    polynomial_array = np.array([ bernstein_poly(i, nPoints-1, t) for i in range(0, nPoints)   ])

    xvals = np.dot(xPoints, polynomial_array)
    yvals = np.dot(yPoints, polynomial_array)

    return list(xvals), list(yvals)
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
    if mapVersion < parse('3.0.0'):     # Try to figure out if the map is the V2 or V3 format
        newMapData = setup.V2_to_V3(mapData)     # Convert to V3
    else:
        newMapData = mapData
    return newMapData
def splitMapData(mapData: dict, leftOrRight: int):    # False or 0 = Left, True or 1 = Right, 2 = Bombs
    if leftOrRight == 0:
        bloqList = [block for block in mapData['colorNotes'] if block['c'] == 0]  #Right handed blocks
    elif leftOrRight == 1:
        bloqList = [block for block in mapData['colorNotes'] if block['c'] == 1]  #Left handed blocks
    else:
        bloqList = [bomb for bomb in mapData['bombNotes']]
    return bloqList
def calculateBaseEntryExit(cBlockP, cBlockA):
    entry = [cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667, cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
    exit = [cBlockP[0] * 0.333333 + math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667, cBlockP[1] * 0.333333 + math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
    return entry, exit
def swingProcesser(mapSplitData: list):    # Returns a list of dictionaries for all swings returning swing angles and timestamps
    swingData = []
    for i in range(0, len(mapSplitData)):
        isSlider = False
        cBlockB = mapSplitData[i]['b']      # Current Block Position in Time in unit [Beats]        
        cBlockA = cut_direction_index[mapSplitData[i]['d']] + mapSplitData[i]['a']      # Current Block Angle in degrees
        cBlockP = [mapSplitData[i]['x'], mapSplitData[i]['y']]
        if i > 0:
            pBlockB = mapSplitData[i-1]['b']    # Pre-cache data for neater code
            pBlockA = swingData[-1]['angle'] # Previous Block Angle in degrees
            pBlockP = [mapSplitData[i-1]['x'], mapSplitData[i-1]['y']]
            if mapSplitData[i]['d'] == 8:   #Dot note? Just assume opposite angle. If it's a slider, the program will handle it
                pBlockA = swingData[-1]['angle']
                if cBlockB - pBlockB <= 0.03125:
                    cBlockA = pBlockA
                else:
                    if pBlockA >= 180:
                        cBlockA = pBlockA - 180
                    else:
                        cBlockA = pBlockA + 180
            # All Pre-caching Done
            if cBlockB - pBlockB >= 0.03125: # = 1/32 Just a check if notes are unreasonable close, just assume they're apart of the same swing
                if cBlockB - pBlockB > 0.120: # = 1/8 The upper bound of normal slider precision commonly used
                    if cBlockB - pBlockB > 0.5:    # = 1/2 About the limit of whats reasonable to expect from a slider
                        swingData.append({'time': cBlockB, 'angle': cBlockA})
                        swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
                    else: # 1/2 Check (just to weed out obvious non-sliders) More complicated methods need to be used
                        if abs(cBlockA - pBlockA) < 112.5:  # 90 + 22.5 JUST IN CASE. not the full 90 + 45 since that would be one hell of a slider or dot note
                            testAnglefromPosition = math.degrees(math.atan2(pBlockP[1]-cBlockP[1], pBlockP[0]-cBlockP[0])) % 360 # Replaces angle swing from block angle to slider angle
                            averageAngleOfBlocks = (cBlockA + pBlockA) / 2
                            if abs(testAnglefromPosition - averageAngleOfBlocks) <= 56.25:  # = 112.5 / 2 = 56.25
                                sliderTime = cBlockB - pBlockB
                                isSlider = True
                            else:
                                swingData.append({'time': cBlockB, 'angle': cBlockA})       # Below calculates the entry and exit positions for each swing
                                swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
                        else:
                            swingData.append({'time': cBlockB, 'angle': cBlockA})
                            swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
                else: # 1/8 Check
                    if mapSplitData[i]['d'] == 8 or abs(cBlockA - pBlockA) < 90: # 90 degree check since 90 degrees is what most would consider the maximum angle for a slider or dot note
                        sliderTime = 0.120
                        isSlider = True
                    else:
                        swingData.append({'time': cBlockB, 'angle': cBlockA})
                        swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
            else:   # 1/32 Check
                sliderTime = 0.03125
                isSlider = True
            if isSlider:
                for f in range(1, len(mapSplitData)):   # We clearly know the last block is a slider with the current block under test. Skip to the one before the last block. Should realistically never search more than 5 blocks deep
                    blockIndex = i - f              # Index of the previous block to start comparisons with
                    if blockIndex < 0:
                        break      # We Reached the beginning of the map
                    if (mapSplitData[blockIndex]['b'] - mapSplitData[blockIndex - 1]['b'] > 1.5 * sliderTime):       # use 2x slider time to account for any "irregularities" / margin of error. We are only comparing pairs of blocks
                        pBlockB = mapSplitData[blockIndex]['b']                                             # Essentially finds then caches first block in the slider group
                        pBlockA = cut_direction_index[mapSplitData[blockIndex]['d']] + mapSplitData[blockIndex]['a']
                        pBlockP = [mapSplitData[blockIndex]['x'], mapSplitData[blockIndex]['y']]
                        break
                    if(mapSplitData[blockIndex]['d'] != 8):     
                        break
                
                cBlockA = math.degrees(math.atan2(pBlockP[1]-cBlockP[1], pBlockP[0]-cBlockP[0])) % 360 # Replaces angle swing from block angle to slider angle
                if len(swingData) > 1:
                    guideAngle = (swingData[-2]['angle'] - 180) % 360           # Use the opposite swing angle as a base starting point
                else:
                    guideAngle = 270        # First swing? use downward swing as a base starting guide
                for f in range(1, len(mapSplitData)):       # Checker that will try to find a better guiding block (arrow block) for the slider angle prediction.
                    blockIndex = i - f
                    if mapSplitData[blockIndex]['b'] < pBlockB:     # Limits check to a little after the first slider block in the group
                        break
                    if mapSplitData[blockIndex]['d'] != 8:          # Breaks out of loop when it finds an arrow block
                        guideAngle = cut_direction_index[mapSplitData[blockIndex]['d']]     # If you found an arrow, use it's angle
                        break
                if abs(cBlockA - guideAngle) > 90:       # If this is true, the predicted angle is wrong, likely by 180 degrees wrong
                    if cBlockA >= 180:
                        cBlockA -= 180               # Apply Fix
                    else:
                        cBlockA += 180                
                swingData[-1]['angle'] = cBlockA
                
                xtest = (swingData[-1]['entryPos'][0] - (cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667)) * math.cos(math.radians(cBlockA))
                ytest = (swingData[-1]['entryPos'][1] - (cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.166667)) * math.sin(math.radians(cBlockA))
                if xtest <= 0.001 and ytest >= 0.001:       # For sliders, one of the entry/exit positions is still correct, this figures out which one then replaces the other
                    swingData[-1]['entryPos'] = [cBlockP[0] * 0.333333 - math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667, cBlockP[1] * 0.333333 - math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]
                else:
                    swingData[-1]['exitPos'] = [cBlockP[0] * 0.333333 + math.cos(math.radians(cBlockA)) * 0.166667 + 0.166667, cBlockP[1] * 0.333333 + math.sin(math.radians(cBlockA)) * 0.166667 + 0.16667]   
        else:
            swingData.append({'time': cBlockB, 'angle': cBlockA})    # First Note Exception. will never be a slider or need to undergo any test
            swingData[-1]['entryPos'], swingData[-1]['exitPos'] = calculateBaseEntryExit(cBlockP, cBlockA)
    return swingData
def swingAngleStrainCalc(swingData: list, leftOrRight): # False or 0 = Left, True or 1 = Right
    strainAmount = 0
    #TODO calculate strain from angle based on left or right hand
    for i in range(0, len(swingData)):
        if swingData[i]['forehand']:     #The Formula firse calculates by first normalizing the angle difference (/180) then using
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(abs(right_handed_angle_strain_forehand - swingData[i]['angle']) - 180)) / 180)**2)          # Right Handed Forehand
            else:
                strainAmount += 2 * (((180 - abs(abs(left_handed_angle_strain_forehand - swingData[i]['angle']) - 180)) / 180)**2)           # Left Handed Forehand
        else:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(abs(right_handed_angle_strain_forehand - 180 - swingData[i]['angle']) - 180))/180)**2)           # Right Handed Backhand
            else:
                strainAmount += 2 * (((180 - abs(abs(left_handed_angle_strain_forehand - 180 - swingData[i]['angle']) - 180))/180)**2)           # Left Handed Backhand
    return strainAmount * 2
def bezierAngleStrainCalc(angleData: list, forehand, leftOrRight):
    strainAmount = 0
    for i in range(0, len(angleData)):
        if forehand:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(abs(right_handed_angle_strain_forehand - angleData[i]) - 180)) / 180)**2)          # Right Handed Forehand
            else:
                strainAmount += 2 * (((180 - abs(abs(left_handed_angle_strain_forehand - angleData[i]) - 180)) / 180)**2)           # Left Handed Forehand
        else:
            if leftOrRight:
                strainAmount += 2 * (((180 - abs(abs(right_handed_angle_strain_forehand - 180 - angleData[i]) - 180))/180)**2)           # Right Handed Backhand
            else:
                strainAmount += 2 * (((180 - abs(abs(left_handed_angle_strain_forehand - 180 - angleData[i]) - 180))/180)**2)           # Left Handed Backhand
    return strainAmount
def patternSplitter(swingData: list):    # Does swing speed analysis to split the long list of dictionaries into smaller lists of patterns containing lists of dictionaries
    for i in range(0, len(swingData)):   # Swing Frequency Analyzer
        if i > 0 and i+1 < len(swingData):    # Checks done so we don't try to access data that doesn't exist
            SF = 2/(swingData[i+1]['time'] - swingData[i-1]['time'])    # Swing Frequency
        else:
            SF = 0
        swingData[i]['frequency'] = SF
    patternFound = False
    SFList = [freq['frequency'] for freq in swingData]
    SFmargin = average(SFList) / 32
    patternList = []            # Pattern List
    tempPlist = []              # Temp Pattern List
    for i in range(0, len(swingData)):
        if i > 0:
            if (1 / (swingData[i]['time'] - swingData[i-1]['time'])) - swingData[i]['frequency'] <= SFmargin:    # Tries to find Patterns within margin
                if not patternFound:    # Found a pattern and it's the first one?
                    patternFound = True
                    del tempPlist[-1]
                    if len(tempPlist) > 0:  # We only want to store lists with stuff
                        patternList.append(tempPlist)
                    tempPlist = [swingData[i-1]]    #Store the 1st block of the pattern
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
def parityPredictor(patternData: list, bombData: list, leftOrRight):    # Parses through a List of Lists of Dictionaries to calculate the most likely parity for each pattern
    newPatternData = []
    for p in range(0, len(patternData)):
        testData1 = patternData[p]
        testData2 = copy.deepcopy(patternData[p])
        for i in range(0, len(testData1)):  # Build Forehand TestData Build
            if i > 0:
                if abs(testData1[i]['angle'] - testData1[i-1]['angle']) > 45:     # If angles are too similar, assume reset since a write roll of that degree is crazy
                    testData1[i]['forehand'] = not testData1[i-1]['forehand']
                else:
                    testData1[i]['forehand'] = testData1[i-1]['forehand']
            else:
                testData1[0]['forehand'] = True
        for i in range(0, len(testData2)):  # Build Banckhand TestData
            if i > 0:
                if abs(testData2[i]['angle'] - testData2[i-1]['angle']) > 45:     # Again, if angles are too similar, assume reset since a write roll of that degree is crazy
                    testData2[i]['forehand'] = not testData2[i-1]['forehand']
                else:
                    testData2[i]['forehand'] = testData2[i-1]['forehand']
            else:
                testData2[0]['forehand'] = False
        forehandTest = swingAngleStrainCalc(testData1, leftOrRight)    # Test Data
        backhandTest = swingAngleStrainCalc(testData2, leftOrRight)    # 
        if forehandTest <= backhandTest:    #Prefer forehand starts over backhand if equal
            newPatternData += testData1      # Forehand gave a lower stress value, therefore is the best option in terms of hand placement for the pattern
        elif forehandTest > backhandTest:
            newPatternData += testData2
    for i in range(0, len(newPatternData)):
        newPatternData[i]['angleStrain'] = swingAngleStrainCalc([newPatternData[i]], leftOrRight)  # Assigns individual strain values to each swing. Done like this in square brackets because the function expects a list.
        if i > 0:
            if newPatternData[i]['forehand'] == newPatternData[i-1]['forehand']:
                newPatternData[i]['reset'] = True
            else:
                newPatternData[i]['reset'] = False
        else:
            newPatternData[i]['reset'] = False
    return newPatternData
def staminaCalc(swingData: list):
    staminaList: list = []
    #TODO calculate strain from stamina drain


    return staminaList
def swingCurveCalc(swingData: list, leftOrRight, isuser=True):
    if len(swingData) == 0:
        returnDict = {'hitAngleStrain': 0, 'positionComplexity': 0, 'curveComplexityStrain': 0, 'pathAngleStrain': 0}
        return swingData, returnDict
    swingData[0]['pathStrain'] = 0  # First Note cannot really have any path strain
    testData = []
    for i in range(1, len(swingData)):
        point0 = swingData[i-1]['exitPos']      # Curve Beginning
        point1x = point0[0] + 1 * math.cos(math.radians(swingData[i-1]['angle']))
        point1y = point0[1] + 1 * math.sin(math.radians(swingData[i-1]['angle']))
        point1 = [point1x, point1y] #Curve Control Point
        point3 = swingData[i]['entryPos']       # Curve Ending
        point2x = point3[0] - 1 * math.cos(math.radians(swingData[i]['angle']))
        point2y = point3[1] - 1 * math.sin(math.radians(swingData[i]['angle']))
        point2 = [point2x, point2y]     #Curve Control Point
        points = [point0, point1, point2, point3]
        xvals, yvals = bezier_curve(points, nTimes=25)      #nTimes = the resultion of the bezier curve. Higher = more accurate but slower
        xvals.reverse()
        yvals.reverse()
        positionComplexity = 0
        angleChangeList = []
        angleList = []
        for f in range(1, min(len(xvals), len(yvals))):
            angleList.append(math.degrees(math.atan2(yvals[f] - yvals[f-1], xvals[f] - xvals[f-1])) % 360)
            if f > 1:
                angleChangeList.append(180 - abs(abs(angleList[-1] - angleList[-2]) - 180))   # Wacky formula to handle 5 - 355 situations
        
        if i > 1:       # Will miss the very first reset if it exists but a sacrafice for speed
            simHandCurPos = swingData[i]['entryPos']
            if(swingData[i]['forehand'] == swingData[i-2]['forehand']):     #Start 2 swings back since it's the most likely
                simHandPrePos = swingData[i-2]['entryPos']
            elif(swingData[i]['forehand'] == swingData[i-1]['forehand']):
                simHandPrePos = swingData[i-1]['entryPos']
            else:
                simHandPrePos = simHandCurPos
            positionDiff = math.sqrt((simHandCurPos[1] - simHandPrePos[1])**2 + (simHandCurPos[0] - simHandPrePos[0])**2)
            positionComplexity = positionDiff**2

        lengthOfList = len(angleChangeList) * (1 - 0.4)             # 0.2 + (1 - 0.8) = 0.4
        firstIndex = int(len(angleChangeList)*0.2)
        lastIndex = int(len(angleChangeList)*0.8)
        if swingData[i]['reset']:       # If the pattern is a reset, look less far back
            pathLookback = 0.75                     # 0.5 angle strain = 0.35 or 65% lookback, 0.1 angle strain = 0.5 or 50% lookback
        else:
            pathLookback = 0.50

        curveComplexity = abs((lengthOfList * average(angleChangeList[firstIndex:lastIndex]) - 180) / 180)   # The more the angle difference changes from 180, the more complex the path, /180 to normalize between 0 - 1
        pathAngleStrain = bezierAngleStrainCalc(angleList[int(len(angleList) * pathLookback):], swingData[i]['forehand'], leftOrRight) / len(angleList) * 2

        # print(f"positionComplexity {positionComplexity}")
        # print(f"curveComplexity {curveComplexity}")
        # print(f"pathAngleStrain {pathAngleStrain}")
        # from matplotlib import pyplot as plt        #   Test
        # fig, ax = plt.subplots(figsize = (8, 5))
        # ax.plot(xvals, yvals, label='curve path')
        # xpoints = [p[0] for p in points]
        # ypoints = [p[1] for p in points]
        # ax.plot(xvals, yvals, label='curve path')
        # ax.plot(xpoints, ypoints, "ro")
        # ax.plot(xvals[int(len(xvals) * (1 - pathLookback))], yvals[int(len(yvals) * (1 - pathLookback))], "ro")
        # ax.plot([xvals[int(len(xvals) * 0.2)], xvals[int(len(xvals) * 0.8)]], [yvals[int(len(yvals) * 0.2)], yvals[int(len(yvals) * 0.8)]], "ro")
        # ax.set_xticks(np.linspace(0,1.333333333,5))
        # ax.set_yticks(np.linspace(0,1,4))
        # #plt.xlim(0,1.3333333)
        # #plt.ylim(0,1)
        # plt.legend()
        # plt.show()

        testData.append({'curveComplexityStrain': curveComplexity, 'pathAngleStrain': pathAngleStrain, 'positionComplexity': positionComplexity})
        swingData[i]['positionComplexity'] = positionComplexity
        swingData[i]['curveComplexity'] = curveComplexity
        swingData[i]['pathAngleStrain'] = pathAngleStrain
        swingData[i]['pathStrain'] = curveComplexity + pathAngleStrain + positionComplexity
    avehitAngleStrain = average([Stra['angleStrain'] for Stra in swingData])
    avepositionComplexity = average([Stra['positionComplexity'] for Stra in testData])
    avecurveComplexityStrain = average([Stra['curveComplexityStrain'] for Stra in testData])
    avepathAngleStrain = average([Stra['pathAngleStrain'] for Stra in testData])
    returnDict = {'hitAngleStrain': avehitAngleStrain, 'positionComplexity': avepositionComplexity, 'curveComplexityStrain': avecurveComplexityStrain, 'pathAngleStrain': avepathAngleStrain}
    if leftOrRight:
        hand = 'Right Handed'
    else:
        hand = 'Left Handed'
    if isuser:
        print(f"Average {hand} hitAngleStrain {avehitAngleStrain}")
        print(f"Average {hand} positionComplexity {avepositionComplexity}")
        print(f"Average {hand} curveComplexityStrain {avecurveComplexityStrain}")
        print(f"Average {hand} pathAngleStrain {avepathAngleStrain}")
    return swingData, returnDict
def diffToPass(swingData, bpm, hand, isuser=True):
    bps = bpm / 60
    SSSpeed = 0         #Sum of Swing Speed
    qSS = deque()       #List of swing speed
    SSStress = 0             #Sum of swing stress
    qST = deque()       #List of swing stress
    smoothing = 8       #Adjusts the smoothing window (how many swings get smoothed) (roughly 8 notes to fail)
    difficultyIndex = []
    data = []
    for i in range(1, len(swingData)):      # Scan all swings, starting from 2nd swing
        xPathDist = swingData[i]['exitPos'][0] - swingData[i-1]['exitPos'][0]
        yPathDist = swingData[i]['exitPos'][1] - swingData[i-1]['exitPos'][1]
        data.append({'preDistance': math.sqrt((xPathDist**2) + (yPathDist**2))})
        if i > smoothing:       # Start removing old swings based on smoothing amount
            SSSpeed -= qSS.popleft()
            SSStress -= qST.popleft()
        distanceDiff = data[-1]['preDistance'] / (data[-1]['preDistance'] + 2) + 1
        qSS.append(swingData[i]['frequency'] * distanceDiff * bps)
        SSSpeed += qSS[-1]
        data[-1]['swingSpeedAve'] = SSSpeed / smoothing


        xHitDist = swingData[i]['entryPos'][0] - swingData[i]['exitPos'][0]
        yHitDist = swingData[i]['entryPos'][1] - swingData[i]['exitPos'][1]
        data[-1]['hitDistance'] = math.sqrt((xHitDist**2) + (yHitDist**2))
        data[-1]['hitDiff'] =  data[-1]['hitDistance'] / (data[-1]['hitDistance'] + 3) + 1

        qST.append((swingData[i]['angleStrain'] + swingData[i]['pathStrain']) * data[-1]['hitDiff'])
        SSStress += qST[-1]
        data[-1]['stressAve'] = SSStress / smoothing
        
        difficulty = data[-1]['swingSpeedAve'] * (-1.4**(-data[-1]['swingSpeedAve']) + 1) * (data[-1]['stressAve'] / (data[-1]['stressAve'] + 2) + 1) * 0.75
        #difficulty = data[-1]['swingSpeedAve'] + data[-1]['stressAve']
        data[-1]['difficulty'] = difficulty
        difficultyIndex.append(difficulty)
    if isuser:
        peakSS = [temp['swingSpeedAve'] for temp in data]
        peakSS.sort(reverse=True)
        print(f"peak {hand} hand speed {average(peakSS[:int(len(peakSS) / 16)])}")
        print(f"average {hand} hand stress {average([temp['stressAve'] for temp in data])}")

    difficultyIndex.sort(reverse=True)      #Sort list by most difficult
    return average(difficultyIndex[:int(len(difficultyIndex) / 16)])          # Use the top 8 swings averaged as the return
def combineAndSortList(array1, array2, key):
    combinedArray = array1 + array2
    combinedArray = sorted(combinedArray, key=lambda x: x[f'{key}'])  # once combined, sort by time
    return combinedArray

def techOperations(mapData, bpm, isuser=True, verbose=True):

    LeftMapData = splitMapData(mapData, 0)
    RightMapData = splitMapData(mapData, 1)
    bombData = splitMapData(mapData, 2)
    
    LeftSwingData = swingProcesser(LeftMapData)
    RightSwingData = swingProcesser(RightMapData)
    
    LeftPatternData = patternSplitter(LeftSwingData)
    RightPatternData = patternSplitter(RightSwingData)
    
    LeftSwingData = parityPredictor(LeftPatternData, bombData, False)
    RightSwingData = parityPredictor(RightPatternData, bombData, True)
    
    LeftSwingData, leftVerbose = swingCurveCalc(LeftSwingData, False, isuser)
    RightSwingData, rightVerbose = swingCurveCalc(RightSwingData, True, isuser)
    
    SwingData = combineAndSortList(LeftSwingData, RightSwingData, 'time')
    StrainList = [strain['angleStrain'] + strain['pathStrain'] for strain in SwingData]
    StrainList.sort()
    tech = average(StrainList[int(len(StrainList) * 0.25):])
    passNum = max(diffToPass(LeftSwingData, bpm, 'left', isuser), diffToPass(RightSwingData, bpm, 'right', isuser))

    balanced_tech = tech * (-1.4**(-passNum) + 1)

    if verbose:
        returnDict = {'left': leftVerbose, 'right': rightVerbose, 'tech': tech, 'passing_difficulty': passNum, 'balanced_tech': balanced_tech}
    else:
        returnDict = {'balanced_tech': balanced_tech, 'passing_difficulty': passNum}
    if isuser:
        print(f"Calculacted Tech = {tech}")        # Put Breakpoint here if you want to see
        print(f"Calculated pass diff = {passNum}")
        print(f"Calculated balanced tech = {balanced_tech}")
    return returnDict

def mapCalculation(mapData, bpm, isuser=True, verbose=True):
    t0 = time.time()
    newMapData = mapPrep(mapData)
    data = techOperations(newMapData, bpm, isuser, verbose)
    t1 = time.time()
    if isuser:
        print(f'Execution Time = {t1-t0}')
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