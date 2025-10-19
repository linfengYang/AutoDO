import json
import os
import time

from gurobipy import *
import matplotlib.pyplot as plt
import ReadUC
import gurobipy as gp
from gurobipy import GRB
plt.rcParams['font.sans-serif'] = ['SimHei']


time_start = time.time()


class UC_Data:
    def __init__(self):
        self.T = 0  # Number of time periods
        self.N = 0  # Number of units
        self.PD = []  # Load
        self.Spin = []  # Spinning reserve
        self.Pup = []  # Ramp-up constraint
        self.Pdown = []  # Ramp-down constraint
        self.TimeCold = []  # Cold start time
        self.CostCold = []  # Cold start cost
        self.CostHot = []  # Hot start cost
        self.StartCost = []  # Startup cost
        self.Alpha = []  # Parameter α
        self.Beta = []  # Parameter β
        self.Gamma = []  # Parameter γ
        self.Pmax = []  # Maximum generation power
        self.Pmin = []  # Minimum generation power
        self.MinTimeOff = []  # Minimum downtime
        self.MinTimeOn = []  # Minimum uptime
        self.T0 = []  # Time the unit has been on/off before t0
        self.P0 = []  # Initial power state of each unit
        self.Pstart = []  # Startup capability
        self.Pshut = []  # Shutdown capability
        self.u0 = []  # Initial on/off state
        self.iframp = []  # Whether the unit has startup ramping
        self.CostFlag = []  # Cost flag (1: has cost, 0: no cost)

    def print_class_attributes(self):
        """
        Print all class attributes with their descriptions.
        """
        attributes = {
            'T': 'Number of time periods',
            'N': 'Number of units',
            'PD': 'Load',
            'Spin': 'Spinning reserve',
            'Pup': 'Ramp-up constraint',
            'Pdown': 'Ramp-down constraint',
            'TimeCold': 'Cold start time',
            'CostCold': 'Cold start cost',
            'CostHot': 'Hot start cost',
            'StartCost': 'Startup cost',
            'Alpha': 'Parameter α',
            'Beta': 'Parameter β',
            'Gamma': 'Parameter γ',
            'Pmax': 'Maximum generation power',
            'Pmin': 'Minimum generation power',
            'MinTimeOff': 'Minimum downtime',
            'MinTimeOn': 'Minimum uptime',
            'T0': 'Time the unit has been on/off before t0',
            'P0': 'Initial power state of each unit',
            'Pstart': 'Startup capability',
            'Pshut': 'Shutdown capability',
            'u0': 'Initial on/off state',
            'iframp': 'Whether the unit has startup ramping',
            'CostFlag': 'Cost flag (1: has cost, 0: no cost)'
        }

        for attr, comment in attributes.items():
            print(f"{attr}: {getattr(self, attr)}  # {comment}")


################### Save file names ############################
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
directory = os.path.abspath(os.path.join(current_dir, "..", "..","..", "DataSet", "Test_set"))
json_file_path_gurobi_solve_data = os.path.abspath(os.path.join(current_dir, "..", "..","..", "DataSet", "Test_set", "gurobi_solve_data_for_test.json"))

json_file_path_gurobi_single_period_solve_data = "gurobi_single_period_solve_data_for_test.json"



with open(json_file_path_gurobi_single_period_solve_data, 'w') as f:
    for entry in os.scandir(directory):
        if entry.name.endswith(".mod"):
            gurobi_solve_data["data"] = entry.name
            data.append(gurobi_solve_data.copy())
    json.dump(data, f, indent=5)

with open(json_file_path_gurobi_single_period_solve_data, "r", encoding="utf-8") as file:
    gurobi_single_period_solve_data = json.load(file)

with open(json_file_path_gurobi_solve_data, "r", encoding="utf-8") as file:
    gurobi_solve_data = json.load(file)
#########################################################


