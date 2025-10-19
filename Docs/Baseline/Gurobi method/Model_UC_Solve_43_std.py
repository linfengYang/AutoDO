import json
import os
import time
from gurobipy import *
import matplotlib.pyplot as plt
import ReadUC
plt.rcParams['font.sans-serif'] = ['SimHei']

class UC_Data:
    def __init__(self):
        self.T = 0  # Number of periods
        self.N = 0  # Number of units
        self.PD = []  # Load
        self.Spin = []  # Reserve load
        self.Pup = []  # Ramp-up constraint
        self.Pdown = []  # Ramp-down constraint
        self.TimeCold = []  # Cold start time
        self.CostCold = []  # Cold start cost
        self.CostHot = []  # Hot start cost
        self.StartCost = []  # Startup cost
        self.Alpha = []  # Parameter α
        self.Beta = []  # Parameter β
        self.Gamma = []  # Parameter γ
        self.Pmax = []  # Unit power upper limit
        self.Pmin = []  # Unit power lower limit
        self.MinTimeOff = []  # Minimum downtime
        self.MinTimeOn = []  # Minimum uptime
        self.T0 = []  # Time on/off before T0
        self.P0 = []  # Initial power state of each unit
        self.Pstart = []  # Startup capability
        self.Pshut = []  # Shutdown capability
        self.u0 = []  # Initial state
        self.iframp = []  # Whether ramping constraint is enabled
        self.CostFlag = []  # Cost flag 1: has cost 0: no cost

    def print_class_attributes(self):
        attributes = {
            'T': 'Number of periods',
            'N': 'Number of units',
            'PD': 'Load',
            'Spin': 'Reserve load',
            'Pup': 'Ramp-up constraint',
            'Pdown': 'Ramp-down constraint',
            'TimeCold': 'Cold start time',
            'CostCold': 'Cold start cost',
            'CostHot': 'Hot start cost',
            'StartCost': 'Startup cost',
            'Alpha': 'Parameter α',
            'Beta': 'Parameter β',
            'Gamma': 'Parameter γ',
            'Pmax': 'Unit power upper limit',
            'Pmin': 'Unit power lower limit',
            'MinTimeOff': 'Minimum downtime',
            'MinTimeOn': 'Minimum uptime',
            'T0': 'Time on/off before T0',
            'P0': 'Initial power state of each unit',
            'Pstart': 'Startup capability',
            'Pshut': 'Shutdown capability',
            'u0': 'Initial state',
            'iframp': 'Whether ramping constraint is enabled',
            'CostFlag': 'Cost flag 1: has cost 0: no cost'
        }

        for attr, comment in attributes.items():
            print(f"{attr}: {getattr(self, attr)}  # {comment}")


count = 0
start_time = time.time()
################### Save file name ############################
data = []
gurobi_solve_data = {
    "data": None,
    "objective": None,
    "gap": None,
    "solve_time": None
}

current_dir = os.path.dirname(os.path.abspath(__file__))
directory = os.path.abspath(os.path.join(current_dir, "..", "..","..", "DataSet", "Test_set"))
json_file_path = "gurobi_solve_data_total.json"

with open(json_file_path, 'w') as f:
    for entry in os.scandir(directory):
        if entry.name.endswith(".mod"):
            gurobi_solve_data["data"] = entry.name
            data.append(gurobi_solve_data.copy())
    json.dump(data, f, indent=5)

with open(json_file_path, "r", encoding="utf-8") as file:
    data_list = json.load(file)
#########################################################

