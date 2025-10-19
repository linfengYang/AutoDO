import json
import os



########################################################################



# folder_path = "../ablation/AutoDO-M"
# gap_power_rates = []
# gap_price_rates = []
#
#
# for filename in ["run1.json", "run2.json", "run3.json"]:
#     file_path = os.path.join(folder_path, filename)
#
#
#     try:
#         with open(file_path, 'r') as file:
#             data_list = json.load(file)
#
#             for data in data_list:
#
#                 if "gap_power_rate" in data:
#                     gap_power_rates.append(data["gap_power_rate"])
#                 if "gap_price_rate" in data:
#                     gap_price_rates.append(data["gap_price_rate"])
#
#     except FileNotFoundError:
#         print(f"Warning: File {filename} not found")
#     except Exception as e:
#         print(f"Error processing file {filename}: {e}")
#
# avg_gap_power = round(sum(gap_power_rates) / len(gap_power_rates), 4) if gap_power_rates else 0
# avg_gap_price = round(sum(gap_price_rates) / len(gap_price_rates), 4) if gap_price_rates else 0
#
# result = {
#     "avg_gap_power_rate": avg_gap_power,
#     "avg_gap_price_rate": avg_gap_price
# }
#
# print(f"Processed {len(gap_power_rates)} records")
# print(f"gap_power_rate average: {avg_gap_power}")
# print(f"gap_price_rate average: {avg_gap_price}")
#
#
# output_path = os.path.join(folder_path, "average.json")
# with open(output_path, 'w') as output_file:
#     json.dump(result, output_file, indent=4)
#
# print(f"Results saved to: {output_path}")

######################### Average value of three data sets ################################



# folder_path = "../ablation/AutoDO-O"
#
# # folder_path = "../three_time/AutoDO_with_next_load_R1"
#
#
#
# for filename in ["run1.json", "run2.json", "run3.json"]:
#     file_path = os.path.join(folder_path, filename)
#
#     gap_power_rates = []
#     gap_price_rates = []
#
#     try:
#         with open(file_path, 'r') as file:
#             data_list = json.load(file)
#
#             for data in data_list:
#                 if "gap_power_rate" in data:
#                     gap_power_rates.append(data["gap_power_rate"])
#                 if "gap_price_rate" in data:
#                     gap_price_rates.append(data["gap_price_rate"])
#
#     except FileNotFoundError:
#         print(f"Warning: File {filename} not found")
#     except Exception as e:
#         print(f"Error processing file {filename}: {e}")
#
#     avg_gap_power = round(sum(gap_power_rates) / len(gap_power_rates), 4)
#     avg_gap_price = round(sum(gap_price_rates) / len(gap_price_rates), 4)
#     fitness =  0.5 * (avg_gap_power + avg_gap_price)
#
#     result = {
#         "avg_gap_power_rate": avg_gap_power,
#         "avg_gap_price_rate": avg_gap_price
#     }
#
#     print(f"Processing file: {filename}")
#     print(f"Processed {len(gap_power_rates)} records")
#     print(f"gap_power_rate average: {avg_gap_power}")
#     print(f"gap_price_rate average: {avg_gap_price}")
#     print(f"fitness: {fitness}")


################################# Average values of three algorithms on different data scales #######################
import json
import os
from collections import defaultdict

files = ["../ablation/AutoDO-S/run1.json", "../ablation/AutoDO-S/run2.json", "../ablation/AutoDO-S/run3.json"]

groups = defaultdict(lambda: {"gap_power_rate": [], "gap_price_rate": []})

for file in files:
    with open(file, "r") as f:
        data = json.load(f)
        for record in data:
            prefix = record["data"].split("_")[0]  # Extract prefix
            groups[prefix]["gap_power_rate"].append(record["gap_power_rate"])
            groups[prefix]["gap_price_rate"].append(record["gap_price_rate"])


temp1 = 0
temp2 = 0

# Calculate averages
result = {}
for prefix, values in groups.items():
    result[prefix] = {
        "gap_power_rate_avg": round(sum(values["gap_power_rate"]) / len(values["gap_power_rate"]), 4),
        "gap_price_rate_avg": round(sum(values["gap_price_rate"]) / len(values["gap_price_rate"]), 4)
    }


    print(len(values["gap_power_rate"]))
    temp1 += sum(values["gap_power_rate"])
    temp2 += sum(values["gap_price_rate"])


temp1 = temp1 / (3*42)
temp2 = temp2 / (3*42)
print(temp1)
print(temp2)

result["avg"] = {
    "gap_power_rate_avg": round(temp1, 4),
    "gap_price_rate_avg": round(temp2, 4)
}


with open("../ablation/AutoDO-S/average_result.json", "w") as f:
    json.dump(result, f, indent=5)

print("Results saved to average_result.json")
