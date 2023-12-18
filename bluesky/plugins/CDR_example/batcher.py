n_scenarios = 10
traffic_densities = [40] #, 60, 80, 100, 120, 140]
lookahead_time = [30, 20, 10]
fileheader_cdr_CDR = "CD_RESO_TRAJ_PRED"
fileheader_cdr_CD = "CD_TRAJ_PRED"
fileheader_state_CDR = "CD_RESO_STATE"
fileheader_state_CD = "CD_STATE"

filelist = []

for density in traffic_densities:
    for seed in range(n_scenarios):
        for time in lookahead_time:
            f = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_cdr_CDR}_{seed}_{density}_{time}.scn","w")
#
            f.write(f"00:00:00>trafficnumber {density} \n")
            f.write(f"00:00:00>SEED {seed} \n")
            f.write(f"00:00:00>cdmethod jasoncd \n")
            f.write(f"00:00:00>setlookahead {time} \n")
            f.write(f"00:00:00>reso jasoncr \n")
            f.write(f"00:00:00>startlogs \n")
            f.write(f"00:00:01>FF")
            
            f = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_cdr_CD}_{seed}_{density}_{time}.scn","w")
#
            f.write(f"00:00:00>trafficnumber {density} \n")
            f.write(f"00:00:00>SEED {seed} \n")
            f.write(f"00:00:00>cdmethod jasoncd \n")
            f.write(f"00:00:00>setlookahead {time} \n")
            f.write(f"00:00:00>startlogs \n")
            f.write(f"00:00:01>FF")
        
        #f_state = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_state_CDR}_{seed}_{density}_30.scn","w")
        #f_state.write(f"00:00:00>trafficnumber {density} \n")
        #f_state.write(f"00:00:00>SEED {seed} \n")
        #f_state.write(f"00:00:00>cdmethod SBCD \n")
        #f_state.write(f"00:00:00>reso SBCR \n")
        #f_state.write(f"00:00:00>startlogs \n")
        #f_state.write(f"00:00:01>FF")
        #
        #f_state_CD = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_state_CD}_{seed}_{density}_30.scn","w")
        #f_state_CD.write(f"00:00:00>trafficnumber {density} \n")
        #f_state_CD.write(f"00:00:00>SEED {seed} \n")
        #f_state_CD.write(f"00:00:00>cdmethod SBCD \n")
        #f_state_CD.write(f"00:00:00>startlogs \n")
        #f_state_CD.write(f"00:00:01>FF")
        #
        #
        #
            filelist.append(f"{fileheader_cdr_CDR}_{seed}_{density}_{time}")
            filelist.append(f"{fileheader_cdr_CD}_{seed}_{density}_{time}")
        #filelist.append(f"{fileheader_state_CDR}_{seed}_{density}_30")
        #filelist.append(f"{fileheader_state_CD}_{seed}_{density}_30")
        
f_bat = open(rf"C:\Coding\bluesky_fork2\scenario\batch_TRAJ_40.scn","w")
for file in filelist:
    f_bat.write(f"00:00:00.00>SCEN {file} \n")
    f_bat.write(f"00:00:00.00>PCALL batches/scenarios/{file}.scn \n")
    f_bat.write(f"00:00:00>SCHEDULE 01:00:00 HOLD \n")
    f_bat.write(f"00:00:00.00>FF \n \n")

    
        
        
