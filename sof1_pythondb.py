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
mapname = "8ab"

sof_log_dir = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server"
sof_log_seek = os.path.join(sof_log_dir,"sof_seek.log")

sof_log_file = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server\\sof.log"
sofplus_data_dir = "C:\\Users\\Human\\Desktop\\Raven\\SOF PLATINUM\\user-server\\sofplus\\data\\race"
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
    with open(event.src_path, "r") as f:
      f.seek(int(log_seek))
      #probably 1 line , but just in case
      lines = f.readlines()
      for line in lines:
        #json string from sofplus
        if "[\"\\\\surf_db\\" == line[0:12]:
          print(line)
          data = json.loads(line[:-1])
          dict_data={}
          if data[1] == "total_laps":
            dict_data = {
                    "name":data[2],
                    "time":data[3],
                    "spb":data[4],
                    "s1":data[5],
                    "s2":data[6],
                    "s3":data[7],
                    "s4":data[8],
                    "slot":data[9]
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
    
    #pydb_set_begin_cvars(~slot,~pb,~rank,~s1,~s2,~s3,~s4,~++,~first,~last)
    slot = data["slot"]
    pb = 42069
    rank = "unranked"
    s1 = 42069
    s2 = 42069
    s3 = 42069
    s4 = 42069
    total = 0
    first_seen = date_now
    last_seen = date_now
  else:
    DoubleLinkedThing[str(name)]["seen_last"] = date_now
    info = DoubleLinkedThing[str(name)]
    slot = data["slot"]
    pb = info["time"]
    rank = info["rank"]
    s1 = info["s1"]
    s2 = info["s2"]
    s3 = info["s3"]
    s4 = info["s4"]
    total = info["total"]
    first_seen = info["seen_first"]
    last_seen = date_now
  msg = [f"""sp_sc_func_exec pydb_set_begin_cvars \"{slot}\" \"{pb}\" \"{rank}\" \"{s1}\" \"{s2}\" \"{s3}\" \"{s4}\" \"{total}\" \"{first_seen}\" \"{last_seen}\""""]
  udp_send(msg)

#print(f"player {data['name']} completed the track in {data['time']} seconds. pb: {data['pb']}")
def lap_completed(data):
  global DoubleLinkedThing
  date_now = datetime.datetime.now().date().isoformat()
  pb_time = data["time"]
  print(f"pb_time:{pb_time}")
  name = data["name"]
  s1 = data["s1"]
  s2 = data["s2"]
  s3 = data["s3"]
  s4 = data["s4"]
  slot = data["slot"]
  spb = data["spb"]
  print(f"{data['slot']} : completed")
  if name not in DoubleLinkedThing:
    add_new(data)
  else:
    #FIXME 
    DoubleLinkedThing[str(name)]["total"] += 1
    if spb == 1:
      if DoubleLinkedThing[str(name)]["s1"] < s1:
        DoubleLinkedThing[str(name)]["s1"] = s1
      if DoubleLinkedThing[str(name)]["s2"] < s2:
        DoubleLinkedThing[str(name)]["s2"] = s2
      if DoubleLinkedThing[str(name)]["s3"] < s3:
        DoubleLinkedThing[str(name)]["s3"] = s3
      if DoubleLinkedThing[str(name)]["s4"] < s4:
        DoubleLinkedThing[str(name)]["s4"] = s1
    DoubleLinkedThing[str(name)]["seen_last"] = date_now
    DoubleLinkedThing[str(name)]["total"] += 1
    if int(DoubleLinkedThing[str(name)]["time"]) > int(pb_time):
      DoubleLinkedThing[str(name)]["time"] = pb_time
      if DoubleLinkedThing[data["name"]]["rank"] != 1:
        rank_up(data)
    else:
      if int(DoubleLinkedThing[str(name)]["rank"]) <= 10:
        #not a pb but
        #still need to update top10
        create_top_10()

#each map has a seperate list
#save old one
def set_map(themap):
  global DoubleLinkedThing
  global mapname
  save_list()
  mapname = themap
  python_db = os.path.join(os.getcwd(),"python-db","mapname",mapname)
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
  print("creat list&&&&&&&&&&&&&&&")
  global DoubleLinkedThing
  APJ = {
    "rank": 1,
    "below":"OP",
    "above":"1st",
    "time": 800,
    "total":5,
    "s1":900,
    "s2":900,
    "s3":900,
    "s4":900,
    "seen_last":"hello",
    "seen_first":"world"
  }
  OP = {
    "rank": 2,
    "below":"last",
    "above":"APJ",
    "time":900,
    "total":1,
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
  s1 = data["s1"]
  s2 = data["s2"]
  s3 = data["s3"]
  s4 = data["s4"]
  slot = data["slot"]
  pb_time = data["time"]
  last = DoubleLinkedThing["last"]
  last_rank = DoubleLinkedThing[str(last)]["rank"]
  rank = last_rank + 1
  DoubleLinkedThing["last"] = str(name)
  DoubleLinkedThing[str(last)]["below"] = str(name)
  date_now = datetime.datetime.now().date().isoformat()
  if not add_old_data:
    DoubleLinkedThing[str(name)] = {
    "rank":rank,
    "below":"last",
    "above":str(last),
    "time": int(pb_time),
    "total": 1,
    "s1":s1,
    "s2":s2,
    "s3":s3,
    "s4":s4,
    "seen_first":date_now,
    "seen_last":date_now
    }
  else:
    seen_first = data["seen_first"]
    seen_last = data["seen_last"]
    DoubleLinkedThing[str(name)] = {
    "rank":rank,
    "below":"last",
    "above":str(last),
    "time": int(pb_time),
    "total": 1,
    "s1":s1,
    "s2":s2,
    "s3":s3,
    "s4":s4,
    "seen_first":seen_first,
    "seen_last":seen_last
    }
  rank_up(data)

def section_pb(data):
  print(f"player {data['name']} got a pb on section {data['section']} time: {data['time']}")
  #debug_data(data)

def debug_data(data):
  for x in data:
    print(data[x])

def change_map(mapname):
  global sof_log_file
  with open(sof_log_file, "a") as f:
    f.write("[" f"\"\\\\surf_db\\\\\",\"map_change\",\"{mapname}\"")

def do_lap(name,time,pb,s1,s2,s3,s4):
  global sof_log_file
  with open(sof_log_file, "a") as f:
    f.write("[" f"\"\\\\surf_db\\\\\",\"total_laps\",\"{name}\",{time},{pb},{s1},{s2},{s3},{s4}" + "]\n")

def testing():
  global DoubleLinkedThing
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)
  do_lap("hello",600,1,100,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",1,1,100,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",2,0,100,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",0,1,100,2,2,2)
  time.sleep(0.1)
  set_map("[r&b]multimoto")
  time.sleep(3)
  pp.pprint(DoubleLinkedThing)

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
  if DoubleLinkedThing[data["name"]]["rank"] != orig_rank:
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
  msg = [f"sp_sc_func_exec broadcast_new_rank \"{data['name']}\" \"{DoubleLinkedThing[data['name']]['rank']}\" \"{data['slot']}\" \"{broadcast}\""]
  udp_send(msg)
  print("are we int he top10?")
  if int(DoubleLinkedThing[data["name"]]["rank"]) <= 10:
    create_top_10()

def save_list_loop():
  time.sleep(60)
    save_list()
    #save every 10 mins ~ temporary
def save_list():
  global DoubleLinkedThing
  global mapname
  python_db = os.path.join(os.getcwd(),"python-db","mapname",mapname)
  while True:
    time.sleep(60)
    #if somebody made a pb <pbwasmade>.file -> rem
    with open(python_db, 'wb+') as f:
      pickle.dump(DoubleLinkedThing,f)
def load_old_data():
  add_old_data = True
  global DoubleLinkedThing
  with open("old_data_list", 'rb') as f:
      old_data = pickle.load(f)

  i = 0 
  for x in old_data:
    if "." in old_data[x]["time"]:
      old_data[x]["time"] = 257
      old_data[x]["seen_first"] = old_data[x]["seen_last"]
    print(f"hello world !___ {old_data[x]['name']}")
    print(f'{old_data[x]["name"]} <----------------------APJ?????')
    lap_completed(old_data[x])
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)
def break_it():
  dict_data = {
                    "name":"Broken",
                    "time":-1,
                    "spb":1,
                    "s1":1,
                    "s2":1,
                    "s3":1,
                    "s4":1,
                    "slot":1
                  }
  lap_completed(dict_data)
  dict_data = {
                    "name":"Broken2",
                    "time":0,
                    "spb":1,
                    "s1":1,
                    "s2":1,
                    "s3":1,
                    "s4":1,
                    "slot":1
                  }
  lap_completed(dict_data)

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
      time = DoubleLinkedThing[str(getinfo)]["time"]
      last_seen = DoubleLinkedThing[str(getinfo)]["seen_last"]
      f.write(f"set pydb_data_{x} \"{name}\\{time}\\{last_seen}\"\n")
      getinfo = DoubleLinkedThing[str(getinfo)]["below"]
      if str(getinfo) == "last":
        break
  msg= ["sp_sc_func_exec pydb_make_top10"]
  udp_send(msg)

def main():
  global DoubleLinkedThing
  global sof_log_seek
  global log_seek
  global mapname
  size = 0
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
  python_db = os.path.join(os.getcwd(),"python-db","mapname")
  if not os.path.exists(python_db):
    os.makedirs(os.path.dirname(python_db))
  y = threading.Thread(target=save_list_loop)
  y.start()
  
  time.sleep(2)
  #break_it()
  #load_old_data()
  #testing()

if __name__ == '__main__':
  main()


