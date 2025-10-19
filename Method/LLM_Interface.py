import http.client
import json
import time
import random
import re
import ast
from openai import OpenAI

class Interface():
    def __init__(self, pop_size, n_gens, llm_api_endpoint, llm_api_key, llm_model, exp_n_proc, exp_timeout):
        self.pop_size = pop_size
        self.n_gens = n_gens

        self.llm_api_endpoint = llm_api_endpoint
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model


        self.exp_n_proc = exp_n_proc
        self.exp_timeout = exp_timeout


    def extract_generation(self, prompt, temperature=1.0):
        offspring = {
            'name': None,
            'algorithm': None,
            'code': None,
            'from': None,
            "gap_power_rate": None,
            "gap_price_rate": None,
            'fitness': None
        }

        response = self.get_response(prompt, temperature)

        pattern = r"def\s+(\w+)"
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            name = match.group(1)
        else:
            name = None
        if name is None:

            pattern = r"\s*Name:\s*(\w*)"
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                name = match.group(1)
            else:
                name = None

        pattern = r"algorithm:\s*(.*?)(?=code:)"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            algorithm = match.group(1)
        else:
            algorithm = None
        if algorithm is None:
            pattern = r"algorithm：\s*(.*?)(?=code：)"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                algorithm = match.group(1)
            else:
                algorithm = None



        pattern = r"```(?:python\s*)?\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1)
        else:
            code = None

        n_retry = 1
        while code is None:
            if n_retry >= 2:
                break
            n_retry += 1

            response = self.get_response(prompt, temperature)

            pattern = r"def\s+(\w+)"
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                name = match.group(1)
            else:
                name = None
            if name is None:
                pattern = r"\s*Name:\s*(\w*)"
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    name = match.group(1)
                else:
                    name = None

            pattern = r"algorithm:\s*(.*?)(?=code:)"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                algorithm = match.group(1)
            else:
                algorithm = None
            if algorithm is None:
                pattern = r"algorithm：\s*(.*?)(?=code：)"
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    algorithm = match.group(1)
                else:
                    algorithm = None


            pattern = r"```(?:python)?\n(.*?)```"
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                code = match.group(1)
            else:
                code = None


        offspring['algorithm'] = algorithm
        offspring['code'] = code
        offspring['name'] = name

        return offspring

    def extract_selection(self, prompt):
        response = self.get_response(prompt)

        match = re.search(r'\[.*\]', response, re.DOTALL)  # Extract the selected offspring
        if match:
            data = match.group(0)
            try:
                selected_individuals_index = ast.literal_eval(data)
                return selected_individuals_index
            except Exception as e:
                print("Parsing error:", e)
                return None
        else:
            print("No list content found")
            return None

    def get_response(self, prompt_content, temperature=1.0):
        print("llm temperature:", temperature)
        print("llm model:", self.llm_model)

        payload_explanation = json.dumps(
            {
                "model": self.llm_model,
                "messages": [
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": temperature,
            }
        )

        headers = {
            "Authorization": "Bearer " + self.llm_api_key,
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "x-api2d-no-cache": 1,
        }

        response = None
        n_trial = 1
        while True:
            n_trial += 1
            if n_trial > 3:
                return response
            try:
                conn = http.client.HTTPSConnection(self.llm_api_endpoint)
                conn.request("POST", "/v1/chat/completions", payload_explanation, headers)
                res = conn.getresponse()
                data = res.read()
                json_data = json.loads(data)
                response = json_data["choices"][0]["message"]["content"]
                break
            except:
                print("Error in API. Restarting the process...")
                continue

        return response



    # def get_response(self, prompt_content, temperature=0.6):
    #
    #     print("waiting for LLM")
    #
    #
    #     client = OpenAI(
    #
    #
    #         api_key="xxxxxxxxxxxxxxxxxxxxxxxxxx",
    #         base_url="xxxxxxxxxxxxxxxxxxxxxxxxx",
    #
    #
    #     )
    #
    #     completion = client.chat.completions.create(
    #         model="deepseek-r1",
    #         # model="deepseek-reasoner",
    #         messages=[
    #             {'role': 'user', 'content': prompt_content}
    #         ]
    #     )
    #
    #
    #     # print(completion.choices[0].message.content)
    #     response = completion.choices[0].message.content
    #     return response





