data = []
# Iterate through each dataset and solve
for item in data_list:
    filename = item["data"]
    print('Model solving for ' + filename)
    filename = os.path.join(directory, filename)
    uc_data = UC_Data()
    uc_data = ReadUC.readUC(uc_data, filename)
    UCModel = Model("UC")
    Fc = 0

    UCModel.setParam("TimeLimit", 3600)         # Set time limit to 3600 seconds
    UCModel.setParam('MIPGap', 0.0001)

    # uc_data.print_class_attributes()

    for i in range(uc_data.N):
        temp = uc_data.Pmax[i] - uc_data.Pmin[i]

        temp1 = uc_data.Pup[i] / (temp)
        temp2 = uc_data.Pdown[i] / (temp)
        temp3 = (uc_data.Pstart[i] - uc_data.Pmin[i]) / (temp)
        temp4 = (uc_data.Pshut[i] - uc_data.Pmin[i]) / (temp)

        if uc_data.P0[i] != 0:                                     # Patch
            temp5 = (uc_data.P0[i] - uc_data.Pmin[i]) / (temp)
            uc_data.P0[i] = temp5
        else:
            uc_data.P0[i] = 0

        uc_data.Pup[i] = temp1
        uc_data.Pdown[i] = temp2
        uc_data.Pstart[i] = temp3
        uc_data.Pshut[i] = temp4

    # uc_data.print_class_attributes()

    Uit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]
    Sit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]
    Pit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]   # unitPower == pit
    Sit_wanwan = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]

    for i in range(uc_data.N):                                         # Objective function
        for j in range(uc_data.T):
            Uit[i][j] = UCModel.addVar(vtype=GRB.BINARY)
            Sit[i][j] = UCModel.addVar(vtype=GRB.BINARY)
            Pit[i][j] = UCModel.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS)
            Sit_wanwan[i][j] = UCModel.addVar(vtype=GRB.CONTINUOUS)
            Fc = Fc + Uit[i][j]*(uc_data.Alpha[i]+uc_data.Beta[i]*uc_data.Pmin[i]+uc_data.Gamma[i]*(uc_data.Pmin[i]**2))+(uc_data.Pmax[i]-uc_data.Pmin[i])*  \
               Pit[i][j]*(uc_data.Beta[i]+2*uc_data.Gamma[i]*uc_data.Pmin[i])+(Pit[i][j]**2)*uc_data.Gamma[i]* \
               ((uc_data.Pmax[i]-uc_data.Pmin[i])**2)+Sit[i][j]*uc_data.CostHot[i] + Sit_wanwan[i][j]

    UCModel.setObjective(Fc, GRB.MINIMIZE)

    for i in range(uc_data.N):                                         # On/off transition constraint
        for j in range(uc_data.T):
            if j == 0:
                UCModel.addConstr(Sit[i][j] >= Uit[i][j] - uc_data.u0[i])            # Patch
            if j > 0:
                UCModel.addConstr(Sit[i][j] >= Uit[i][j] - Uit[i][j-1])

    finit_it = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]

    for i in range(uc_data.N):
        for j in range(uc_data.T):
            if (j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i]) <= 0 and max(0, -uc_data.T0[i]) < abs(j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i]) + 1:
                finit_it[i][j] = 1
            else:
                finit_it[i][j] = 0

    for i in range(uc_data.N):                                         #36
        for j in range(uc_data.T):
            tao = max(1, j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i])
            temp1 = 0
            if j >= 2:
                for k in range(int(tao), j-1):
                    temp1 += Uit[i][k]
            UCModel.addConstr(Sit_wanwan[i][j] >= (uc_data.CostCold[i] - uc_data.CostHot[i])*(Sit[i][j] - temp1 - finit_it[i][j]))
            UCModel.addConstr(Pit[i][j] >= 0)                           #P_wanwan projection constraint
            UCModel.addConstr(Uit[i][j] >= Pit[i][j])

    for j in range(uc_data.T):
        temp2 = 0
        for k in range(uc_data.N):
            temp2 += Pit[k][j]*(uc_data.Pmax[k]-uc_data.Pmin[k]) + Uit[k][j]*uc_data.Pmin[k]
        UCModel.addConstr(temp2 == uc_data.PD[j])                         #Power balance constraint

    # for i in range(uc_data.N):
    #     temp3 = 0                                        #Spinning reserve constraint
    #     for j in range(uc_data.T):
    #         temp3 = 0
    #         for k in range(uc_data.N):
    #             temp3 += Uit[k][j] * uc_data.Pmax[k]
    #         UCModel.addConstr(temp3 >= uc_data.PD[j] + uc_data.Spin[j])

    for i in range(uc_data.N):                                         #31-32 Ramp constraints
        for j in range(uc_data.T):
            if j == 0:
               UCModel.addConstr(Pit[i][j] - uc_data.P0[i] <= (Uit[i][j] * uc_data.Pup[i] + Sit[i][j] * (uc_data.Pstart[i] - uc_data.Pup[i])))     # Patch
               UCModel.addConstr(uc_data.P0[i] - Pit[i][j] <= (uc_data.u0[i] * uc_data.Pshut[i] + (Sit[i][j] - Uit[i][j]) * (uc_data.Pshut[i] - uc_data.Pdown[i])))   # Patch
            if j > 0:
               UCModel.addConstr(Pit[i][j] - Pit[i][j-1] <= (Uit[i][j]* uc_data.Pup[i] + Sit[i][j]*(uc_data.Pstart[i] - uc_data.Pup[i])))
               UCModel.addConstr(Pit[i][j-1] - Pit[i][j] <= (Uit[i][j-1]* uc_data.Pshut[i] + (Sit[i][j] - Uit[i][j])*(uc_data.Pshut[i] - uc_data.Pdown[i])))

    Li = [0 for j in range(uc_data.N)]
    Ui = [0 for j in range(uc_data.N)]

    for i in range(uc_data.N):
        Li[i] = max(0, min(uc_data.T, (1 - uc_data.u0[i]) * (uc_data.MinTimeOff[i] + uc_data.T0[i])))  # Thermal unit must remain off for at least this time
        Ui[i] = max(0, min(uc_data.T, uc_data.u0[i] * (uc_data.MinTimeOn[i] - uc_data.T0[i])))          # Thermal unit must remain on for at least this time

    for i in range(uc_data.N):                                         #13 Minimum uptime constraint
        for j in range(int(Ui[i]), uc_data.T):
            wanwan = (max(0, j - uc_data.MinTimeOn[i]) + 1)
            temp4 = 0
            for k in range(int(wanwan), j):
                temp4 += Sit[i][k]
            UCModel.addConstr(temp4 <= Uit[i][j])

    for i in range(uc_data.N):                                         #33
        for j in range(int(Li[i]), uc_data.T):
            wanwan = (max(0, j - uc_data.MinTimeOff[i]) + 1)
            lt = int(max(0, j - uc_data.MinTimeOn[i]))
            temp5 = 0
            for k in range(int(wanwan), j):
                temp5 += Sit[i][k]
            UCModel.addConstr(temp5 <= (1 - Uit[i][lt]))

    for i in range(uc_data.N):                                         #10
        for j in range(int(Ui[i] + Li[i])):
            UCModel.addConstr(Uit[i][j] == uc_data.u0[i])

    UCModel.optimize()

    if UCModel.Status == GRB.OPTIMAL:
        print('-----------------------Model solved to optimality' + filename)
        item["objective"] = UCModel.objVal
        item["gap"] = UCModel.MIPGap
        item["solve_time"] = UCModel.Runtime
        data.append(item)
    elif UCModel.status == GRB.TIME_LIMIT:
        if UCModel.SolCount > 0:
            print('-----------------------Time limit ' + filename)
            item["objective"] = UCModel.objVal
            item["gap"] = UCModel.MIPGap
            item["solve_time"] = UCModel.Runtime
            data.append(item)
    else:
        print('-----------------------Model is infeasible' + filename)
        data.append(item)

    temp_path = "gurobi_solve_data_" + item["data"] + ".json"
    with open(temp_path, 'w') as f:
        json.dump(item, f, indent=5)

with open(json_file_path, 'w') as f:
    json.dump(data, f, indent=5)

end_time = time.time()
print("Running time:", end_time - start_time)
