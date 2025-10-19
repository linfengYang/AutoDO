import numpy as np

def solve_rolling_uc_CP(units_info, load):
    n_units = len(units_info)
    flac_list = []

    #CPlist
    for idx, unit in enumerate(units_info):
        a, b, c, p_max = unit['a_i'], unit['b_i'], unit['c_i'], unit['p_max_i']
        flac = (a + b * p_max + c * p_max ** 2) / p_max
        flac_list.append((flac, idx))


    # Sort units by FLAC (ascending)
    sorted_indices = [idx for _, idx in sorted(flac_list, key=lambda x: x[0])]



    u_current = [0] * n_units
    p_current = [0] * n_units

    # Apply minimum up/down time constraints
    for i, unit in enumerate(units_info):
        u_i0, t_i0, p_i0 = unit['u_i_0'], unit['t_i_0'], unit['p_i_0']
        t_on_min, t_off_min, p_shut = unit['t_on_min_i'], unit['t_off_min_i'], unit['p_shut_i']

        if u_i0 == 1:
            if t_i0 < t_on_min or p_i0 > p_shut:
                u_current[i] = 1
                p_current[i] = max(unit['p_min_i'], min(p_i0, unit['p_max_i']))

            else:
                u_current[i] = u_i0
                p_current[i] = p_i0
        else:
            if -t_i0 < t_off_min:
                u_current[i] = 0
                p_current[i] = 0
            else:
                u_current[i] = u_i0
                p_current[i] = p_i0

    total_generation = sum(p_current)
    load_difference = load - total_generation

    # Load increase case
    if load_difference > 0:
        for idx in sorted_indices:
            if load_difference <= 0:
                break
            unit = units_info[idx]
            if u_current[idx] == 1:
                # Already online - increase output
                current_p = p_current[idx]
                max_increase = min(unit['p_up_i'], unit['p_max_i'] - current_p)
                increase = min(load_difference, max_increase)
                p_current[idx] += increase
                load_difference -= increase
            else:
                if -unit['t_i_0'] >= unit['t_off_min_i']:
                    u_current[idx] = 1
                    min_p = unit['p_min_i']
                    max_p = min(unit['p_max_i'], unit['p_start_i'])
                    allocation = min(load_difference, max_p)
                    allocation = max(min_p, allocation)
                    p_current[idx] = allocation
                    load_difference -= allocation

    elif load_difference < 0:
        load_difference = abs(load_difference)
        for idx in reversed(sorted_indices):
            if load_difference <= 0:
                break
            if u_current[idx] == 1:
                unit = units_info[idx]
                current_p = p_current[idx]
                min_p = unit['p_min_i']

                # Reduce output if possible
                max_decrease = min(unit['p_down_i'], current_p - min_p)
                if max_decrease > 0:
                    decrease = min(load_difference, max_decrease)
                    p_current[idx] -= decrease
                    load_difference -= decrease

                # Shutdown unit if possible
                if (load_difference > 0 and
                        unit['t_i_0'] >= unit['t_on_min_i'] and
                        current_p <= unit['p_shut_i']):
                    u_current[idx] = 0
                    load_difference -= current_p
                    p_current[idx] = 0

    return np.array([u_current, p_current])
