from gurobipy import *
import matplotlib.pyplot as plt
import ReadUC
import time
import os
import json
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei']
start_time = time.time()


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
        self.StartCost = []  # Initial cost
        self.Alpha = []  # Parameter α
        self.Beta = []  # Parameter β
        self.Gamma = []  # Parameter γ
        self.Pmax = []  # Unit max power
        self.Pmin = []  # Unit min power
        self.MinTimeOff = []  # Minimum downtime
        self.MinTimeOn = []  # Minimum uptime
        self.T0 = []  # Time unit has been on/off before T0
        self.P0 = []  # Initial power state of each unit
        self.Pstart = []  # Start-up capability
        self.Pshut = []  # Shut-down capability
        self.u0 = []  # Initial status
        self.iframp = []  # Has ramping at start
        self.CostFlag = []  # Cost flag: 1 = has cost, 0 = no cost

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
            'StartCost': 'Initial cost',
            'Alpha': 'Parameter α',
            'Beta': 'Parameter β',
            'Gamma': 'Parameter γ',
            'Pmax': 'Unit max power',
            'Pmin': 'Unit min power',
            'MinTimeOff': 'Minimum downtime',
            'MinTimeOn': 'Minimum uptime',
            'T0': 'Time unit has been on/off before T0',
            'P0': 'Initial power state of each unit',
            'Pstart': 'Start-up capability',
            'Pshut': 'Shut-down capability',
            'u0': 'Initial status',
            'iframp': 'Has ramping at start',
            'CostFlag': 'Cost flag: 1 = has cost, 0 = no cost'
        }

        for attr, comment in attributes.items():
            print(f"{attr}: {getattr(self, attr)}  # {comment}")

    def perturb_next_load(self, load_list, delta=None, method="uniform", seed=None,
                          keep_first=True):
        if seed is not None:
            np.random.seed(seed)
        arr = np.asarray(load_list, dtype=float)
        n = len(arr)

        if keep_first:
            perturbed = np.zeros(n)
            perturbed[0] = arr[0]
            start_idx = 1
        else:
            perturbed = np.zeros(n)
            start_idx = 0

        if method == "uniform":
            noise = np.random.uniform(-delta, delta, size=n - start_idx)

        perturbed[start_idx:] = arr[start_idx:] * (1 + noise)
        # Ensure non-negative
        perturbed = np.clip(perturbed, 0, None)
        return perturbed


################### Save filenames ############################
data = []
gurobi_solve_data = {
    "data": None,
    "objective": None,
    "fitness": None,
    "gap_power_rate": None,
    "gap_price_rate": None,
    "solve_time": None
}

current_dir = os.path.dirname(os.path.abspath(__file__))
directory = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "DataSet", "Test_set"))
json_file_path_gurobi_solve_data = os.path.abspath(
    os.path.join(current_dir, "..", "..", "..", "DataSet", "Test_set",
                 "gurobi_solve_data_for_test.json"))

json_file_path_gurobi_second_period_solve_data = "gurobi_second_period_solve_data_for_test.json"

with open(json_file_path_gurobi_second_period_solve_data, 'w') as f:
    for entry in os.scandir(directory):
        if entry.name.endswith(".mod"):
            gurobi_solve_data["data"] = entry.name
            data.append(gurobi_solve_data.copy())
    json.dump(data, f, indent=5)

with open(json_file_path_gurobi_second_period_solve_data, "r", encoding="utf-8") as file:
    gurobi_second_period_solve_data = json.load(file)

with open(json_file_path_gurobi_solve_data, "r", encoding="utf-8") as file:
    gurobi_solve_data = json.load(file)

