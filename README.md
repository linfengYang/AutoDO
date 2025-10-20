In this repository, we provide code for implementing our proposed Evolutionary LLM-Driven Heuristics Framework for Rolling Unit Commitment under Renewable-Induced Forecast Uncertainty.

Our framework uses a dual-role LLM as both heuristic designer and population optimizer. Through parallel crossover and mutation, it automatically generates and optimizes heuristics for Rolling Unit Commitment, improving adaptability, search efficiency, and robustness under renewable-induced forecast uncertainty compared to manually designed methods.

## Requirements:
joblib==1.4.2

matplotlib==3.10.0

numpy==2.0.1

openai==1.101.0

pebble==5.1.3

gurobipy==12.0

## Dataset Preparation
We use the Unit Commitment dataset, available in (http://groups.di.unipi.it/optimize/Data/UC.html)

## Get the paper results quickly
Some of the best-generated heuristics ('*.json' files) are in the folder directory '/Docs/Experimental results/Best/' 

## Start the heuristics training
You can run Run.py in the folder directory '/Test/', and you also need to configure your LLM API key and endpoint.

------

Contact e-mail:mail_shijianhuang@163.com
