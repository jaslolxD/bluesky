n_scenarios = 10
traffic_densities = [40, 60, 80, 100, 120, 140]
fileheader_cdr = "CDR_TRAJ_PRED"
fileheader_state = "CDR_STATE"

filelist = []

for density in traffic_densities:
    for seed in range(n_scenarios):
        f = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_cdr}_{seed}_{density}.scn","w")
        
        f.write(f"00:00:00>trafficnumber {density} \n")
        f.write(f"00:00:00>SEED {seed} \n")
        f.write(f"00:00:00>cdmethod jasoncd \n")
        f.write(f"00:00:00>reso jasoncr \n")
        f.write(f"00:00:00>startlogs \n")
        f.write(f"00:00:01>FF")
        
        f_state = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader_state}_{seed}_{density}.scn","w")
        f_state.write(f"00:00:00>trafficnumber {density} \n")
        f_state.write(f"00:00:00>SEED {seed} \n")
        f_state.write(f"00:00:00>cdmethod SBCD \n")
        f_state.write(f"00:00:00>reso SBCR \n")
        f_state.write(f"00:00:00>startlogs \n")
        f_state.write(f"00:00:01>FF")
        
        
        
        filelist.append(f"{fileheader_cdr}_{seed}_{density}")
        filelist.append(f"{fileheader_state}_{seed}_{density}")
        
f_bat = open(rf"C:\Coding\bluesky_fork2\scenario\batch.scn","w")
for file in filelist:
    f_bat.write(f"00:00:00.00>SCEN {file} \n")
    f_bat.write(f"00:00:00.00>PCALL batches/scenarios/{file}.scn \n")
    f_bat.write(f"00:00:00>SCHEDULE 01:00:00 HOLD \n")
    f_bat.write(f"00:00:00.00>FF \n \n")

    
        
        
