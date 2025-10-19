import numpy as np

def readUC(data_UC, pathAndFilename):
    with open(pathAndFilename) as obj:

        obj.readline()
        temp = obj.readline()
        data_UC.T = int(temp.split()[1])   # Horizon length (number of periods)
        temp = obj.readline()
        data_UC.N = int(temp.split()[1])    # Number of generating units
        for i in range(7):
            obj.readline()
        pd = obj.readline()

        for each in pd.split():
            data_UC.PD.append(float(each))    # Loads for each period
        obj.readline()
        rt = obj.readline()
        for each in rt.split():
            data_UC.Spin.append(float(each))   # Spinning reserve for each period
        obj.readline()
        unit_parameter = []
        for i in range(data_UC.N):
            temp = obj.readline()
            unit_parameter.append(temp.split())
            temp = obj.readline()
            data_UC.Pup.append(float(temp.split()[1]))        # Ramp-up limit
            data_UC.Pdown.append(float(temp.split()[2]))      # Ramp-down limit


        CostHotTemp = [float(i[13]) for i in unit_parameter]  # Hot start cost (14th parameter)

        data_UC.Alpha = [float(i[3]) for i in unit_parameter]  # Parameter α
        data_UC.Beta = [float(i[2]) for i in unit_parameter]   # Parameter β
        data_UC.Gamma = [float(i[1]) for i in unit_parameter]  # Parameter γ
        data_UC.Pmax = [float(i[5]) for i in unit_parameter]   # Maximum power of units
        data_UC.Pmin = [float(i[4]) for i in unit_parameter]   # Minimum power of units
        data_UC.MinTimeOff = [float(i[8]) for i in unit_parameter]  # Minimum downtime
        data_UC.MinTimeOn = [float(i[7]) for i in unit_parameter]   # Minimum uptime
        data_UC.T0 = [float(i[6]) for i in unit_parameter]          # Time the unit has been on/off before T0
        data_UC.P0 = [float(i[15]) for i in unit_parameter]         # Initial power of each unit
        data_UC.Pstart = [float(i[4]) for i in unit_parameter]      # Start-up capability
        data_UC.Pshut =[float(i[4]) for i in unit_parameter]        # Shut-down capability
        data_UC.PD = np.array(data_UC.PD)                            # Convert to numeric array
        data_UC.Spin = np.array(data_UC.Spin)                        # Convert to numeric array


        for i in data_UC.P0:
            if i != 0:
                data_UC.u0.append(1)
            else:
                data_UC.u0.append(0)


        data_UC.TimeCold = [0] * data_UC.N
        data_UC.CostCold = CostHotTemp
        data_UC.CostHot = CostHotTemp
        data_UC.StartCost = CostHotTemp

        return data_UC


class UC_Data:
    def __init__(self):
            self.T = 0  # Number of periods
            self.N = 0  # Number of generating units
            self.PD = []  # Load
            self.Spin = []  # Spinning reserve
            self.Pup = []  # Ramp-up limit
            self.Pdown = []  # Ramp-down limit
            self.TimeCold = []  # Cold start time
            self.CostCold = []  # Cold start cost
            self.CostHot = []  # Hot start cost
            self.StartCost = []  # Initial cost
            self.Alpha = []  # Parameter α
            self.Beta = []  # Parameter β
            self.Gamma = []  # Parameter γ
            self.Pmax = []  # Maximum power of units
            self.Pmin = []  # Minimum power of units
            self.MinTimeOff = []  # Minimum downtime
            self.MinTimeOn = []  # Minimum uptime
            self.T0 = []  # Time the unit has been on/off before T0
            self.P0 = []  # Initial power of each unit
            self.Pstart = []  # Start-up capability
            self.Pshut = []  # Shut-down capability
            self.u0 = []  # Initial state


    def print_class_attributes(self):

        attributes = {
            'T': 'Number of periods',
            'N': 'Number of generating units',
            'PD': 'Load',
            'Spin': 'Spinning reserve',
            'Pup': 'Ramp-up limit',
            'Pdown': 'Ramp-down limit',
            'TimeCold': 'Cold start time',
            'CostCold': 'Cold start cost',
            'CostHot': 'Hot start cost',
            'StartCost': 'Initial cost',
            'Alpha': 'Parameter α',
            'Beta': 'Parameter β',
            'Gamma': 'Parameter γ',
            'Pmax': 'Maximum power of units',
            'Pmin': 'Minimum power of units',
            'MinTimeOff': 'Minimum downtime',
            'MinTimeOn': 'Minimum uptime',
            'T0': 'Time the unit has been on/off before T0',
            'P0': 'Initial power of each unit',
            'Pstart': 'Start-up capability',
            'Pshut': 'Shut-down capability',
            'u0': 'Initial state'
        }

        for attr, comment in attributes.items():
            print(f"{attr}: {getattr(self, attr)}  # {comment}")
