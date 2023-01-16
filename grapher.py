from tkinter.filedialog import askopenfile
import json
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import (FormatStrFormatter)
import numpy as np

jsonPath = askopenfile(mode ='r', filetypes =[('newPPJSON', '*.json')])
JSON_Path = jsonPath.name
with open(JSON_Path, encoding='ISO-8859-1') as playlist_json:
    PPJSON = json.load(playlist_json)

starsPair = []
newPpPair = []
oldPpPair = []

for i, score in enumerate(PPJSON):
    try:
        starsPair.append(PPJSON[i]['newStar'])
        newPpPair.append(PPJSON[i]['AIpp'])
        oldPpPair.append(PPJSON[i]['oldPP'])
    except:
        print("done")

fig, ax = plt.subplots(figsize = (15, 8))

ax.xaxis.set_major_formatter(FormatStrFormatter('% 1.1f'))

ax.set_title("PP graph")
ax.set_xlabel("Stars", fontsize=12)
ax.set_ylabel("PP", fontsize=12)

ax.set_xticks(np.linspace(0,20,21))
ax.set_yticks(np.linspace(0,1000,21))

ax.plot(starsPair, newPpPair, 'o', label = 'NewPP')
ax.plot(starsPair, oldPpPair, 'o', label = 'OldPP')

plt.xlim(0,20)
plt.ylim(0,1000)
plt.grid(visible=True,which='major',axis='both')

ax.legend(fontsize=10, fancybox=False, edgecolor='black', bbox_to_anchor=(1.1,1))
fig.tight_layout()
plt.show()

print("done")
print("Press Enter to Exit")
input()