time_start = time.time()
for item in gurobi_second_period_solve_data:

    filename = item["data"]
    print('Model solving for ' + filename)
    filename = os.path.join(directory, filename)
    uc_data = UC_Data()
    uc_data = ReadUC.readUC(uc_data, filename)
    UCModel = Model("UC")
    Fc = 0
    runtime = []

    total_cost = 0
    power_list = []

    P_shed_t_new = []
    P_over_t_new = []

    # Initialize state
    u_prev = [uc_data.u0[i] for i in range(uc_data.N)]
    consecutive_on = [uc_data.T0[i] if u_prev[i] == 1 else 0 for i in range(uc_data.N)]
    consecutive_off = [uc_data.T0[i] if u_prev[i] == 0 else 0 for i in range(uc_data.N)]
    pit_prev = [uc_data.P0[i] for i in range(uc_data.N)]

    for i in range(uc_data.N):
        if uc_data.P0[i] != 0:
            pit_prev[i] = ((uc_data.P0[i] - uc_data.Pmin[i]) / (uc_data.Pmax[i] - uc_data.Pmin[i]))
        else:
            pit_prev[i] = 0

    uc_data.print_class_attributes()

    for i in range(uc_data.N):
        temp = uc_data.Pmax[i] - uc_data.Pmin[i]

        temp1 = uc_data.Pup[i] / (temp)
        temp2 = uc_data.Pdown[i] / (temp)
        temp3 = (uc_data.Pstart[i] - uc_data.Pmin[i]) / (temp)
        temp4 = (uc_data.Pshut[i] - uc_data.Pmin[i]) / (temp)

        if uc_data.P0[i] != 0:
            temp5 = (uc_data.P0[i] - uc_data.Pmin[i]) / (temp)
            uc_data.P0[i] = temp5
        else:
            uc_data.P0[i] = 0

        uc_data.Pup[i] = temp1
        uc_data.Pdown[i] = temp2
        uc_data.Pstart[i] = temp3
        uc_data.Pshut[i] = temp4

    uc_data.print_class_attributes()

    Uit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]
    Sit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]
    Pit = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]
    Sit_wanwan = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]

    M = 10000
    P_shed = [0 for j in range(uc_data.T)]
    P_over = [0 for j in range(uc_data.T)]

    for i in range(uc_data.T):
        P_shed[i] = UCModel.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                   name=f"P_shed")  # Load shedding slack variable
        P_over[i] = UCModel.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                   name=f"P_over")  # Over-generation slack variable

    ## Load forecast
    perturb_next_load = uc_data.perturb_next_load(uc_data.PD, delta=0.1, method="uniform", seed=3,
                                                  keep_first=True)
    print(perturb_next_load)

    for count in range(24):
        step = 2
        if count == 23:
            step = 1

        print(f"########Period {count + 1}")

        for j in range(count, count + step):  # Objective function
            for i in range(uc_data.N):
                Uit[i][j] = UCModel.addVar(vtype=GRB.BINARY)
                Sit[i][j] = UCModel.addVar(vtype=GRB.BINARY)
                Pit[i][j] = UCModel.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS)
                Sit_wanwan[i][j] = UCModel.addVar(vtype=GRB.CONTINUOUS)
                Fc = Fc + Uit[i][j] * (
                            uc_data.Alpha[i] + uc_data.Beta[i] * uc_data.Pmin[i] + uc_data.Gamma[
                        i] * (uc_data.Pmin[i] ** 2)) + (uc_data.Pmax[i] - uc_data.Pmin[i]) * \
                     Pit[i][j] * (uc_data.Beta[i] + 2 * uc_data.Gamma[i] * uc_data.Pmin[i]) + (
                                 Pit[i][j] ** 2) * uc_data.Gamma[i] * \
                     ((uc_data.Pmax[i] - uc_data.Pmin[i]) ** 2) + Sit[i][j] * uc_data.CostHot[i] + \
                     Sit_wanwan[i][j]

        for i in range(count, count + step):
            Fc = Fc + M * P_shed[i] + M * P_over[i]

        UCModel.setObjective(Fc, GRB.MINIMIZE)

        ########################################################################
        ### Two-stage start-up constraints reconstruction
        for i in range(uc_data.N):  # Start-up constraints between periods
            UCModel.addConstr(Sit[i][count] >= Uit[i][count] - u_prev[i])

            if count != 23:
                UCModel.addConstr(
                    Sit[i][count + step - 1] >= Uit[i][count + step - 1] - Uit[i][count])

        ########################################################################

        finit_it = [[0 for j in range(uc_data.T)] for i in range(uc_data.N)]

        for i in range(uc_data.N):
            for j in range(count, count + step):
                if (j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i]) <= 0 and max(0, -uc_data.T0[
                    i]) < abs(j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i]) + 1:  # finit = 1
                    finit_it[i][j] = 1
                else:  # finit = 0
                    finit_it[i][j] = 0

        for i in range(uc_data.N):
            for j in range(count, count + step):
                tao = max(1, j - uc_data.MinTimeOff[i] - uc_data.TimeCold[i])
                temp1 = 0
                if j >= 2:
                    for k in range(int(tao), j - 1):
                        temp1 += Uit[i][k]
                UCModel.addConstr(Sit_wanwan[i][j] >= (uc_data.CostCold[i] - uc_data.CostHot[i]) * (
                            Sit[i][j] - temp1 - finit_it[i][j]))
                UCModel.addConstr(Pit[i][j] >= 0)  # Projected Pit constraint
                UCModel.addConstr(Uit[i][j] >= Pit[i][j])

        for j in range(count, count + step):
            temp2 = 0
            for k in range(uc_data.N):
                temp2 += Pit[k][j] * (uc_data.Pmax[k] - uc_data.Pmin[k]) + Uit[k][j] * uc_data.Pmin[
                    k]

            if j == count:  # Load forecast
                UCModel.addConstr(temp2 + P_shed[j] == uc_data.PD[j] + P_over[j])
            if j == count + step - 1 and j != 23:
                UCModel.addConstr(temp2 + P_shed[j] == perturb_next_load[j] + P_over[j])

        ####################################################################################
        #### Two-stage ramping constraints reconstruction
        for i in range(uc_data.N):
            UCModel.addConstr(Pit[i][count] - pit_prev[i] <= (
                        Uit[i][count] * uc_data.Pup[i] + Sit[i][count] * (
                            uc_data.Pstart[i] - uc_data.Pup[i])))
            UCModel.addConstr(pit_prev[i] - Pit[i][count] <= (
                        u_prev[i] * uc_data.Pshut[i] + (Sit[i][count] - Uit[i][count]) * (
                            uc_data.Pshut[i] - uc_data.Pdown[i])))

            # Second window ramping constraints
            if count != 23:
                UCModel.addConstr(Pit[i][count + step - 1] - Pit[i][count] <= (
                            Uit[i][count + step - 1] * uc_data.Pup[i] + Sit[i][count + step - 1] * (
                                uc_data.Pstart[i] - uc_data.Pup[i])))
                UCModel.addConstr(Pit[i][count] - Pit[i][count + step - 1] <= (
                            Uit[i][count] * uc_data.Pshut[i] + (
                                Sit[i][count + step - 1] - Uit[i][count + step - 1]) * (
                                        uc_data.Pshut[i] - uc_data.Pdown[i])))
        ####################################################################################
        ## Two-stage UC scheduling constraints reconstruction
        for i in range(uc_data.N):
            # Minimum on/off time constraints
            if u_prev[i] == 1 and consecutive_on[i] < uc_data.MinTimeOn[i]:  # First window
                UCModel.addConstr(Uit[i][count] == 1, f"must_on_{i}_{count}")

                if consecutive_on[i] + 1 < uc_data.MinTimeOn[i]:
                    UCModel.addConstr(Uit[i][count + step - 1] == 1, f"must_on_{i}_{count + 1}")


            elif u_prev[i] == 0 and abs(consecutive_off[i]) < uc_data.MinTimeOff[i]:

                UCModel.addConstr(Uit[i][count] == 0, f"must_off_{i}_{count}")
                if consecutive_off[i] + 1 < uc_data.MinTimeOff[i]:
                    UCModel.addConstr(Uit[i][count + step - 1] == 0, f"must_on_{i}_{count + 1}")

        ####################################################################################

        UCModel.optimize()

        if UCModel.Status == GRB.OPTIMAL:  # Save results and update state

            for i in range(uc_data.N):
                u_new = Uit[i][count].x
                pit_new = Pit[i][count].x
                p_new = u_new * uc_data.Pmin[i] + pit_new * (uc_data.Pmax[i] - uc_data.Pmin[i])

                # Update state: update T0, U0, P0, only update first window
                if u_new == 1:
                    consecutive_on[i] = consecutive_on[i] + 1 if u_prev[i] == 1 else 1
                    consecutive_off[i] = 0
                else:
                    consecutive_off[i] = consecutive_off[i] - 1 if u_prev[i] == 0 else -1
                    consecutive_on[i] = 0

                u_prev[i] = u_new
                pit_prev[i] = pit_new

                power_list.append(p_new)

            previous_cost = 0
            for i in range(uc_data.N):
                previous_cost += Uit[i][count].x * (
                        uc_data.Alpha[i] + uc_data.Beta[i] * uc_data.Pmin[i] + uc_data.Gamma[i] * (
                        uc_data.Pmin[i] ** 2)) + (uc_data.Pmax[i] - uc_data.Pmin[i]) * \
                                 Pit[i][count].x * (
                                             uc_data.Beta[i] + 2 * uc_data.Gamma[i] * uc_data.Pmin[
                                         i]) + (
                                         Pit[i][count].x ** 2) * uc_data.Gamma[i] * \
                                 ((uc_data.Pmax[i] - uc_data.Pmin[i]) ** 2) + Sit[i][count].x * \
                                 uc_data.CostHot[i] + \
                                 Sit_wanwan[i][count].x

            total_cost += previous_cost

            P_shed_t_new.append(P_shed[count].x)
            P_over_t_new.append(P_over[count].x)
            runtime.append(UCModel.Runtime)

    # Save data
    item["objective"] = total_cost
    for temp in gurobi_solve_data:
        if temp["data"] == item["data"]:
            item["gap_price_rate"] = abs(total_cost - temp["objective"]) / temp["objective"]
    item["gap_power_rate"] = (sum(P_shed_t_new) + sum(P_over_t_new)) / sum(uc_data.PD)
    item["solve_time"] = sum(runtime)
    item["fitness"] = 0.5 * item["gap_price_rate"] + 0.5 * item["gap_power_rate"]

time_end = time.time()
print("Time used:", time_end - time_start)

print(gurobi_second_period_solve_data)

with open(json_file_path_gurobi_second_period_solve_data, "w", encoding="utf-8") as file:
    json.dump(gurobi_second_period_solve_data, file, indent=5)
