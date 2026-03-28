from pilot.parser import parse_natural_language
from pilot.schema import StructureType


def test_parse_patch_2p4ghz():
    q = "Design a 2.4 GHz rectangular patch antenna on FR4 with S11 < -10 dB near resonance."
    spec = parse_natural_language(q)
    assert spec.structure_type == StructureType.RECTANGULAR_PATCH
    assert abs(spec.frequency.center_ghz - 2.4) < 1e-6
    assert spec.performance.s11_max_db == -10.0
    assert spec.material.name == "FR4"


def test_default_frequency():
    spec = parse_natural_language("patch antenna on FR4")
    assert spec.frequency.center_ghz == 2.4
