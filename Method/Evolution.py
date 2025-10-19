import heapq
import random
import os
import numpy as np
import json
from joblib import Parallel, delayed
from concurrent.futures import ProcessPoolExecutor, wait
import concurrent.futures
import time

from Method.LLM_Interface import Interface
from Rolling_UC.Prompts import GetPrompts
from Rolling_UC.Rolling_UC_Manger import UC_Data_dict
from Rolling_UC.Rolling_UC_Manger import evaluate_Manger
time_start = time.time()

from pebble import ProcessPool
from concurrent.futures import TimeoutError


class EC:
    def __init__(self):
        self.pop_size = 5
        self.n_gens = 5

        self.llm_api_endpoint = None
        self.llm_api_key = None
        self.llm_model = None
        self.temperature = 1.0

        self.exp_n_proc = 10
        self.exp_timeout = 10

        self.interface = None
        self.path = "./"
        self.prompts = GetPrompts()



    def show_paras(self):
        print("pop_size:", self.pop_size)
        print("n_gens:", self.n_gens)
        print("llm_api_endpoint:", self.llm_api_endpoint)
        print("llm_api_key:", self.llm_api_key)
        print("llm_model:", self.llm_model)
        print("exp_n_proc:", self.exp_n_proc)
        print("exp_timeout:", self.exp_timeout)
        print("interface:", self.interface)
        print("path:", self.path)

    def set_paras(self, **paras):
        for key, value in paras.items():
            if hasattr(self, key):
                setattr(self, key, value)
#######################################################Population management###########################################
    def management(self, populations,  heuristics = None, size = None, operator = None):
        # This part of the code will be released after the paper is accepted.
        return pop_new


    def selection(self, pop, m):
        ranks = [i for i in range(len(pop))]
        probs = [1 / (rank + 1 + len(pop)) for rank in ranks]
        parents = random.choices(pop, weights=probs, k=m)

        print("The selected parents is",parents)
        return parents

    def keep_populations_history(self, population, populations_history):
        existing_fitness = {individual['fitness'] for individual in populations_history}
        for individual in population:
            if individual['fitness'] is None:
                continue
            if individual['fitness'] not in existing_fitness:
                populations_history.append(individual)
                existing_fitness.add(individual['fitness'])
        return populations_history


    def trigger_resample(self, population, populations_history):
        # This part of the code will be released after the paper is accepted.

        return population

#######################################################Crossover and Mutation###########################################
    def offspring(self, population = None, operator = None):

        if operator == "crossover":
            offspring = self.crossover(population)
        elif operator == "mutation":
            offspring = self.mutation(population)
        else:
            offspring = self.initial()

        name = offspring['name']
        algorithm = offspring['algorithm']
        code = offspring['code']


        with concurrent.futures.ThreadPoolExecutor() as executor:         #Evaluate heuristic
            future = executor.submit(evaluate_Manger, name, algorithm, code, operator)
            fitness = future.result(timeout=self.exp_timeout)
            if fitness is None:
                offspring['fitness'] = None
            else:
                offspring['fitness'] = np.round(fitness[0], 10)
                offspring['gap_power_rate'] = np.round(fitness[1], 10)
                offspring['gap_price_rate'] = np.round(fitness[2], 10)
            future.cancel()

        offspring['from'] = operator
        return offspring


    def initial(self):
        prompt = self.prompts.prompt_initial()
        offspring_initial = self.interface.extract_generation(prompt, self.temperature)
        return offspring_initial


    def mutation(self, populations):                   #Mutation
        parent = self.selection(populations, 1)


        parent_copy = parent.copy()
        parent_copy = [{key: individual[key] for key in ['name', 'algorithm', 'fitness']} for individual in parent_copy]
        parent_copy = [str(population_dict) for population_dict in parent_copy]


        populations_copy = populations.copy()
        populations_copy = [{key: individual[key] for key in ['name', 'algorithm', 'fitness']} for individual in populations_copy]
        populations_copy = [str(population_dict) for population_dict in populations_copy]
        prompt = self.prompts.prompt_mutation(populations_copy, parent_copy)

        print("prompts mutation", prompt)

        offspring_mutation = self.interface.extract_generation(prompt, self.temperature)
        return offspring_mutation

    def crossover(self, populations):                 #Crossover
        parents = self.selection(populations, 2)


        parents_copy = parents.copy()
        parents_copy = [{key: individual[key] for key in ['name', 'algorithm', 'fitness']} for individual in parents_copy]
        parents_copy = [str(population_dict) for population_dict in parents_copy]


        populations_copy = populations.copy()
        populations_copy = [{key: individual[key] for key in ['name', 'algorithm', 'fitness']} for individual in populations_copy]
        populations_copy = [str(population_dict) for population_dict in populations_copy]
        prompt = self.prompts.prompt_crossover(populations_copy, parents_copy)

        print("prompts crossover", prompt)



        offspring_crossover = self.interface.extract_generation(prompt, self.temperature)
        return offspring_crossover

