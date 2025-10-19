import numpy as np

def readUC(data_UC, pathAndFilename):
    with open(pathAndFilename) as obj:
        obj.readline()
        temp = obj.readline()
        data_UC.T = int(temp.split()[1])   # HorizonLen 24 periods
        temp = obj.readline()
        data_UC.N = int(temp.split()[1])    # NumThermal number of units
        for i in range(7):
            obj.readline()
        pd = obj.readline()
        for each in pd.split():
            data_UC.PD.append(float(each))    # Loads for each period
        obj.readline()
        rt = obj.readline()
        for each in rt.split():
            data_UC.Spin.append(float(each))   # Spin reserve for each period
        obj.readline()
        unit_parameter = []
        for i in range(data_UC.N):
            temp = obj.readline()
            unit_parameter.append(temp.split())         # 15th line data
            temp = obj.readline()
            data_UC.Pup.append(float(temp.split()[1]))        # 16th line ramp-up constraint
            data_UC.Pdown.append(float(temp.split()[2]))

        if "_std.mod" in pathAndFilename and len(unit_parameter[0]) == 17:
            data_UC.TimeCold = [float(i[16]) for i in unit_parameter]        # The 17th parameter is cold start time
        CostHotTemp = [float(i[13]) for i in unit_parameter]                # 14th parameter hot start cost
        # Initialize parameters
        data_UC.Alpha = [float(i[3]) for i in unit_parameter]  # Parameter α (cost parameter)
        data_UC.Beta = [float(i[2]) for i in unit_parameter]  # Parameter β
        data_UC.Gamma = [float(i[1]) for i in unit_parameter]  # Parameter γ
        data_UC.Pmax = [float(i[5]) for i in unit_parameter]  # Unit power upper limit
        data_UC.Pmin = [float(i[4]) for i in unit_parameter]  # Unit power lower limit
        data_UC.MinTimeOff = [float(i[8]) for i in unit_parameter]  # Minimum downtime
        data_UC.MinTimeOn = [float(i[7]) for i in unit_parameter]  # Minimum uptime
        data_UC.T0 = [float(i[6]) for i in unit_parameter]  # Time on/off before T0
        data_UC.P0 = [float(i[15]) for i in unit_parameter]  # Initial power state of each unit
        # data_UC.Pstart = data_UC.Pmin                        # Startup capability
        # data_UC.Pshut = data_UC.Pmin
        data_UC.Pstart = [float(i[4]) for i in unit_parameter]
        data_UC.Pshut =[float(i[4]) for i in unit_parameter]
        data_UC.PD = np.array(data_UC.PD)                    # Convert to numeric array
        data_UC.Spin = np.array(data_UC.Spin)                # Convert to numeric array

        for i in data_UC.P0:
            if i != 0:
                data_UC.u0.append(1)
            else:
                data_UC.u0.append(0)

        if "_std.mod" in pathAndFilename:                 # Cold start cost for different units
            data_UC.CostCold = [i for i in CostHotTemp]  # Thermal unit cold start cost - N * 1 matrix
            if "5_std.mod" in pathAndFilename:
                data_UC.CostCold = CostHotTemp
        else:
            data_UC.TimeCold = [0] * data_UC.N
            data_UC.CostCold = CostHotTemp

        data_UC.TimeCold = [0] * data_UC.N

        data_UC.CostHot = CostHotTemp
        data_UC.StartCost = data_UC.CostHot
        data_UC.iframp = np.ones(data_UC.N)
        data_UC.CostFlag = np.ones(data_UC.N)

        return data_UC


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
