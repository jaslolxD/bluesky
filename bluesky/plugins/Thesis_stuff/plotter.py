import matplotlib.pyplot as plt
import os
import pandas as pd
directory = os.listdir(r"bluesky\plugins\Thesis_stuff\output_second_run")
conflog_40_state = []
conflog_60_state = []
conflog_80_state = []
conflog_100_state = []
conflog_120_state = []
conflog_140_state = []

conflog_40_traj = []
conflog_60_traj = []
conflog_80_traj = []
conflog_100_traj = []
conflog_120_traj = []
conflog_140_traj = []
for file in directory:
    if "FLSTLOG_CDR_STATE" in file and "WASLOSLOG" not in file:
        #conflog [28:31] and [28:30]
        #loslog  [19:22] and [19:23]
        #flstlog [20:23] and [20:22]
        if file[20:23] == "100":
            conflog_100_state.append(file)
        elif file[20:23] == "120":
            conflog_120_state.append(file)
        elif file[20:23] == "140":
            conflog_140_state.append(file)
        elif file[20:22] == "80":
            conflog_80_state.append(file)
        elif file[20:22] == "60":
            conflog_60_state.append(file)
        else: 
            conflog_40_state.append(file)
        
    elif "FLSTLOG_CDR_TRAJ_PRED" in file and "WASLOSLOG" not in file:
        #conflog [32:35] [32:34]
        #loslog [23:26] [23:25]
        #flst [24:27] [24:26]
        if file[24:27] == "100":
            conflog_100_traj.append(file)
        elif file[24:27] == "120":
            conflog_120_traj.append(file)
        elif file[24:27] == "140":
            conflog_140_traj.append(file)
        elif file[24:26] == "80":
            conflog_80_traj.append(file)
        elif file[24:26] == "60":
            conflog_60_traj.append(file)
        else: 
            conflog_40_traj.append(file)
            
conf_number = []
conf_data= [conflog_40_state, conflog_40_traj, conflog_60_state, conflog_60_traj, conflog_80_state, conflog_80_traj,  conflog_100_state, conflog_100_traj, conflog_120_state, conflog_120_traj, conflog_140_state, conflog_140_traj]
variable = 0
for scenario in conf_data:
    conf_number_sub = [] 
    if variable == 0 or variable == 1:
        counter_orig = 40
        
    elif variable == 2 or variable == 3:
        counter_orig = 60
        
    elif variable == 4 or variable == 5:
        counter_orig = 80
        
    elif variable == 6 or variable == 7:
        counter_orig = 100
        
    elif variable == 8 or variable == 9:
        counter_orig = 120
        
    elif variable == 10 or variable == 11:
        counter_orig = 140
        
    counter = counter_orig
    for log in scenario:
        #f= open(rf"bluesky\plugins\Thesis_stuff\output_second_run\{log}")
        #print(f.read())
        data = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_second_run\{log}", sep = ",", skiprows= 9,  header = None)
        # conflog: data.columns = ["simt", "confid", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2"]
        #loslog: data.columns = ["simt", "losexit", "losstart", "tomd", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2", "intersect"]
        data.columns = ["delt", "id", "spawnt", "flighttime", "1", "2", "3", "4","5","6","7","8","9","10","11", "12", "13", "14"]
        for i in range(len(data)):
            callid = f"DR{counter +1}"
            if (data["id"] == callid).any():
                data.loc[data.id == callid, "spawnt"] = data.iloc[i].delt
                data.loc[data.id == callid, "flighttime"] = data.loc[data.id == callid].delt - data.iloc[i].delt
            counter +=1 
        
        
        conf_number_sub.append(data["flighttime"].mean())
    conf_number.append(conf_number_sub)
    variable +=1 

print(conf_number)
datastring = ["State 40", "Traj 40", "State 60", "Traj 60", "State 80", "Traj 80", "State 100", "Traj 100", "State 120", "Traj 120", "State 140", "Traj 140" ]

sliced_conf = []
sliced_string = []
i=0
while i < len(datastring):
    sliced_conf.append(conf_number[i])
    sliced_string.append(datastring[i])
    i +=2

print(sliced_conf)
fig = plt.figure(figsize =(10, 7))
ax = fig.add_subplot(111)
bp = ax.boxplot(conf_number)
plt.title("Average flight duration")
ax.set_ylabel("time in seconds")
ax.set_xticklabels(datastring)
plt.show()
#f= open(rf"bluesky\plugins\Thesis_stuff\output_second_run\{conflog_100_state[0]}")
#print(f.read())