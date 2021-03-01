
import os
import threading 
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import json 
import time 
import os 
import pprint
import datetime
DoubleLinkedThing = {}

sof_log_dir = os.getcwd()
sof_log_seek = os.path.join(sof_log_dir,"sof_seek.log")
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
  if "sof.log" in event.src_path:
    print("modified")
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
                    "pb":data[4],
                    "rank":data[5],
                    "s1":data[6],
                    "s2":data[7],
                    "s3":data[8],
                    "s4":data[9]
                  }
            lap_completed(dict_data)
        else:
          print(f"not good {line[0:12]}")
    log_seek = os.path.getsize(event.src_path)
    with open(sof_log_seek, "w+") as f:
      f.write(str(log_seek))
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
  rank = data["rank"]
  if name not in DoubleLinkedThing:
    add_new(name,data)
  else:
    data_current = DoubleLinkedThing[str(name)]
    data_current["total"] += 1
    data_current["s1"] = s1
    data_current["s2"] = s2
    data_current["s3"] = s3
    data_current["s4"] = s4 
    data_current["seen_last"] = date_now
    data_current["time"] = pb_time
    if data["pb"] == 1:
      rank_up(name)
      pass

def create_list():
  global DoubleLinkedThing
  APJ = {
    "rank": 1,
    "below":"OPJ",
    "above":"1st",
    "time": 100,
    "total":1
  }
  OPJ = {
    "rank": 2,
    "below":"last",
    "above":"APJ",
    "time":200,
    "total":2
  }

  DoubleLinkedThing["first"] = "APJ"
  DoubleLinkedThing["last"] = "OPJ"
  DoubleLinkedThing["APJ"] = APJ
  DoubleLinkedThing["OPJ"] = OPJ

def add_new(name,data):
  global DoubleLinkedThing
  s1 = data["s1"]
  s2 = data["s2"]
  s3 = data["s3"]
  s4 = data["s4"]
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
  rank_up(name)

def section_pb(data):
  print(f"player {data['name']} got a pb on section {data['section']} time: {data['time']}")
  #debug_data(data)

def debug_data(data):
  for x in data:
    print(data[x])


def do_lap(name,time,pb,s1,s2,s3,s4):
  with open("sof.log", "a") as f:
    f.write("[" f"\"\\\\surf_db\\\\\",\"total_laps\",\"{name}\",{time},{pb},{s1},{s2},{s3},{s4}" + "]\n")

def testing():
  global DoubleLinkedThing
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(DoubleLinkedThing)
  do_lap("hello",600,1,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("hello",600,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",1,1,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",2,0,100,2,2,2,2)
  time.sleep(0.1)
  do_lap("plowsof",0,1,100,2,2,2,2)
  time.sleep(3)
  pp.pprint(DoubleLinkedThing)

def rank_up(name):
  global DoubleLinkedThing
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
    if self_above == "1st":
      DoubleLinkedThing[str(name)]["below"] = DoubleLinkedThing["first"]
      DoubleLinkedThing[str(name)]["above"] = "1st"
      DoubleLinkedThing["first"] = str(name)
      DoubleLinkedThing[str(compare_name)]["above"]=str(name)
      DoubleLinkedThing[str(name)]["rank"] = 1
      break
    self_below = DoubleLinkedThing[str(compare_name)]["below"]

    above_above = DoubleLinkedThing[str(self_above)]["above"]
    above_below = DoubleLinkedThing[str(self_above)]["below"]
    
    tmp_time = DoubleLinkedThing[str(self_above)]["time"]
    #if abovs time < than ours 
    if DoubleLinkedThing[str(self_above)]["time"] >= original_time:        
      if not initial_changes:
        if self_below == "last":
          DoubleLinkedThing["last"] = self_above
          DoubleLinkedThing[str(self_above)]["below"] = "last"
          self_below = "done"

        else:
          #belows above is now our above
          DoubleLinkedThing[str(self_below)]["above"] = str(self_above)
          DoubleLinkedThing[str(self_above)]["below"] = str(self_below)
        initial_changes = True

      DoubleLinkedThing[str(self_above)]["rank"] += 1
      compare_name = self_above
    else:
      if str(compare_name) != str(name):
        new_rank = DoubleLinkedThing[str(self_above)]["rank"]
        new_rank = new_rank + 1
        DoubleLinkedThing[str(name)]["rank"] = new_rank
        DoubleLinkedThing[str(name)]["below"] = str(self_below)
        DoubleLinkedThing[str(name)]["above"] = str(self_above)
        print(f"self above:{self_above} below:{self_below}")
        DoubleLinkedThing[str(self_above)]["below"] = str(name)
        #self_below = "last"
        if self_below != "last":
          DoubleLinkedThing[str(self_below)]["above"] =str(name)
          pass
      break
  #we're ranked
  new_rank = DoubleLinkedThing[str(name)]["rank"]
  print(f"{name} was ranked: {original_rank} new_rank: {new_rank}")


def main():
  global sof_log_seek
  global log_seek
  size = 0
  create_list()
  if os.path.isfile(sof_log_seek):
    with open(sof_log_seek, "r") as f:
      size = f.readlines()[0]
  else:
    with open(sof_log_seek,"w+") as f:
      f.write("0")
  log_seek = size
  x = threading.Thread(target=start_observer)
  x.start()
  time.sleep(2)
  testing()

if __name__ == '__main__':
  main()

