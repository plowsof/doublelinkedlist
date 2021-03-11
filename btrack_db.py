#f = io.open("/dev/ttyUSB0")
 #   while True:
  #      print f.readline().strip()

import os
import threading 
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import json 
import time 
import os 
import pprint
import datetime
import pickle 
from getstatus import udp_send

DoubleLinkedThing = {}
#pickled lists for each map
mapname = ""

sof_log_dir = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server"
sof_log_seek = os.path.join(sof_log_dir,"sof_seek.log")

sof_log_file = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server\\sof.log"
sofplus_data_dir = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server\\sofplus\\data\\btrack"
log_seek = 0

add_old_data = False

def start_observer():
  print("observera")
  global sof_log_dir

  path = sof_log_dir
  patterns = "*"
  ignore_patterns = ""
  ignore_directories = True
  case_sensitive = True
  my_event_handler_2 = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
  my_event_handler_2.on_modified = on_modified
  my_observer_2 = Observer()
  my_observer_2.schedule(my_event_handler_2, sof_log_dir, recursive=False)
  my_observer_2.start()
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    my_observer_2.stop()
    my_observer_2.join()

def on_modified(event):
  global sof_log_seek
  global log_seek
  global sof_log_file
  if "sof.log" in event.src_path:
    print("modified")
    time.sleep(0.1)
    #encoding="utf-8"
    with open(event.src_path, "r", encoding="latin-1") as f:
      f.seek(int(log_seek))
      #probably 1 line , but just in case
      lines = f.readlines()
      for line in lines:
        #json string from sofplus
        if "[\"\\\\bt_db\\" in line[0:12]:
          print(line)
          data = json.loads(line[:-1])
          dict_data={}
          if data[1] == "bt_finish":
            dict_data = {
                    "name":data[2],
                    "time":data[3],
                    "slot":data[4],
                    "loads":data[5],
                    "saves":data[6]
                  }
            lap_completed(dict_data)
          if data[1] == "map_change":
            themap = data[2]
            set_map(themap)
            #map changed
          if data[1] == "join":
            print("if we exist - update last seen")
            dict_data = {
                    "name":data[2],
                    "slot":data[3]
            }
            player_joined(dict_data)
    log_seek = os.path.getsize(event.src_path)
    with open(sof_log_seek, "w+") as f:
      f.write(str(log_seek))

def player_joined(data):
  global DoubleLinkedThing
  name = data["name"]
  slot = data["slot"]
  date_now = datetime.datetime.now().replace(microsecond=0).isoformat()
  if name not in DoubleLinkedThing:
    slot = data["slot"]
    pb = 99999999
    rank = "unranked"
    saves = 0
    loads = 0
    total = 0
    first_seen = date_now
    last_seen = date_now
  else:
    DoubleLinkedThing[str(name)]["seen_last"] = date_now
    info = DoubleLinkedThing[str(name)]
    slot = data["slot"]
    pb = info["time"]
    rank = info["rank"]
    loads = info["loads"]
    saves = info["saves"]
    total = info["total"]
    first_seen = info["seen_first"]
    last_seen = date_now
    #function pydb_bt_set_begin_cvars(bt_slot,bt_rank,bt_time,bt_saves,bt_loads,bt_total)
  msg = [f"sp_sc_func_exec pydb_bt_set_begin_cvars \"{slot}\" \"{pb}\" \"{rank}\" \"{saves}\" \"{loads}\" \"{total}\" \"{first_seen}\""]
  udp_send(msg)

#print(f"player {data['name']} completed the track in {data['time']} seconds. pb: {data['pb']}")
def lap_completed(data):
  global DoubleLinkedThing
  date_now = datetime.datetime.now().date().isoformat()
  pb = data["time"]
  print(f"pb_time:{pb}")
  name = data["name"]
  loads = data["loads"]
  saves = data["saves"]
  slot = data["slot"]
  print(f"{data['slot']} : completed")
  if name not in DoubleLinkedThing:
    add_new(data)
  else:
    #FIXME 
    DoubleLinkedThing[str(name)]["total"] += 1
    if int(pb) < int(DoubleLinkedThing[str(name)]["time"]):
      print("We made a PB!")
      DoubleLinkedThing[str(name)]["time"] = pb
      print(f"loads = {loads} saves = {saves}")
      DoubleLinkedThing[str(name)]["saves"] = saves
      DoubleLinkedThing[str(name)]["loads"] = loads
    DoubleLinkedThing[str(name)]["seen_last"] = date_now
    if DoubleLinkedThing[data["name"]]["rank"] != 1:
        rank_up(data)
    else:
      if int(DoubleLinkedThing[str(name)]["rank"]) <= 10:
        #not a pb but
        #still need to update top10
        create_top_10()
    #set new values for players .rank info
    #name and slot
    tmpDict = {
    "name":str(name),
    "slot":slot
    }
    player_joined(tmpDict)

