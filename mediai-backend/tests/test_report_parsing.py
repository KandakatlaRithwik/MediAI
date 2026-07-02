"""Tests for ReportParserService (regex-based parameter detection)."""

from app.services.report_parser_service import ReportParserService


def test_parses_cbc_parameters():
    service = ReportParserService()
    text = "Hemoglobin: 11.2 g/dL\nWBC Count: 7800 /uL\nPlatelet Count: 1,80,000 /uL\nMCH: 29\nMCHC: 33"
    result = service.parse(text)
    assert result["hemoglobin"] == 11.2
    assert result["wbc_count"] == 7800
    assert result["platelet_count"] == 180000
    # MCH and MCHC must not cross-contaminate each other.
    assert result["mch"] == 29
    assert result["mchc"] == 33


def test_parses_blood_sugar_parameters():
    service = ReportParserService()
    text = "Fasting Blood Sugar: 145 mg/dL\nHbA1c: 6.8 %"
    result = service.parse(text)
    assert result["glucose"] == 145
    assert result["hba1c"] == 6.8


def test_parses_lipid_profile_parameters():
    service = ReportParserService()
    text = "Total Cholesterol: 235\nLDL Cholesterol: 165\nHDL: 38\nTriglycerides: 210"
    result = service.parse(text)
    assert result["cholesterol"] == 235
    assert result["ldl"] == 165
    assert result["hdl"] == 38
    assert result["triglycerides"] == 210


def test_parses_thyroid_profile_parameters():
    service = ReportParserService()
    text = "TSH: 8.4\nT3: 120\nT4: 7.5"
    result = service.parse(text)
    assert result["tsh"] == 8.4
    assert result["t3"] == 120
    assert result["t4"] == 7.5


def test_parses_kidney_function_test_parameters():
    service = ReportParserService()
    text = "Serum Creatinine: 1.8\nBlood Urea: 45\nUric Acid: 8.1"
    result = service.parse(text)
    assert result["creatinine"] == 1.8
    assert result["urea"] == 45
    assert result["uric_acid"] == 8.1


def test_parses_liver_function_test_parameters():
    service = ReportParserService()
    text = "SGOT: 65\nSGPT: 90\nTotal Bilirubin: 1.9"
    result = service.parse(text)
    assert result["sgot"] == 65
    assert result["sgpt"] == 90
    assert result["bilirubin"] == 1.9


def test_spec_example_values():
    service = ReportParserService()
    text = "Hemoglobin: 11.2\nGlucose: 145\nTSH: 8.4\nCholesterol: 235"
    result = service.parse(text)
    assert result["hemoglobin"] == 11.2
    assert result["glucose"] == 145
    assert result["tsh"] == 8.4
    assert result["cholesterol"] == 235


def test_no_recognizable_parameters_returns_empty_dict():
    service = ReportParserService()
    result = service.parse("This is just some unrelated text with no lab values.")
    assert result == {}


def test_case_insensitive_matching():
    service = ReportParserService()
    result = service.parse("glucose: 145\nHEMOGLOBIN: 11.2")
    assert result["glucose"] == 145
    assert result["hemoglobin"] == 11.2
