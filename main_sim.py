import numpy as np


class DNKPU():
    """
    Class to define a DNPU kernel performing (vertical) soble filter. 
    The kernel represents 3 DNPUs with current sum and linear scaling (a * x + b) and 21 DACs grouped into input_DACs and weight_DACs.
    """
    def __init__(self, dataflow, DAC_input_share) -> None:
        self.DNPU_1 = np.array(([-1., 0., 1.]))
        self.DNPU_2 = np.array(([-1., 0., 1.]))
        self.DNPU_3 = np.array(([-1., 0., 1.]))

        self.dataflow = dataflow
        self.DAC_input_share = DAC_input_share
        
        self.input_DACs = 9
        self.weight_DACs = 12

        self.DNPU_access = 0
        self.DAC_access = 0

    def run(self, x):
        """
        x: numpy array
            cunk of the input, e.g., image as shape of 3 * 3
        """
        
        # output 
        y = np.zeros((3))
        y[0] = np.dot(x[0], self.DNPU_1)
        y[1] = np.dot(x[1], self.DNPU_2)
        y[2] = np.dot(x[2], self.DNPU_3)

        # access management
        if self.dataflow == "weight_stationary":
            if not self.DAC_input_share:
                self.DNPU_access += 3
                self.DAC_access = self.input_DACs * 1 + self.weight_DACs * 0.
            else:
                self.DNPU_access += 3
                self.DAC_access = self.input_DACs * 0. + self.weight_DACs * 0.
        elif self.dataflow == "input_stationary":
            raise Exception("Sorry mate, not implemented yet...") 
        else:
            raise Exception("Sorry mate, not implemented yet...")

        return {
            "computation_result": np.sum(y),
            "DAC_access": self.DAC_access,
            "DNPU_access": self.DNPU_access
        }

# class ADC():
#     """
#     Class to define analog-to-digital converter
#     """
#     def __init__(self) -> None:
#         pass

#     def run(self, ADC_ACCESS):
#         return ADC_ACCESS + 1

class crossbar_column():
    """
    Class to define crossbar column containing DNKPUs, DACs, and ADCs. At the behavioural model, it simulates and keeps track of the number of accesses to each component.
    size : int
        - numer of DNKPU
    dataflow: str
        - input_stationray
        - weight_stationary
    """
    def __init__(self, size, dataflow, DAC_input_share) -> None:
        self.dataflow = dataflow
        self.DAC_input_share = DAC_input_share
        self.DNKPUs = [DNKPU(self.dataflow, self.DAC_input_share) for i in range(0, size)]
        # self.ADC = ADC()
        self.DNPU_access = 0
        self.ADC_access = 0
        self.DAC_access = 0

    def run(self, x):
        """
        x: np.array
            - a numpy array (CH, H, W)
        """

        assert x.shape[0] == len(self.DNKPUs), "sorry mate. currently, the simulator considers only full utilization..."
        y = np.zeros((x.shape[1], x.shape[2]))
        # perform convolution
        if self.dataflow == "weight_stationary":
            if self.DAC_input_share == False:
                for w in range(1, x.shape[2] - 1):
                    for h in range(1, x.shape[1] - 1):
                        partial_y = 0.
                        for c in range(0, x.shape[0]):
                            dnkpu_out = self.DNKPUs[c].run(x[c][h-1:h+2, w-1:w+2])
                            partial_y += dnkpu_out["computation_result"]
                            self.DAC_access += dnkpu_out["DAC_access"]
                            self.DNPU_access += dnkpu_out["DNPU_access"]
                        
                        self.ADC_access += 1
                        y[w, h] = partial_y
                return self.ADC_access, self.DAC_access, self.DNPU_access
            else:
                Exception("Sorry mate, not implemented yet...") 
        else:
            raise Exception("Sorry mate, not implemented yet...") 
        

if __name__ == "__main__":
    
    input_image = np.random.randn(64, 32, 32)
    crossbar = crossbar_column(
        size = 64,
        dataflow = "weight_stationary",
        DAC_input_share = False
    )
    adc_access, dac_access, dnpu_access = crossbar.run(input_image)

    # ------------------------------------------------------------------------------------------------------------------------------------
    # A 34fJ/conversion-step 10-bit 6.66MS/s SAR ADC with built-in digital calibration in 130nm CMOS
    # ADC -> 34 fJ per conversion step

    # https://www.imec-int.com/en/adc-11-enob -> Analog Digital Converter 11 ENOB 170MS/s
    # ADC -> 10 fJ per conversion step

    # A 12bit 250 MS/s 5.43fJ/conversion-step SAR ADC with adaptive asynchronous logic in 28 nm CMOS
    # ADC -> 5.4 fJ per conversion step

    # ------------------------------------------------------------------------------------------------------------------------------------
    # Design of Relaxation Digital-to-Analog Converters for Internet of Things Applications in 40nm CMOS
    # DAC -> 1.2 fJ per conversion step

    #  A Highly Reconfigurable 40-97GS/s DAC and ADC with 40GHz AFE Bandwidth and Sub-35fJ/conv-step for 400Gb/s Coherent Optical Applications in 7nm FinFET
    # DAC -> 18 fJ per conversion step



