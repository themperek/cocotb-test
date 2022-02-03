
import cocotb_test.simulator


# For partial back compatibility
def run(simulator=None, **kwargs):

    if simulator:
        sim = simulator(**kwargs)
        sim.run()
    else:
        cocotb_test.simulator.run(**kwargs)