#######################################################Main program##############

    def run(self):
        self.interface = Interface(self.pop_size,self.n_gens,self.llm_api_endpoint,self.llm_api_key,self.llm_model,self.exp_n_proc,self.exp_timeout)
        print("Evolutionary Computation starts...")
        population = []
        populations_history = []



        # Parallel method
        with ProcessPool(max_workers=48) as pool:
            futures = [
                pool.schedule(self.offspring,timeout=self.exp_timeout + 600) for _ in range(self.pop_size+5)
            ]
            offspring = []

            for future in futures:
                try:
                    result = future.result()
                    offspring.append(result)
                    print("finished")
                except TimeoutError:
                    print("time out")
                except Exception as e:
                    print(f"Task error: {e}")




        #Seed method
        # json_file_path = '../Test/results/population/population_generation_0.json'  #Test set path
        # with open(json_file_path, 'r') as f:
        #     offspring = json.load(f)


        for off in offspring:
            population.append(off)

        print("##########################################Population",population)
        print(len(population))

        populations_history = self.keep_populations_history(population, populations_history)          #keep historical population
        population = self.management(population, None, self.pop_size,  'initial')         #Population management

        print("##########################################Population aftermanagement",population)
        print(len(population))


        print("##########################################Historical population",populations_history)
        print(len(populations_history))


        print(f"Pop initial: ")
        for off in population:
            print(" fitness: ", off['fitness'], end="|")
        print()
        print(f"initial population has been created!  Time Cost:{((time.time()-time_start)/60):.1f} m")
        filename = "./results/population/population_generation_0.json"
        with open(filename, 'w') as f:
            json.dump(population, f, indent=5)

        best_history = []
        no_improve_count = 0

        for generation in range(self.n_gens):
            print(f"Generation {generation+1} starts...")
            operators = ["crossover"] * (self.pop_size // 2) + ["mutation"] * (self.pop_size // 2)


            with ProcessPool(max_workers=48) as pool:
                futures = [
                    pool.schedule(self.offspring, args=(population, operator), timeout = self.exp_timeout + 300)
                    for operator in operators
                ]
                offspring = []
                for future in futures:
                    try:
                        result = future.result()
                        offspring.append(result)
                        print("finished")
                    except TimeoutError:
                        print("time out")
                    except Exception as e:
                        print(f"Task error: {e}")

            correct_offspring = []
            for off in offspring:
                print(" springs fitness:", off['fitness'], end="|")
                if off['fitness'] is not None:
                    correct_offspring.append(off)
                # population.append(off)

            populations_history = self.keep_populations_history(correct_offspring, populations_history)
            population = self.management(population, correct_offspring,  self.pop_size)
            print()

            # Save population to a file
            filename = "./results/population/population_generation_" + str(generation + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population, f, indent=5)

            # Save the best one to a file
            filename = "./results/population_best/population_generation_" + str(generation + 1) + ".json"
            with open(filename, 'w') as f:
                json.dump(population[0], f, indent=5)


            print(f"--- {generation + 1} of {self.n_gens} populations finished. Time Cost:  {((time.time()-time_start)/60):.1f} m")
            print("Pop fitness: ", end=" ")
            for i in range(len(population)):
                print(population[i]['fitness'], end="|")
            print()


            best = population[0]['fitness']
            if len(best_history) > 0 and best == best_history[-1]:
                no_improve_count += 1
            else:
                no_improve_count = 0

            best_history.append(best)


            if no_improve_count >= 2 and (generation + 1) != self.n_gens:
                print("###################################Trapped in a local optimum, triggering population optimization##########")
                population = self.trigger_resample(population, populations_history)
                no_improve_count = -1

        print("Evolutionary Computation finished!")
        print(" Best individual fitness: ", population[0]['fitness'])



















