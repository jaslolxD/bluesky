import matplotlib.pyplot as plt
import os
import pandas as pd
from statistics import mean

directory_state = os.listdir(r"bluesky\plugins\Thesis_stuff\output_state")
directory_traj = os.listdir(r"bluesky\plugins\Thesis_stuff\output_traj")
directory_all = os.listdir(r"bluesky\plugins\Thesis_stuff\output_all1")

def datagather(directory, logtype, index_traf):
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
    index_traf_1 = index_traf[0]
    index_traf_2 = index_traf[1]
    index_traf_3 = index_traf[2]
    index_traf_4 = index_traf[3]
    for file in directory:
        if logtype[0] in file and "WASLOSLOG" not in file:
            #conflog [28:31] and [28:30]
            #loslog  [19:22] and [19:23]
            #flstlog [20:23] and [20:22]
            if file[index_traf_1[0]:index_traf_1[1]] == "100":
                conflog_100_state.append(file)
            elif file[index_traf_1[0]:index_traf_1[1]] == "120":
                conflog_120_state.append(file)
            elif file[index_traf_1[0]:index_traf_1[1]] == "140":
                conflog_140_state.append(file)
            elif file[index_traf_2[0]:index_traf_2[1]] == "80":
                conflog_80_state.append(file)
            elif file[index_traf_2[0]:index_traf_2[1]] == "60":
                conflog_60_state.append(file)
            else: 
                conflog_40_state.append(file)

        elif logtype[1] in file and "WASLOSLOG" not in file:
            #conflog [32:35] [32:34]
            #loslog [23:26] [23:25]
            #flst [24:27] [24:26]
            if file[index_traf_3[0]:index_traf_3[1]] == "100":
                conflog_100_traj.append(file)
            elif file[index_traf_3[0]:index_traf_3[1]] == "120":
                conflog_120_traj.append(file)
            elif file[index_traf_3[0]:index_traf_3[1]] == "140":
                conflog_140_traj.append(file)
            elif file[index_traf_4[0]:index_traf_4[1]] == "80":
                conflog_80_traj.append(file)
            elif file[index_traf_4[0]:index_traf_4[1]] == "60":
                conflog_60_traj.append(file)
            else: 
                conflog_40_traj.append(file)

    return [conflog_40_state, conflog_40_traj, conflog_60_state, conflog_60_traj, conflog_80_state, conflog_80_traj,  conflog_100_state, conflog_100_traj, conflog_120_state, conflog_120_traj, conflog_140_state, conflog_140_traj]

def datagatherlookahead(lookahead, directory, logtype, index_traf):
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
    index_traf_1 = index_traf[0]
    index_traf_2 = index_traf[1]
    index_traf_3 = index_traf[2]
    index_traf_4 = index_traf[3]
    for file in directory:
        if logtype[0] in file and "WASLOSLOG" not in file:
            #conflog [28:31] and [28:30]
            #loslog  [19:22] and [19:23]
            #flstlog [20:23] and [20:22]
            if file[index_traf_1[0]:index_traf_1[1]] == "100" and file[index_traf_1[0]+4:index_traf_1[1]+3] == str(lookahead):
                conflog_100_state.append(file)
            elif file[index_traf_1[0]:index_traf_1[1]] == "120" and file[index_traf_1[0]+4:index_traf_1[1]+3] == str(lookahead):
                conflog_120_state.append(file)
            elif file[index_traf_1[0]:index_traf_1[1]] == "140" and file[index_traf_1[0]+4:index_traf_1[1]+3] == str(lookahead):
                conflog_140_state.append(file)
            elif file[index_traf_2[0]:index_traf_2[1]] == "80" and file[index_traf_2[0]+3:index_traf_2[1]+3] == str(lookahead):
                conflog_80_state.append(file)
            elif file[index_traf_2[0]:index_traf_2[1]] == "60"and file[index_traf_2[0]+3:index_traf_2[1]+3] == str(lookahead):
                conflog_60_state.append(file) 
            elif file[index_traf_2[0]:index_traf_2[1]] == "40"and file[index_traf_2[0]+3:index_traf_2[1]+3] == str(lookahead): 
                conflog_40_state.append(file)

        elif logtype[1] in file and "WASLOSLOG" not in file:
            #conflog [32:35] [32:34]
            #loslog [23:26] [23:25]
            #flst [24:27] [24:26]
            if file[index_traf_3[0]:index_traf_3[1]] == "100" and file[index_traf_3[0]+4:index_traf_3[1]+3] == str(lookahead):
                conflog_100_traj.append(file)
            elif file[index_traf_3[0]:index_traf_3[1]] == "120" and file[index_traf_3[0]+4:index_traf_3[1]+3] == str(lookahead):
                conflog_120_traj.append(file)
            elif file[index_traf_3[0]:index_traf_3[1]] == "140" and file[index_traf_3[0]+4:index_traf_3[1]+3] == str(lookahead):
                conflog_140_traj.append(file)
            elif file[index_traf_4[0]:index_traf_4[1]] == "80" and file[index_traf_4[0]+3:index_traf_4[1]+3] == str(lookahead):
                conflog_80_traj.append(file)
            elif file[index_traf_4[0]:index_traf_4[1]] == "60" and file[index_traf_4[0]+3:index_traf_4[1]+3] == str(lookahead):
                conflog_60_traj.append(file)
            elif file[index_traf_4[0]:index_traf_4[1]] == "40" and file[index_traf_4[0]+3:index_traf_4[1]+3] == str(lookahead): 
                conflog_40_traj.append(file)

    return [conflog_40_state, conflog_40_traj, conflog_60_state, conflog_60_traj, conflog_80_state, conflog_80_traj,  conflog_100_state, conflog_100_traj, conflog_120_state, conflog_120_traj, conflog_140_state, conflog_140_traj]

