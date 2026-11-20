import json
from pathlib import Path
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, sys.argv[1])
import numpy as np
from lingshu.nn.hex_hier import HexHierNet, OBJ
from lingshu.nn.hex_text import spatial_detect

net=HexHierNet(n_kernels=1,stacked=False)
vec=np.zeros_like(net.get_vec())
vec[0]=1
head=vec[7:].reshape(net.head.shape)
head[OBJ.index("circle|red"),1]=100
net.set_vec(vec)
results=[]
for r,c in [(1,1),(1,2),(2,1),(2,2),(4,4),(5,5),(8,8),(18,16),(18,18),(0,3),(3,0),(0,0)]:
    lat=np.zeros((1,r,c,3));lat[...,0]=1
    try:
        got=spatial_detect(net,lat)
        results.append({"shape":[r,c],"count":len(got[0]),"result":got[0]})
    except Exception as exc:
        results.append({"shape":[r,c],"error":type(exc).__name__+": "+str(exc)})
print(json.dumps({"root":sys.argv[1],"cases":results},indent=2))
