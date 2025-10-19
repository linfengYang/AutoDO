import json
import sys
import types
import re
import warnings
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from joblib import Parallel, delayed
from Rolling_UC import Read_UC

class UC_Data_dict:
    def __init__(self):
        self.N = None
        self.T = None
        self.PD = None
        self.invalid_data = []
        self.invalid_times = 0
        self.gap_power = 0
        self.plt_data = []
        # self.price_data = 0
        self.total_cost = 0
        self.units_info = []
        self.filename = None
        self.objective = 0


    def transform_to_dictionary(self, uc_data, filename, objective):
        self.filename = filename
        self.objective = objective
        self.N = uc_data.N
        self.T = uc_data.T
        self.PD = uc_data.PD
        for i in range(uc_data.N):
            self.units_info.append({
                          "a_i":uc_data.Alpha[i],
                           "b_i":uc_data.Beta[i] ,
                           "c_i":uc_data.Gamma[i],
                           "u_i": 0,
                           "p_i": 0,
                           "p_max_i": uc_data.Pmax[i],
                           "p_min_i": uc_data.Pmin[i],
                            "p_up_i": uc_data.Pup[i],
                            "p_down_i": uc_data.Pdown[i],
                            "p_start_i": uc_data.Pstart[i],
                            "p_shut_i": uc_data.Pshut[i],
                           "s_i": uc_data.CostHot[i],
                           "p_i_0": uc_data.P0[i],          #Information to be updated
                           "u_i_0": uc_data.u0[i],          #Information to be updated
                           "t_on_min_i": uc_data.MinTimeOn[i],
                           "t_off_min_i": uc_data.MinTimeOff[i],
                           "t_i_0": uc_data.T0[i],          #Information to be updated

                           })


    def show_units_info(self):
        for i in self.units_info:
            print(i)


    def hard_constraint_check(self, schedules, period):
        pass
        #This part of the code will be released after the paper is accepted.


############################
##########update########
############################
    def update(self, schedules, load):
        for i in range(len(self.units_info)):
            if schedules[0, i] == 0 and self.units_info[i]['u_i_0'] == 0:    #Keep shut down
                self.units_info[i]['t_i_0'] -= 1
                self.units_info[i]['u_i_0'] = schedules[0, i]
                self.units_info[i]['p_i_0'] = schedules[1, i]
                continue
            elif schedules[0, i] == 1 and self.units_info[i]['u_i_0'] == 1:     #Keep powered on
                self.units_info[i]['t_i_0'] += 1
                self.units_info[i]['u_i_0'] = schedules[0, i]
                self.units_info[i]['p_i_0'] = schedules[1, i]
                self.total_cost += self.units_info[i]['a_i'] * 1 + self.units_info[i]['b_i'] * self.units_info[i]['p_i_0'] + self.units_info[i]['c_i'] * (self.units_info[i]['p_i_0'] ** 2)
                continue
            elif schedules[0, i] == 0 and self.units_info[i]['u_i_0'] == 1:     #shut down
                self.units_info[i]['t_i_0'] = -1
                self.units_info[i]['u_i_0'] = schedules[0, i]
                self.units_info[i]['p_i_0'] = schedules[1, i]
            else:                                                               #powered on
                self.units_info[i]['t_i_0'] = 1
                self.units_info[i]['u_i_0'] = schedules[0, i]
                self.units_info[i]['p_i_0'] = schedules[1, i]
                self.total_cost += self.units_info[i]['a_i'] * 1 + self.units_info[i]['b_i'] * self.units_info[i]['p_i_0'] + self.units_info[i]['c_i'] * (self.units_info[i]['p_i_0'] ** 2) +self.units_info[i]['s_i']

        self.gap_power += abs(sum(schedules[1]) - load)
        self.plt_data.append(schedules[1])