#string = "CDR_CONFLICTLOG_CD_RESO_STATE_5_100_10_20231211_09-48-11.log"
#print(string.find("100"))
#conflog traj reso [36:39]
#conflog traj cd [32:35]
#loslog traj reso [27:30]
#loslog traj cd [22:25]
#flstlog traj reso [28:31]
#flstlog traj cd [23:26]

#conflog state reso [32:35]
#conflog state cd [27:30]
#loslog state reso [23:26]
#loslog state cd [18:21]
#flstlog state reso [24:27]
#flstlog state cd [19:22]

def conflictcounter(conflict_files):
    conf_number =[]
    for scenario in conflict_files:
        conf_number_sub=[]
        for log in scenario:
            f= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}")
            data = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}", sep = ",", skiprows= 9,  header = None)
            data.columns = ["simt", "confid", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2"]
            conf_number_sub.append(max(data["confid"])-1)
        conf_number.append(conf_number_sub)
    return(conf_number)

def loscounter(los_files):
    los_number =[]
    for scenario in los_files:
        los_number_sub=[]
        for log in scenario:
            f= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}")
            data = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}", sep = ",", skiprows= 9,  header = None)
            data.columns = ["losexit", "losstart", "tomd", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2", "dist", "intersect"]
            los_number_sub.append(len(data[data["intersect"] ==1]))
        los_number.append(los_number_sub)
    return los_number

def fdcounter(cd_files, cdr_files):
    fd_number = []
    for i in range(len(cdr_files)):
        fd_number_sub=[]
        for j in range(len(cdr_files[i])):
            fd_number_sub_sub=[]
            f= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{cd_files[i][j]}")
            f2= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{cdr_files[i][j]}")
            data_cd = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_all1\{cd_files[i][j]}", sep = ",", skiprows= 9,  header = None)
            data_cd.columns = ["delt", "id", "spawnt", "flighttime", "dist", "2", "3", "lat","lon","6","7","8","9","10","11", "12", "13", "14"]
            data_cdr = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_all1\{cdr_files[i][j]}", sep = ",", skiprows= 9,  header = None)
            data_cdr.columns = ["delt", "id", "spawnt", "flighttime", "dist", "2", "3", "lat","lon","6","7","8","9","10","11", "12", "13", "14"]
            for acid in data_cdr["id"]:
                try:
                    float(data_cdr[data_cdr["id"] == acid].lat.iloc[0]) == float(data_cd[data_cd["id"] == acid].lat.iloc[0])
                except:
                    continue
                else:
                    if float(data_cdr[data_cdr["id"] == acid].lat.iloc[0]) == float(data_cd[data_cd["id"] == acid].lat.iloc[0]) and float(data_cdr[data_cdr["id"] == acid].lon.iloc[0]) == float(data_cd[data_cd["id"] == acid].lon.iloc[0]):
                        ft1 = float(data_cdr[data_cdr["id"] == acid].flighttime.iloc[0])
                        ft2 = float(data_cd[data_cd["id"] == acid].flighttime.iloc[0])
                        #print(ft1, ft2)
                        fd_number_sub_sub.append(ft1- ft2)
                #print(fd_number_sub_sub)
            fd_number_sub.append(mean(fd_number_sub_sub))
        fd_number.append(fd_number_sub)
    return fd_number

def distanceflown(cdr_files):
    dist_number =[]
    for scenario in cdr_files:
        dist_number_sub=[]
        for log in scenario:
            print(log)
            f= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}")
            data = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_all1\{log}", sep = ",", skiprows= 9,  header = None)
            data.columns = ["delt", "id", "spawnt", "flighttime", "dist", "2", "3", "lat","lon","6","7","8","9","10","11", "12", "13", "14"]
            dist_number_sub.append(data["dist"].sum())
        dist_number.append(dist_number_sub)
    return dist_number
            

