import numpy as np


class DNKPU():
    """
    Class to define a DNPU kernel performing (vertical) soble filter. 
    The kernel represents 3 DNPUs with current sum and linear scaling (a * x + b) and 21 DACs grouped into input_DACs and weight_DACs.
    """
    def __init__(self, dataflow, DAC_input_share) -> None:

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
        
        # access management
        if self.dataflow == "weight_stationary":
            if not self.DAC_input_share:
                self.DNPU_access = 3
                self.DAC_access = self.input_DACs * 1 + self.weight_DACs * 0.
            else:
                self.DNPU_access = 3
                self.DAC_access = self.input_DACs * 0. + self.weight_DACs * 0.
        elif self.dataflow == "input_stationary":
            raise Exception("Sorry mate, not implemented yet...") 
        else:
            raise Exception("Sorry mate, not implemented yet...")

        return {
            # "computation_result": np.sum(y),
            "DAC_access": self.DAC_access,
            "DNPU_access": self.DNPU_access
        }

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

        self.digital_MAC_access = 0

    def run(self, x):
        """
        x: np.array
            - a numpy array (CH, H, W)
        """

        assert x.shape[0] == len(self.DNKPUs), "sorry mate. currently, the simulator considers only full utilization..."
        # perform convolution
        if self.dataflow == "weight_stationary":
            for h in range(1, x.shape[2] - 1):
                for w in range(1, x.shape[1] - 1):
                    for c in range(0, x.shape[0]):
                        dnkpu_out = self.DNKPUs[c].run(x[c][h-1:h+2, w-1:w+2])
                        self.DAC_access += dnkpu_out["DAC_access"]
                        self.DNPU_access += dnkpu_out["DNPU_access"]
                        
                        # Number of access to a digital counterpart performing 3*3 kernel operation 
                        self.digital_MAC_access += 1
                    
                    self.ADC_access += 1
            return self.ADC_access, self.DAC_access, self.DNPU_access, self.digital_MAC_access                
        else:
            raise Exception("Sorry mate, not implemented yet...") 
        
class Crossbar():
    def __init__(self, num_rows, num_columns, dataflow) -> None:
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.dataflow = dataflow

        self.total_DNPU_access = 0
        self.total_DAC_access = 0
        self.total_ADC_access = 0
        self.total_digital_access = 0

        self.crossbar = [crossbar_column(self.num_rows, "weight_stationary", False if i == 0 else True) for i in range(0, self.num_columns)]
                

    def run(self, x):
        """
        x: np.array
            - a numpy array (CH_out, CH_in, H, W)
            where, CH_out is the number of output channels (equal to the number of columns),
            and CH_in is the number of input channels (equal to the number of rows).
        """
        assert x.shape[0] == self.num_columns and x.shape[1] == self.num_rows, "Sorry mate, currently, the simulator only supports full utilization ..."

        for c_out in range(0, x.shape[0]):
            _x, _y , _z, _k = self.crossbar[c_out].run(x[c_out])
            self.total_ADC_access += _x
            self.total_DAC_access += _y
            self.total_DNPU_access += _z
            self.total_digital_access += _k

        return self.total_ADC_access, self.total_DAC_access, self.total_DNPU_access, self.total_digital_access

if __name__ == "__main__":
    

    input_image = np.zeros((64, 64, 32, 32))
    crossbar = Crossbar(
        num_rows    = 64,
        num_columns = 64,
        dataflow    = "weight_stationary"
    )
    adc_access, dac_access, dnpu_access, digital_MAC_access = crossbar.run(input_image)

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


    DNPU_energy = dnpu_access * 5e-9 * 10e-9
    DAC_energy = dac_access * 1.2e-15
    ADC_energy = adc_access * 5.4e-15
    digital_MAC_energy = digital_MAC_access * 5.173e-6*0.97e-9

    print(
        "----------------------------------------------------------------------------------------------------\n"
        "Number of DNPU access is ", dnpu_access, ", consuming ", DNPU_energy, "J of energy\n",
        "Number of DAC access is ", dac_access, ", consuming ", DAC_energy, "J of energy\n",
        "Number of ADC access is ", adc_access, ", consuming ", ADC_energy, "J of energy\n",
        "----------------------------------------------------------------------------------------------------\n"
        "The total power consumption of crossbar array of DNPUs with ", input_image.shape[0], "DNKPUs is: ", DNPU_energy + DAC_energy + ADC_energy, "\n"
        "While in digital, the number of access is: ", digital_MAC_access, "consuming: ", digital_MAC_energy, "J.",
        "----------------------------------------------------------------------------------------------------\n",
        "This shows ", digital_MAC_energy/(DNPU_energy + DAC_energy + ADC_energy), "X improvement when using DNPU crossbar array compared to a similar digital counterpart."
    )

    print()

