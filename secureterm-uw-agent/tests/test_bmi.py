from secureterm_uw.arithmetic.bmi import calculate_bmi, parse_height_cm, parse_weight_kg


def test_feet_inches_converted_to_cm():
    parsed = parse_height_cm("5'10\"")
    assert 177 < parsed.value < 179


def test_pounds_converted_to_kg():
    parsed = parse_weight_kg("198 lbs")
    assert 89 < parsed.value < 90.5


def test_bmi_corrects_policycenter_imperial_defect():
    result = calculate_bmi("5'10\"", "198 lbs", policycenter_bmi="72.1")
    assert 27 < result.bmi < 29
    assert result.unit_mismatch_corrected is True
    assert result.deviation_percent is not None and result.deviation_percent > 1
    assert result.requires_manual_check is True


def test_metric_inputs():
    result = calculate_bmi("172 cm", "70 kg", policycenter_bmi="23.66")
    assert result.bmi == 23.66
    assert result.deviation_percent == 0
