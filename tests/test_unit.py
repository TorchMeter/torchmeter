from enum import Enum

import pytest

from torchmeter.unit import (
    CountUnit,
    BinaryUnit,
    TimeUnit,
    SpeedUnit,
    auto_unit
)

def is_unitsys_valid(unit_sys):
    assert issubclass(unit_sys, Enum)
    assert all(unit_val > 0 for unit_val in unit_sys._value2member_map_.keys())

@pytest.fixture(params=[CountUnit, BinaryUnit, TimeUnit, SpeedUnit])
def all_type_unit(request):    
    return request.param

def test_count_unit():    
    is_unitsys_valid(CountUnit)
    
    assert CountUnit.T.value == 1e12
    assert CountUnit.G.value == 1e9
    assert CountUnit.M.value == 1e6
    assert CountUnit.K.value == 1e3
    
    assert len(list(CountUnit)) == 4

def test_binary_unit():
    is_unitsys_valid(BinaryUnit)
    
    assert BinaryUnit.TiB.value == 2**40
    assert BinaryUnit.GiB.value == 2**30
    assert BinaryUnit.MiB.value == 2**20
    assert BinaryUnit.KiB.value == 2**10
    assert BinaryUnit.B.value == 2**0
    
    assert len(list(BinaryUnit)) == 5

def test_time_unit():
    is_unitsys_valid(TimeUnit)
    
    assert TimeUnit.h.value == 60**2
    assert TimeUnit.min.value == 60**1
    assert TimeUnit.s.value == 60**0
    assert TimeUnit.ms.value == 1e-3
    assert TimeUnit.us.value == 1e-6
    assert TimeUnit.ns.value == 1e-9
    
    assert len(list(TimeUnit)) == 6

def test_speed_unit():
    is_unitsys_valid(SpeedUnit)
    
    assert SpeedUnit.TSamPS.value == 1e12
    assert SpeedUnit.GSamPS.value == 1e9
    assert SpeedUnit.MSamPS.value == 1e6
    assert SpeedUnit.KSamPS.value == 1e3
    assert SpeedUnit.SamPS.value == 1e0
    
    assert len(list(SpeedUnit)) == 5

@pytest.mark.vital
def test_auto_unit(all_type_unit):
    stage_vals = list(all_type_unit._value2member_map_.keys())
    stage_vals.sort()
    
    # in range
    for i in range(len(stage_vals)-1):
        low_stage, high_stage = stage_vals[i:i+2]
        unit = all_type_unit(low_stage).name

        if 2 * low_stage < high_stage:
            integral_multiple_val = 2 * low_stage
            int_multiple_time = 2
        else:
            integral_multiple_val = low_stage
            int_multiple_time = 1
        assert f"{int_multiple_time} {unit}" == auto_unit(integral_multiple_val, 
                                                      unit_system=all_type_unit)

        float_multiple_val = 1.9 * low_stage
        while not float_multiple_val % low_stage and float_multiple_val < 2*low_stage-1:
            float_multiple_val += 1
        assert f"{1.9:.2f} {unit}" == auto_unit(float_multiple_val, 
                                                unit_system=all_type_unit)
    
    # out of range(smaller)
    underflow_float_val = stage_vals[0] / 2
    assert f"{underflow_float_val:.2f}" == auto_unit(underflow_float_val,
                                                     unit_system=all_type_unit)
    
    underflow_int_val = int(underflow_float_val)
    assert f"{underflow_int_val}" == auto_unit(underflow_int_val,
                                               unit_system=all_type_unit)
    
    # out of range(bigger)
    unit = all_type_unit(stage_vals[-1]).name
    
    overflow_integral_multiple_val = stage_vals[-1] * 2
    assert f"2 {unit}" == auto_unit(overflow_integral_multiple_val,
                                    unit_system=all_type_unit)
    overflow_float_multiple_val = stage_vals[-1] * 1.5
    assert f"{1.5:.2f} {unit}" == auto_unit(overflow_float_multiple_val,
                                            unit_system=all_type_unit)