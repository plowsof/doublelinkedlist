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
log_seek = 0

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
            mapname = data[2]
            set_map(mapname)
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
  date_now = datetime.datetime.now().date().isoformat()
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
    last_seen = info["seen_last"]
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
        pass

#each map has a seperate list
def set_map(mapname):
  global DoubleLinkedThing
  DoubleLinkedThing = {}
  python_db = os.path.join(os.getcwd(),"python-db","mapname",mapname)
  if os.path.isfile(python_db):
    with open(python_db, 'rb') as f:
      DoubleLinkedThing = pickle.load(f)
  else:
    create_list()
    with open(python_db, 'wb+') as f:
      pickle.dump(DoubleLinkedThing,f)

  #load pickled list <mapname>.pickle
def create_list():
  global DoubleLinkedThing
  APJ = {
    "rank": 1,
    "below":"OP",
    "above":"1st",
    "time": 100,
    "total":5
  }
  OP = {
    "rank": 2,
    "below":"last",
    "above":"APJ",
    "time":200,
    "total":1
  }

  DoubleLinkedThing["first"] = "APJ"
  DoubleLinkedThing["last"] = "OP"
  DoubleLinkedThing["APJ"] = APJ
  DoubleLinkedThing["OP"] = OP

def add_new(data):
  global DoubleLinkedThing
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
  print("After add_new done, before rank up")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)

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
  global DoubleLinkedThing
  name = data["name"]
  slot = data["slot"]
  original_data = DoubleLinkedThing[str(name)]
  original_rank = original_data["rank"]
  original_prev = original_data["below"]
  original_next = original_data["above"]
  original_time = original_data["time"]
  new_rank = original_rank
  compare_name = name
  initial_changes = False
  
  while True:
    self_above = DoubleLinkedThing[str(compare_name)]["above"]
    self_below = DoubleLinkedThing[str(compare_name)]["below"]
    if self_above == "1st":
      DoubleLinkedThing[str(name)]["below"] = str(DoubleLinkedThing["first"])
      DoubleLinkedThing[str(name)]["above"] = "1st"
      DoubleLinkedThing["first"] = str(name)
      DoubleLinkedThing[str(compare_name)]["above"]=str(name)
      DoubleLinkedThing[str(name)]["rank"] = 1
      break
    aboves_below = DoubleLinkedThing[str(self_above)]["below"]
    #if abovs time < than ours 
    if int(DoubleLinkedThing[str(self_above)]["time"]) >= int(original_time):        
      if not initial_changes:
        if self_below == "last":
          print("we're last")
          DoubleLinkedThing["last"] = str(self_above)
          DoubleLinkedThing[str(self_above)]["below"] = "last"

        else:
          #belows above is now our above
          DoubleLinkedThing[str(self_below)]["above"] = str(self_above)
          DoubleLinkedThing[str(self_above)]["below"] = str(self_below)
        initial_changes = True
      DoubleLinkedThing[str(self_above)]["rank"] += 1
      new_rank -= 1
      compare_name = self_above
      print(f"compare name: {compare_name}")
      pp = pprint.PrettyPrinter(indent=4)
      pp.pprint(DoubleLinkedThing)

    else:
      break
  #we're ranked
  #comparenames APJ
  #self_below=OP
  new_rank = DoubleLinkedThing[str(name)]["rank"]
  print(f"orig: {original_rank} new: {new_rank}")
  if original_rank != new_rank & new_rank != 1:
    #print change
    msg = [f"sp_sc_func_exec broadcast_new_rank \"{name}\" \"{new_rank}\" \"{slot}\""]
    udp_send(msg)
    DoubleLinkedThing[str(name)]["rank"] = new_rank
    print(f"comparenames {compare_name}")
    DoubleLinkedThing[str(compare_name)]["below"] = str(name)
    print(f"self_below={self_below}")
    DoubleLinkedThing[str(self_below)]["above"] = str(name)
    DoubleLinkedThing[str(name)]["above"] = str(compare_name)
    DoubleLinkedThing[str(name)]["below"] = str(self_below)

  else:
    print("no rank change / we're last / we're first")
    #print(f"{name} was ranked: {original_rank} new_rank: {new_rank}")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)

def save_list():
  global DoubleLinkedThing
  global mapname
  python_db = os.path.join(os.getcwd(),"python-db","mapname",mapname)
  while True:
    time.sleep(600)
    #if somebody made a pb <pbwasmade>.file -> rem
    with open(python_db, 'wb+') as f:
      pickle.dump(DoubleLinkedThing,f)
    #save every 10 mins ~ temporary
    
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
  y = threading.Thread(target=save_list)
  y.start()
  time.sleep(2)
  #testing()

if __name__ == '__main__':
  main()
