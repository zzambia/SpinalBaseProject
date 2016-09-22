import random
from Queue import Queue

import cocotb
from cocotb.result import TestFailure
from cocotb.triggers import RisingEdge, Timer

@cocotb.coroutine
def genClockAndReset(dut):
    dut.reset = 1
    dut.clk = 0
    yield Timer(1000)
    dut.reset = 0
    yield Timer(1000)
    while True:
        dut.clk = 1
        yield Timer(500)
        dut.clk = 0
        yield Timer(500)


@cocotb.coroutine
def driverAgent(dut):
    dut.io_push_valid = 0
    dut.io_pop_ready  = 0

    while True:
        yield RisingEdge(dut.clk)
        dut.io_push_valid   = random.random() < 0.5
        dut.io_push_payload = random.randint(0,255)
        dut.io_pop_ready    = random.random() < 0.5


@cocotb.coroutine
def checkerAgent(dut):
    queue = Queue()
    matchCounter = 0
    while matchCounter < 5000:
        yield RisingEdge(dut.clk)

        # capture and store 'push' transactions
        if dut.io_push_valid == 1 and dut.io_push_ready == 1:
            queue.put(int(dut.io_push_payload))

        # capture and check 'pop' transactions
        if dut.io_pop_valid == 1 and dut.io_pop_ready == 1:
            if queue.empty():
                raise TestFailure("parasite io_pop transaction")
            if dut.io_pop_payload != queue.get():
                raise TestFailure("io_pop_payload missmatch")
            matchCounter += 1

@cocotb.test()
def test1(dut):
    # Create all threads
    cocotb.fork(genClockAndReset(dut))
    cocotb.fork(driverAgent(dut))
    checker = cocotb.fork(checkerAgent(dut))

    # Wait until the checker finish his job
    yield checker.join()