def sliceStateOnly(data, datastring):
    sliced_conf = []
    sliced_string = []
    i=0
    while i < len(datastring):
        sliced_conf.append(data[i])
        sliced_string.append(datastring[i])
        i +=2
    return sliced_conf, sliced_string

def sliceTrajOnly(data, datastring):
    sliced_conf = []
    sliced_string = []
    i=1
    while i < len(datastring):
        sliced_conf.append(data[i])
        sliced_string.append(datastring[i])
        i +=2
    return sliced_conf, sliced_string
    

#datastring = ["State 40", "Traj 40", "State 60", "Traj 60", "State 80", "Traj 80", "State 100", "Traj 100", "State 120", "Traj 120", "State 140", "Traj 140" ]
datastring = ["S40", "T40", "S60", "T60", "S80", "T80", "S100", "T100", "S120", "T120", "S140", "T140" ]

##Conflict stuff ------------------------------------------------------------------------------------------------------
conflict_files = datagather(directory_all, ["CDR_CONFLICTLOG_CD_RESO_STATE", "CDR_CONFLICTLOG_CD_RESO_TRAJ_PRED"], [[32,35], [32,34], [36,39], [36,38]])
conflict_files_10 = datagatherlookahead(10, directory_all, ["CDR_CONFLICTLOG_CD_RESO_STATE", "CDR_CONFLICTLOG_CD_RESO_TRAJ_PRED"], [[32,35], [32,34], [36,39], [36,38]])
conflict_files_20 = datagatherlookahead(20, directory_all, ["CDR_CONFLICTLOG_CD_RESO_STATE", "CDR_CONFLICTLOG_CD_RESO_TRAJ_PRED"], [[32,35], [32,34], [36,39], [36,38]])
conflict_files_30 = datagatherlookahead(30, directory_all, ["CDR_CONFLICTLOG_CD_RESO_STATE", "CDR_CONFLICTLOG_CD_RESO_TRAJ_PRED"], [[32,35], [32,34], [36,39], [36,38]])

data_conflicts = conflictcounter(conflict_files)
data_conflicts_10 = conflictcounter(conflict_files_10)
data_conflicts_20 = conflictcounter(conflict_files_20)
data_conflicts_30 = conflictcounter(conflict_files_30)
#
#slice_state_10, slice_state_string = sliceTrajOnly(data_conflicts_10,datastring)
#slice_state_20, slice_state_string = sliceTrajOnly(data_conflicts_20,datastring)
#slice_state_30, slice_state_string = sliceTrajOnly(data_conflicts_30,datastring)

#Los stuff--------------------------------------------------------------------------------------------------------------
#los_files = datagather(directory_all, ["LOSLOG_CD_RESO_STATE", "LOSLOG_CD_RESO_TRAJ_PRED"], [[23,26], [23,25], [27,30], [27,29]])
#los_files_10 = datagatherlookahead(10,directory_all, ["LOSLOG_CD_RESO_STATE", "LOSLOG_CD_RESO_TRAJ_PRED"], [[23,26], [23,25], [27,30], [27,29]])
#los_files_20 = datagatherlookahead(20,directory_all, ["LOSLOG_CD_RESO_STATE", "LOSLOG_CD_RESO_TRAJ_PRED"], [[23,26], [23,25], [27,30], [27,29]])
#los_files_30 = datagatherlookahead(30,directory_all, ["LOSLOG_CD_RESO_STATE", "LOSLOG_CD_RESO_TRAJ_PRED"], [[23,26], [23,25], [27,30], [27,29]])
#
#data_los = loscounter(los_files)
#data_los_10 = loscounter(los_files_10)
#data_los_20 = loscounter(los_files_20)
#data_los_30 = loscounter(los_files_30)
#
#slice_10, slice_string = sliceStateOnly(data_los_10,datastring)
#slice_20, slice_string = sliceStateOnly(data_los_20,datastring)
#slice_30, slice_string = sliceStateOnly(data_los_30,datastring)

