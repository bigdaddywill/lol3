from tools.swarm_protocol import MESSAGE_TYPES, validate_structure


def test_message_types_are_present():
    assert "TASK" in MESSAGE_TYPES
    assert "RESULT" in MESSAGE_TYPES
    assert "CHALLENGE" in MESSAGE_TYPES
    assert "CHECKPOINT" in MESSAGE_TYPES


def test_swarm_structure_exists():
    assert validate_structure() == []
