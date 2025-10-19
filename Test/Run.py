from Method.Evolution import EC



ec = EC()
ec.set_paras(
            llm_api_endpoint = "api.deepseek.com", #endpoint
            llm_api_key = "xxxxxxxxxxxxx",   #key
            # llm_model = "deepseek-chat", #Chat model
            llm_model = "deepseek-reasoner", #Reasoning model

            pop_size = 10,         #Population size
            n_gens = 15,           #Number of generations
            exp_n_proc = 10,       #Number of processor cores
            exp_timeout = 1000)    #Timeout (seconds)

if __name__ == '__main__':
    ec.show_paras()
    ec.run()