#Flight delay -----------------------------------------------------------------------------------
#fd_files_cd = datagather(directory_all, ["FLSTLOG_CD_STATE", "FLSTLOG_CD_TRAJ_PRED"], [[19,22], [19,21], [23,26], [23,25]])
#fd_files_cdr = datagather(directory_all, ["FLSTLOG_CD_RESO_STATE", "FLSTLOG_CD_RESO_TRAJ_PRED"], [[24,27], [24,26], [28,31], [28,30]])

#data_fd = fdcounter(fd_files_cd, fd_files_cdr)
#data_fd = [[2.2785714285714285, 10.544642857142858, 0.9342105263157895, 0.7156862745098039, 0.5727272727272728, 2.357142857142857, 1.6875, 0.6111111111111112, 1.1170212765957446, 0.0, 0.2734375, 1.0774647887323943, 1.76, 1.475609756097561, 0.0, 0.0, 0.0, 2.196629213483146, 2.0934065934065935, 2.075, 0.7804878048780488, 0.0, 2.3125, 3.3548387096774195, 1.0517241379310345, 0.0, 0.4090909090909091, 0.4603174603174603, 0.0, 0.0196078431372549], [1.5934065934065933, 1.3762376237623761, 1.40625, 0.660377358490566, 0.0, 1.1842105263157894, -3.0616438356164384, 0.0, 0.0, 1.4291044776119404, 1.4715909090909092, 0.031578947368421054, 0.676056338028169, 0.9285714285714286, 18.337209302325583, 0.8461538461538461, 0.9545454545454546, 5.375, 0.375, 1.6914893617021276, 0.4935064935064935, 1.4864864864864864, 0.0, 0.34210526315789475, 2.9152542372881354, 0.09836065573770492, 0.0, 0.9882352941176471, 0.7777777777777778, 0.7359550561797753], [2.8, 5.127906976744186, 11.775862068965518, 0.8518518518518519, 0.2564102564102564, 5.017857142857143, 3.1323529411764706, 2.610526315789474, 4.453125, 0.8771929824561403, 6.549180327868853, 0.36666666666666664, 1.3191489361702127, 3.810810810810811, 1.9285714285714286, 0.45652173913043476, 3.4347826086956523, 3.2697368421052633, 2.3013698630136985, 0.0, 3.909090909090909, 0.9838709677419355, 20.428571428571427, 9.954545454545455, 0.24324324324324326, 2.892156862745098, 1.8095238095238095, 1.295774647887324, 0.23, 7.088235294117647], [1.8412698412698412, 0.4954545454545455, 2.534090909090909, 0.2644230769230769, 0.675, 0.9945652173913043, 0.6293103448275862, 0.2909090909090909, 0.17307692307692307, 1.1478260869565218, 1.7191780821917808, 1.7463768115942029, 4.104651162790698, 0.21875, 0.7419354838709677, 1.8351063829787233, 0.8571428571428571, 1.7023809523809523, 0.28125, 0.07142857142857142, 3.1666666666666665, 0.175, 0.28125, 0.3469387755102041, 0.0410958904109589, 0.18032786885245902, 0.39655172413793105, 0.905982905982906, 0.8939393939393939, 1.3452380952380953], [1.736842105263158, 4.336956521739131, 2.0208333333333335, 3.336734693877551, 0.1746031746031746, 6.755813953488372, 0.9913793103448276, 3.2205882352941178, 5.681818181818182, 0.5652173913043478, 0.0, 13.289473684210526, 2.7642857142857142, 4.895348837209302, 2.4444444444444446, 0.20093457943925233, 0.3780487804878049, 2.6491228070175437, 2.019230769230769, 3.5, 4.723684210526316, 2.515625, 4.012820512820513, 6.9375, 0.9841269841269841, 8.91, 14.025, 1.7053571428571428, 0.013513513513513514, 6.1], [0.4017857142857143, 0.2962962962962963, 1.219298245614035, 0.7, 0.15517241379310345, 0.061224489795918366, 0.6818181818181818, 0.7661290322580645, 0.28431372549019607, 0.023255813953488372, 0.2625, 0.11267605633802817, 1.0841584158415842, 0.2717391304347826, 0.3953488372093023, 0.7327586206896551, 1.5460526315789473, 1.3098591549295775, 0.515625, 0.8773584905660378, 2.5392156862745097, 0.35294117647058826, 0.06818181818181818, 0.06976744186046512, 0.07792207792207792, 0.0, 0.8068181818181818, 0.3148148148148148, 0.2018348623853211, 0.0], [3.3839285714285716, 1.0517241379310345, 1.484375, 4.1911764705882355, 3.0217391304347827, 6.321428571428571, 1.2032967032967032, 6.1521739130434785, 9.0, 0.7555555555555555, 2.3076923076923075, 6.0606060606060606, 1.5104166666666667, 2.375, 7.642857142857143, 2.5267857142857144, 4.990384615384615, 8.55, 2.5784313725490198, 4.024390243902439, 3.9, 2.3068181818181817, 9.96, 17.285714285714285, 2.8666666666666667, 7.0, 2.1, 3.5434782608695654, 4.5, 3.576923076923077], [0.7640449438202247, 0.2621951219512195, 1.3636363636363635, 0.373015873015873, 0.15833333333333333, 0.1557377049180328, 0.53125, 1.0217391304347827, 0.5652173913043478, 0.5, 0.5563380281690141, 0.17857142857142858, 2.0357142857142856, 0.16, 1.8555555555555556, 0.6117021276595744, 0.0, 1.037037037037037, 0.20625, 0.5066666666666667, 0.21212121212121213, 0.3238095238095238, 0.8028169014084507, 0.21014492753623187, 0.3492063492063492, 0.0, -0.1118421052631579, 0.5993377483443708, 0.4883720930232558, 0.05660377358490566], [5.572916666666667, 2.957627118644068, 7.7, 0.28378378378378377, 1.380952380952381, 3.3, 0.7272727272727273, 4.297297297297297, 3.097560975609756, 3.576923076923077, 4.0606060606060606, 6.53125, 2.2063492063492065, 2.2872340425531914, 4.631578947368421, 1.125, 4.709302325581396, 8.211538461538462, 2.5793650793650795, 6.557142857142857, 18.428571428571427, 1.1044776119402986, 2.5865384615384617, 19.73076923076923, 0.8378378378378378, 0.0, 0.475, 2.9166666666666665, 3.5555555555555554, 16.847826086956523], [0.3048780487804878, 0.4897959183673469, 0.057692307692307696, -12.972727272727273, 0.6339285714285714, 9.073170731707316, 0.6436781609195402, 0.38271604938271603, 0.9466666666666667, 0.5, 0.2318840579710145, 0.20238095238095238, 0.5104166666666666, 0.22535211267605634, 1.2063492063492063, 0.3103448275862069, 0.08928571428571429, 0.9196428571428571, 0.3238095238095238, 0.3425925925925926, 0.20394736842105263, 0.32608695652173914, 0.6118421052631579, 0.16037735849056603, 0.17721518987341772, 0.6428571428571429, 1.0422535211267605, 0.7272727272727273, 0.36363636363636365, 0.37037037037037035], [5.833333333333333, 1.8857142857142857, 13.05, 1.1219512195121952, 10.26923076923077, 18.785714285714285, 0.47619047619047616, 2.6702127659574466, 1.85, 1.4150943396226414, 1.3076923076923077, 18.710526315789473, 7.650943396226415, 0.5, 0.5555555555555556, 0.2, 1.0, 13.25, 4.0131578947368425, 0.2903225806451613, 1.8333333333333333, 3.963235294117647, 1.8333333333333333, 29.1, 3.4705882352941178, 2.15, 24.142857142857142, 6.40625, 2.6346153846153846, 6.678571428571429], [0.7830188679245284, 0.8666666666666667, 0.09803921568627451, -13.601851851851851, 0.5, 0.19090909090909092, 1.18125, 0.5785714285714286, 0.25757575757575757, 1.232394366197183, 0.5958904109589042, 0.815068493150685, -0.06896551724137931, 0.22131147540983606, 0.41, 0.6015625, 0.15833333333333333, 0.32727272727272727, 0.3404255319148936, 0.0, 1.9926470588235294, 0.5108695652173914, 0.45, 0.47619047619047616, 0.5769230769230769, 0.17105263157894737, 0.7884615384615384, 2.1862745098039214, 0.5277777777777778, 0.58]]