#each map has a seperate list
#save old one
def set_map(themap):
  global DoubleLinkedThing
  global mapname
  save_list()
  mapname = themap
  python_db = os.path.join(os.getcwd(),"python-db","btrack","mapname",mapname)
  if os.path.isfile(python_db):
    print("Loading pickled dict fro mfile")
    with open(python_db, 'rb') as f:
      DoubleLinkedThing = pickle.load(f)
  else:
    print("creating our own list")
    create_list()
    with open(python_db, 'wb+') as f:
      pickle.dump(DoubleLinkedThing,f)
  create_top_10()

  #load pickled list <mapname>.pickle
def create_list():
  global DoubleLinkedThing
  APJ = {
    "rank": 1,
    "below":"OP",
    "above":"1st",
    "time": 99999998,
    "total":5,
    "saves":900,
    "loads":900,
    "seen_last":"hello",
    "seen_first":"world"
  }
  OP = {
    "rank": 2,
    "below":"last",
    "above":"APJ",
    "time": 99999999,
    "total":5,
    "saves":900,
    "loads":900,
    "seen_last":"hello",
    "seen_first":"world"
  }

  DoubleLinkedThing["first"] = "APJ"
  DoubleLinkedThing["last"] = "OP"
  DoubleLinkedThing["APJ"] = APJ
  DoubleLinkedThing["OP"] = OP

def add_new(data):
  global DoubleLinkedThing
  global add_old_data 
  name = data["name"]
  saves = data["saves"]
  loads = data["loads"]
  slot = data["slot"]
  pb_time = data["time"]
  last = DoubleLinkedThing["last"]
  last_rank = DoubleLinkedThing[str(last)]["rank"]
  rank = last_rank + 1
  DoubleLinkedThing["last"] = str(name)
  DoubleLinkedThing[str(last)]["below"] = str(name)
  date_now = datetime.datetime.now().date().isoformat()
  DoubleLinkedThing[str(name)] = {
  "rank":rank,
  "below":"last",
  "above":str(last),
  "time": int(pb_time),
  "total": 1,
  "saves":saves,
  "loads":loads,
  "seen_first":date_now,
  "seen_last":date_now
  }
  rank_up(data)

