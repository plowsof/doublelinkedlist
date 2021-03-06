import glob
import os 
import pprint 
import pickle

def add_old_to_new():
  everyone = {}
  for x in glob.glob("*"):
    data={}
    name = os.path.basename(x)[:-4]
    if "add_old" not in name:
      print(name)
      with open(x,'r', encoding='utf-8',errors='ignore') as f:
        lines = f.readlines()
        for line in lines:
          if not "//" in line:
            val = line.split("\"")[3]
            if "_pb" in line:
              data_time = val
              continue
            if "lastseen" in line:
              seen_last = val
              continue
            if "firstseen" in line:
              seen_first = val
              continue
            if "41" in line:
              s4 = val
              continue
            if "34" in line:
              s3 = val
              continue
            if "23" in line:
              s2 = val
              continue
            if "12" in line:
              s1 = val
              continue
      data = {
      "time":data_time,
      "s1":s1,
      "s2":s2,
      "s3":s3,
      "s4":s4,
      "seen_first":seen_first,
      "seen_last":seen_last,
      "name":str(name),
      "slot":0,
      "spb":1
      }
      everyone[len(everyone)] = data
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(everyone)
  with open("old_data_list", 'wb+') as f:
    pickle.dump(everyone,f)
add_old_to_new()
'''
set "~r_orig_name" "Sever"
set "~r_frames" "2212"
set "~r_lastseen" "2021-03-0115:43:31"
set "~r_firstseen" "2021-03-0115:43:18"
set "~r_below" "race/73686976616d.cfg"
set "~r_above" "race/2d3130.cfg"
set "~r_rank" "37840"
set "race_section_++" "445"
set "race_section_pb" "445"
set "race_section_41" "119"
set "race_section_34" "105"
set "race_section_23" "92"
set "race_section_12" "129"
'''