#Distance flown ----------------------------------------------------------------------------------
#df_files_cdr = datagather(directory_all, ["FLSTLOG_CD_STATE", "FLSTLOG_CD_TRAJ_PRED"], [[19,22], [19,21], [23,26], [23,25]])
df_files_cdr = datagather(directory_all, ["FLSTLOG_CD_RESO_STATE", "FLSTLOG_CD_RESO_TRAJ_PRED"], [[24,27], [24,26], [28,31], [28,30]])

data_df = distanceflown(df_files_cdr)

fig = plt.figure(figsize =(10, 7))
plt.title("Conflicts")
plt.xticks([])
plt.yticks([])
ax = fig.add_subplot(111)
ax.boxplot(data_conflicts)
ax.set_ylabel("No. conflicts")
ax.set_xticklabels(datastring)
plt.show()

 
#Subplots -------------------------------------------------------------    
#fig = plt.figure(figsize =(10, 7))
#plt.title("Amount of LoS state-based")
#plt.xticks([])
#plt.yticks([])
#ax = fig.add_subplot(221)
#ax.boxplot(slice_10)
#ax.set_ylabel("No. LoS")
#ax.set_title("t_lookahead = 10s")
#ax.set_xticklabels(slice_string)
#
#ax = fig.add_subplot(222)
#ax.boxplot(slice_20)
#ax.set_ylabel("No. LoS")
#ax.set_title("t_lookahead = 20s")
#ax.set_xticklabels(slice_string)
#
#ax = fig.add_subplot(223)
#ax.boxplot(slice_30)
#ax.set_ylabel("No. LoS")
#ax.set_title("t_lookahead = 30s")
#ax.set_xticklabels(slice_string)
#
#plt.show()