def rank_up(data):
  #rank 1 never gets here
  global DoubleLinkedThing
  name = data["name"]
  slot = data["slot"]
  orig_data = DoubleLinkedThing[str(name)]
  orig_rank = orig_data["rank"]
  print(f"begin rank = {orig_rank}")
  compare_to_name = DoubleLinkedThing[str(data["name"])]["above"]
  compare_to_above = DoubleLinkedThing[str(compare_to_name)]["above"]
  print(compare_to_name)
  compare_to_time = DoubleLinkedThing[str(compare_to_name)]["time"]
  initial_changes = False
  broadcast = 0
  while True:
    print("hello")
    print(f"is {orig_data['time']} <= {compare_to_time} <=" )
    if int(orig_data["time"]) <= int(compare_to_time):  
      print(f"YES it is!")      
      if not initial_changes:
        if orig_data["below"] == "last":
          print("we're last")
          DoubleLinkedThing["last"] = str(orig_data["above"])
          DoubleLinkedThing[str(orig_data["above"])]["below"] = "last"
        else:
          #belows above is now our above
          DoubleLinkedThing[orig_data["below"]]["above"] = str(orig_data["above"])
          DoubleLinkedThing[orig_data["above"]]["below"] = str(orig_data["below"])
        initial_changes = True
      DoubleLinkedThing[str(compare_to_name)]["rank"] += 1
      DoubleLinkedThing[data["name"]]["rank"] -= 1

      #prevent infinite loop
      if int(DoubleLinkedThing[data["name"]]["rank"]) < 0:
        print("rank < 0 - fatal error")
        sys.exit()

      print(f"compare_toname = {compare_to_above}")
      if str(compare_to_above) == "1st":
        DoubleLinkedThing[str(data["name"])]["above"] = "1st"
        DoubleLinkedThing[str(data["name"])]["below"] = compare_to_name
        DoubleLinkedThing[str(compare_to_name)]["above"] = data["name"]
        DoubleLinkedThing["first"] = data["name"]
        print("BREAK we'#re 1st")
        break
      else:
        compare_to_name = DoubleLinkedThing[str(compare_to_name)]["above"]
        compare_to_above = DoubleLinkedThing[str(compare_to_name)]["above"]
        compare_to_time = DoubleLinkedThing[str(compare_to_name)]["time"]
    else:
      print("BREAK not true <=?lo")
      break

  else:
    print("No were not top10")
  print(f"orig: {orig_rank} new: {DoubleLinkedThing[data['name']]['rank']}")
  if int(DoubleLinkedThing[data["name"]]["rank"]) != int(orig_rank):
    print("ranks are != ofcourse")
    #rank changed
    broadcast = 1

    print(f"compare_to_name = {compare_to_above}")
    if int(DoubleLinkedThing[data["name"]]["rank"]) != 1:
      compare_to_below = DoubleLinkedThing[str(compare_to_name)]["below"]
      DoubleLinkedThing[str(data["name"])]["below"] = str(compare_to_below)

      #aboves below has us as their below
      DoubleLinkedThing[str(compare_to_below)]["above"] = data["name"]

      DoubleLinkedThing[str(compare_to_name)]["below"] = data["name"] 
      DoubleLinkedThing[str(data["name"])]["above"] = str(compare_to_name)
  else:
    print("no rank change / we're last / we're first")
    #new info in top 10
  msg = [f"sp_sc_func_exec pydb_bt_broadcast_new_rank \"{data['name']}\" \"{DoubleLinkedThing[data['name']]['rank']}\" \"{data['slot']}\" \"{broadcast}\""]
  udp_send(msg)
  print("are we int he top10?")
  if int(DoubleLinkedThing[data["name"]]["rank"]) <= 10:
    create_top_10()

def save_list_loop():
  while True:
    time.sleep(60)
    save_list()
def save_list():
  global DoubleLinkedThing
  global mapname
  python_db = os.path.join(os.getcwd(),"python-db","btrack","mapname",mapname)
  #if somebody made a pb <pbwasmade>.file -> rem
  with open(python_db, 'wb+') as f:
    pickle.dump(DoubleLinkedThing,f)

def create_top_10():
  print("Create top10")
  global DoubleLinkedThing
  global sofplus_data_dir
  global mapname
  cfg_name = "top10-" + mapname + ".cfg"
  fname = os.path.join(sofplus_data_dir,cfg_name)
  getinfo = DoubleLinkedThing["first"]
  with open(fname,"w+") as f:
    for x in range(1,11):
      name = getinfo
      print(DoubleLinkedThing[str(getinfo)])
      rank = x 
      pb = DoubleLinkedThing[str(getinfo)]["time"]
      print(f"pb at stting:{pb}")
      saves = DoubleLinkedThing[str(getinfo)]["saves"]
      loads = DoubleLinkedThing[str(getinfo)]["loads"]
      last_seen = DoubleLinkedThing[str(getinfo)]["seen_last"]
      f.write(f"set pydb_data_{x} \"{name}\\{pb}\\{saves}\\{loads}\\{last_seen}\"\n")
      getinfo = DoubleLinkedThing[str(getinfo)]["below"]
      if str(getinfo) == "last":
        break
  msg= ["sp_sc_func_exec bt_make_top10"]
  udp_send(msg)

def main():
  global DoubleLinkedThing
  global sof_log_seek
  global log_seek
  global mapname
  size = 0
  create_list()
  msg = [f"_sp_sv_info_map_current"]
  mapname = udp_send(msg).split("/")[1].split("\"")[0]
  set_map(mapname)
  print("original list:")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)
  if os.path.isfile(sof_log_seek):
    with open(sof_log_seek, "r") as f:
      size = f.readlines()[0]
  else:
    with open(sof_log_seek,"w+") as f:
      f.write("0")
  log_seek = size
  x = threading.Thread(target=start_observer)
  x.start()
  python_db = os.path.join(os.getcwd(),"python-db","btrack","mapname")
  if not os.path.exists(python_db):
    os.makedirs(os.path.dirname(python_db))
  #y = threading.Thread(target=save_list_loop)
  #y.start()
  
  time.sleep(2)
  #break_it()
  #load_old_data()
  #testing()

if __name__ == '__main__':
  main()