# Iterate through each dataset and solve
for item in gurobi_single_period_solve_data:


    filename = item["data"]
    print('Model solving for '+filename)
    filename = os.path.join(directory, filename)
    uc_data = UC_Data()
    uc_data = ReadUC.readUC(uc_data,filename)
    UCModel = Model("UC")
    Fc = 0
    runtime = []


    print("initial time")
    uc_data.print_class_attributes()



    u_prev = [uc_data.u0[i] for i in range(uc_data.N)]
    consecutive_on = [uc_data.T0[i] if u_prev[i] == 1 else 0 for i in range(uc_data.N)]
    consecutive_off = [uc_data.T0[i] if u_prev[i] == 0 else 0 for i in range(uc_data.N)]
    pit_prev = [uc_data.P0[i] for i in range(uc_data.N)]

    for i in range(uc_data.N):              # Projection
        if uc_data.P0[i] != 0:
            pit_prev[i] = ((uc_data.P0[i] - uc_data.Pmin[i]) / (uc_data.Pmax[i] - uc_data.Pmin[i]))
        else:
            pit_prev[i] = 0

    print("-------------------------------")
    print(u_prev)
    print(consecutive_on)
    print(consecutive_off)
    print(pit_prev)
    print("-------------------------------")



    for i in range (uc_data.N):
        temp = uc_data.Pmax[i] - uc_data.Pmin[i]
        temp1 = uc_data.Pup[i] / (temp)
        temp2 = uc_data.Pdown[i] / (temp)
        temp3 = (uc_data.Pstart[i] - uc_data.Pmin[i]) / (temp)
        temp4 = (uc_data.Pshut[i] - uc_data.Pmin[i]) / (temp)

        uc_data.Pup[i] = temp1
        uc_data.Pdown[i] = temp2
        uc_data.Pstart[i] = temp3
        uc_data.Pshut[i] = temp4


    print("initial time modify")
    uc_data.print_class_attributes()


    results = []
    optimality_gap = []
    P_shed = []
    P_over = []
    total_cost = 0
    previous_cost = 0
    M = 10000         # Penalty coefficient for load shedding


    t = 0
    for t in range(uc_data.T):
        UCModel = gp.Model(f"UC_Single_Period_{t}")            # Create model



        # Define variables
        Uit = [UCModel.addVar(vtype=GRB.BINARY, name=f"u_{i}_{t}") for i in range(uc_data.N)]
        Sit = [UCModel.addVar(vtype=GRB.BINARY, name=f"s_{i}_{t}") for i in range(uc_data.N)]
        Pit = [UCModel.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=f"p_{i}_{t}") for i in range(uc_data.N)]
        P_shed_t = UCModel.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"P_shed_{t}")    # Load shedding slack variable
        P_over_t = UCModel.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"P_over_{t}")  # Overgeneration slack variable

        # Power balance constraint
        UCModel.addConstr(
            sum(Uit[i] * uc_data.Pmin[i] + Pit[i] * (uc_data.Pmax[i] - uc_data.Pmin[i]) for i in range(uc_data.N)) + P_shed_t ==uc_data.PD[t] + P_over_t, "demand"
        )


        for i in range(uc_data.N):
            # Minimum up/down time constraints
            if u_prev[i] == 1 and consecutive_on[i] < uc_data.MinTimeOn[i]:
                UCModel.addConstr(Uit[i] == 1, f"must_on_{i}_{t}")
            elif u_prev[i] == 0 and abs(consecutive_off[i]) < uc_data.MinTimeOff[i]:
                UCModel.addConstr(Uit[i] == 0, f"must_off_{i}_{t}")

            # Startup constraints
            UCModel.addConstr(Sit[i] >= Uit[i] - u_prev[i], f"startup_{i}_{t}")

            # Power output constraints
            UCModel.addConstr(Pit[i] >= 0, f"pit_min_{i}_{t}")
            UCModel.addConstr(Uit[i] >= Pit[i], f"pit_link_{i}_{t}")


            UCModel.addConstr(
                Pit[i] - pit_prev[i] <= (Uit[i] * uc_data.Pup[i] + Sit[i] * (uc_data.Pstart[i] - uc_data.Pup[i])),
                f"ramp_up_{i}_{t}"
            )
            UCModel.addConstr(
                pit_prev[i] - Pit[i] <= (u_prev[i] * uc_data.Pshut[i] + (Sit[i] - Uit[i]) * (
                            uc_data.Pshut[i] - uc_data.Pdown[i])),
                f"ramp_down_{i}_{t}"
            )



        # Objective function
        Fc = 0
        for i in range(uc_data.N):

            fuel_cost = (
                    Uit[i] * (
                        uc_data.Alpha[i] + uc_data.Beta[i] * uc_data.Pmin[i] + uc_data.Gamma[i] * (uc_data.Pmin[i] ** 2)) +
                    (uc_data.Pmax[i] - uc_data.Pmin[i]) * Pit[i] * (
                                uc_data.Beta[i] + 2 * uc_data.Gamma[i] * uc_data.Pmin[i]) +
                    (Pit[i] ** 2) * uc_data.Gamma[i] * ((uc_data.Pmax[i] - uc_data.Pmin[i]) ** 2)
            )

            startup_cost = 0
            if u_prev[i] == 0:
                startup_cost = uc_data.CostCold[i] if abs(consecutive_off[i]) > (uc_data.TimeCold[i] + uc_data.MinTimeOff[i]) else uc_data.CostHot[i]
            Fc += fuel_cost + Sit[i] * startup_cost

        Fc += M * P_shed_t + M * P_over_t              # Load shedding penalty
        UCModel.setObjective(Fc, GRB.MINIMIZE)

        # Solve
        UCModel.optimize()

        period_result = {
            't': t,
            'status': UCModel.status,
            'objective': UCModel.objVal if UCModel.status == GRB.OPTIMAL else None,
            'u': [],
            'p': [],
            's': []
        }

        if UCModel.Status == GRB.OPTIMAL:            # Save results and update state


            for i in range(uc_data.N):
                u_new = Uit[i].x
                pit_new = Pit[i].x
                p_new = u_new * uc_data.Pmin[i] + pit_new * (uc_data.Pmax[i] - uc_data.Pmin[i])
                s_new = Sit[i].x


                period_result['u'].append(u_new)
                period_result['p'].append(p_new)
                period_result['s'].append(s_new)

                # Update state
                if u_new == 1:
                    consecutive_on[i] = consecutive_on[i] + 1 if u_prev[i] == 1 else 1
                    consecutive_off[i] = 0
                else:
                    consecutive_off[i] = consecutive_off[i] - 1 if u_prev[i] == 0 else -1
                    consecutive_on[i] = 0

                u_prev[i] = u_new
                pit_prev[i] = pit_new

            runtime.append(UCModel.Runtime)
            P_shed_t_new = P_shed_t.x
            P_over_t_new = P_over_t.x
            P_shed.append(P_shed_t_new)
            P_over.append(P_over_t_new)
            results.append(period_result)
            previous_cost = UCModel.objVal - M * P_shed_t_new - M * P_over_t_new
            total_cost += UCModel.objVal - M * P_shed_t_new - M * P_over_t_new

            print(u_prev)
            print(consecutive_on)
            print(consecutive_off)
            print(pit_prev)
            print(P_shed_t_new)
            print(P_over_t_new)



        else:                       # No feasible solution found, skip to next period. Theoretically this should not happen.
            for i in range(uc_data.N):
                p_new = u_prev[i] * uc_data.Pmin[i] + pit_prev[i] * (uc_data.Pmax[i] - uc_data.Pmin[i])             # For plotting
                period_result['p'].append(p_new)
            period_result['u'].append(u_prev)
            results.append(period_result)
            optimality_gap.append(UCModel.MIPGap)
            total_cost += previous_cost


            # Update state
            for i in range(uc_data.N):
                if u_prev[i] == 1:
                    consecutive_on[i] = consecutive_on[i] + 1
                else:
                    consecutive_off[i] = consecutive_off[i] - 1

            print(u_prev)
            print(consecutive_on)
            print(consecutive_off)
            print(pit_prev)
            print('Model not solved to optimality')




    # Save results
    item["objective"] = total_cost
    for temp in gurobi_solve_data:
        if temp["data"] == item["data"]:
            item["gap_price_rate"] = abs(total_cost - temp["objective"]) / temp["objective"]
    item["gap_power_rate"] = (sum(P_shed) + sum(P_over)) / sum(uc_data.PD)
    item["solve_time"] = sum(runtime)
    item["fitness"] = 0.5 * item["gap_price_rate"] + 0.5 * item["gap_power_rate"]

time_end = time.time()
print("Time used:", time_end - time_start)

with open(json_file_path_gurobi_single_period_solve_data, "w", encoding="utf-8") as file:
    json.dump(gurobi_single_period_solve_data, file, indent=5)
