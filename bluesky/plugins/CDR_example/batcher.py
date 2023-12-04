n_scenarios = 4
traffic_densities = [10, 15 ,20]
fileheader = "CDR_TRAJ_PRED"
filelist = []

for density in traffic_densities:
    for seed in range(n_scenarios):
        f = open(rf"C:\Coding\bluesky_fork2\scenario\batches\scenarios\{fileheader}_{seed}_{density}.scn","w")
        
        f.write(f"00:00:00>trafficnumber {density} \n")
        f.write(f"00:00:00>SEED {seed} \n")
        f.write(f"00:00:00>cdmethod jasoncd \n")
        f.write(f"00:00:00>reso jasoncr \n")
        f.write(f"00:00:00>startlogs \n")
        f.write(f"00:00:01>FF")
        filelist.append(f"{fileheader}_{seed}_{density}")
        
f_bat = open(rf"C:\Coding\bluesky_fork2\scenario\batch.scn","w")
for file in filelist:
    f_bat.write(f"00:00:00.00>SCEN {file} \n")
    f_bat.write(f"00:00:00.00>PCALL batches\scenarios\{file}.scn \n")
    f_bat.write(f"00:00:00>SCHEDULE 00:30:00 HOLD \n")
    f_bat.write(f"00:00:00.00>FF \n \n")

    
        
        