############################
##########evaluate########
############################
    def evaluate(self, code, name):
        try:
            # Suppress warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                heuristic_module = types.ModuleType("heuristic_module")
                exec(code, heuristic_module.__dict__)
                sys.modules[heuristic_module.__name__] = heuristic_module

                load = []
                for i in range(self.T):
                    load.append(self.PD[i])

                print(f"Current data:{self.filename}")
                time_start = time.time()



                ###################  #Perturbed data
                perturb_next_load = self.perturb_next_load(load, delta=0.1, method="uniform", seed=2, keep_first=True)
                ####################



                for i in range(self.T):
                    if i + 1 < len(load):
                        load_current = load[i:i + 2]
                        # load_current = [load[i], perturbnextload[i+1]]               #Simulated load forecast
                    else:
                        load_current = load[i:] + [0]

                    schedules =getattr(heuristic_module, name)(self.units_info, load_current)  #Scheduling


                    self.hard_constraint_check(schedules, i)  #Violation of hard constraints
                    self.update(schedules, load[i])  #Update status (update cost, update load deviation)
                time_end = time.time()
                time_cost = time_end - time_start



                print(f"Number of hard constraint violations:{self.invalid_times}")

                if self.invalid_times > 0:
                    return None

                total = 0
                for i in range(self.T):
                    total += self.PD[i]

                real_power = [sum(sublist) for sublist in self.plt_data]
                gap_power = [abs(real_power[i] - load[i]) for i in range(self.T)]
                gap_power_rate = sum(gap_power) / total
                gap_price_rate = (abs(self.total_cost - self.objective) / self.objective)
                fitness = 0.5 * gap_power_rate + 0.5 * gap_price_rate



                return [fitness, gap_power_rate, gap_price_rate]


        except Exception as e:
            print("Error:", str(e))
            return None

############################
##########Perturbed data####
############################

    def perturb_next_load(self, load_list, delta=0, method="uniform", seed=None, keep_first=True):

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
        perturbed = np.clip(perturbed, 0, None)
        return perturbed


############################
##########Heuristic evaluation program########
############################
def evaluate_Manger(name = None,algorithm = None,code = None,operator = None):
    print("Evaluating the heuristic...")

    json_file_path = '../DataSet/Development set/gurobi_solve_data_for_training.json'  #Path to the development set
    with open(json_file_path, "r", encoding="utf-8") as file:
        training_set = json.load(file)

    # json_file_path = '../DataSet/Test_set/gurobi_solve_data_for_test.json'          #Path to the test set
    # with open(json_file_path, "r", encoding="utf-8") as file:
    #     training_set = json.load(file)


    objects = []
    for training_data in training_set:


        file_path = '../DataSet/Development set/' + training_data['data']              #Path to the developmentg set
        # file_path = '../DataSet/Test_set/' + training_data['data']                #Path to the test set

        uc_data = Read_UC.UC_Data()
        uc_data = Read_UC.readUC(uc_data, file_path)
        uc_data_dict = UC_Data_dict()
        uc_data_dict.transform_to_dictionary(uc_data, training_data['data'], training_data['objective'])
        objects.append(uc_data_dict)

    warnings.filterwarnings("ignore", category=UserWarning)
    # fitness = Parallel(n_jobs=len(objects), timeout=600)(delayed(obj.evaluate)(code, name) for obj in objects)

    try:
        fitness = Parallel(n_jobs=1, timeout=600)(delayed(obj.evaluate)(code, name) for obj in objects)
    except TimeoutError:
        print("Evaluation task timed out")
        fitness = [None, None, None]

    fitness_list = []
    gap_power_rate_list = []
    gap_price_rate_list = []

    if None in fitness:
        history = {
            "name": name,
            "algorithm": algorithm,
            "code": code,
            "from": operator,
            "gap_power_rate": None,
            "gap_price_rate": None,
            "fitness": None,
        }
        name = get_unique_function_name(name)
        filename = "./results/history/" + str(name) + ".json"
        with open(filename, 'w') as f:
            json.dump(history, f, indent=5)
        return None

    if None not in fitness:
        for temp in fitness:
            if temp is not None:
                fitness_list.append(temp[0])
                gap_power_rate_list.append(temp[1])
                gap_price_rate_list.append(temp[2])


        history = {
            "name": name,
            "algorithm": algorithm,
            "code": code,
            "from": operator,
            "gap_power_rate": np.mean(gap_power_rate_list),
            "gap_price_rate": np.mean(gap_price_rate_list),
            "fitness": np.mean(fitness_list),
        }


        name = get_unique_function_name(name)
        filename = "./results/history/" + str(name) + ".json"
        with open(filename, 'w') as f:
            json.dump(history, f, indent=5)


        return [np.mean(fitness_list),np.mean(gap_power_rate_list),np.mean(gap_price_rate_list)]

def get_unique_function_name(base_name):
    existing_names = {
        os.path.splitext(f)[0]
        for f in os.listdir("./results/history/")
        if f.endswith(".json")
    }


    if base_name not in existing_names:
        return base_name

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}"