#conf_number = []
#variable = 0
#for scenario in conf_data:
#    conf_number_sub = [] 
#    if variable == 0 or variable == 1:
#        counter_orig = 40
#    
#    elif variable == 2 or variable == 3:
#        counter_orig = 60
#    
#    elif variable == 4 or variable == 5:
#        counter_orig = 80
#    
#    elif variable == 6 or variable == 7:
#        counter_orig = 100
#    
#    elif variable == 8 or variable == 9:
#        counter_orig = 120
#    
#    elif variable == 10 or variable == 11:
#        counter_orig = 140
#    
#    counter = counter_orig
#    for log in scenario:
#        #f= open(rf"bluesky\plugins\Thesis_stuff\output_second_run\{log}")
#        #print(f.read())
#        data = pd.read_csv(rf"bluesky\plugins\Thesis_stuff\output_second_run\{log}", sep = ",", skiprows= 9,  header = None)
#        # conflog: data.columns = ["simt", "confid", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2"]
#        #loslog: data.columns = ["simt", "losexit", "losstart", "tomd", "DR1", "DR2", "latDR1", "lonDR1", "alt1", "latDR2", "lonDR2", "alt2", "intersect"]
#        data.columns = ["delt", "id", "spawnt", "flighttime", "1", "2", "3", "4","5","6","7","8","9","10","11", "12", "13", "14"]
#        for i in range(len(data)):
#            callid = f"DR{counter +1}"
#            if (data["id"] == callid).any():
#                data.loc[data.id == callid, "spawnt"] = data.iloc[i].delt
#                data.loc[data.id == callid, "flighttime"] = data.loc[data.id == callid].delt - data.iloc[i].delt
#            counter +=1 
#        
#        conf_number_sub.append(data["flighttime"].mean())
#    conf_number.append(conf_number_sub)
#    variable +=1 

#datastring = ["State 40", "Traj 40", "State 60", "Traj 60", "State 80", "Traj 80", "State 100", "Traj 100", "State 120", "Traj 120", "State 140", "Traj 140" ]
#
#sliced_conf = []
#sliced_string = []
#i=0
#while i < len(datastring):
#    sliced_conf.append(conf_number[i])
#    sliced_string.append(datastring[i])
#    i +=2
#
#print(sliced_conf)



#fig = plt.figure(figsize =(10, 7))
#ax = fig.add_subplot(111)
#bp = ax.boxplot(conf_number)
#plt.title("Average flight duration")
#ax.set_ylabel("time in seconds")
#ax.set_xticklabels(datastring)
#plt.show()
#f= open(rf"bluesky\plugins\Thesis_stuff\output_second_run\{conflog_100_state[0]}")
#print(f.read())