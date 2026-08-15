"""Tests for comparer_mcp.part_matcher."""

from music21 import instrument, stream

from comparer_mcp.part_matcher import match_parts


def _part(part_id, name, instr=None):
    p = stream.Part(id=part_id)
    p.partName = name
    if instr is not None:
        p.insert(0, instr)
    return p


class TestMatchByName:
    def test_exact_name_match(self):
        ref = [_part("P1", "Soprano"), _part("P2", "Alto")]
        tgt = [_part("Q1", "Soprano"), _part("Q2", "Alto")]

        result = match_parts(ref, tgt)

        assert len(result.matched) == 2
        assert result.matched[0][0].id == "P1"
        assert result.matched[0][1].id == "Q1"
        assert result.matched[1][0].id == "P2"
        assert result.matched[1][1].id == "Q2"
        assert result.missing == []
        assert result.extra == []

    def test_name_match_is_case_insensitive(self):
        ref = [_part("P1", "Soprano")]
        tgt = [_part("Q1", "SOPRANO")]

        result = match_parts(ref, tgt)

        assert len(result.matched) == 1

    def test_name_match_out_of_order(self):
        ref = [_part("P1", "Soprano"), _part("P2", "Bass")]
        tgt = [_part("Q1", "Bass"), _part("Q2", "Soprano")]

        result = match_parts(ref, tgt)

        pairs = {(r.id, t.id) for r, t in result.matched}
        assert pairs == {("P1", "Q2"), ("P2", "Q1")}


class TestMatchByPositionFallback:
    def test_falls_back_to_position_when_no_name_match(self):
        ref = [_part("P1", "Voice 1"), _part("P2", "Voice 2")]
        tgt = [_part("Q1", "Part A"), _part("Q2", "Part B")]

        result = match_parts(ref, tgt)

        assert len(result.matched) == 2
        assert result.matched[0] == (ref[0], tgt[0])
        assert result.matched[1] == (ref[1], tgt[1])


class TestMissingAndExtraParts:
    def test_reference_only_part_is_missing(self):
        ref = [_part("P1", "Soprano"), _part("P2", "Alto")]
        tgt = [_part("Q1", "Soprano")]

        result = match_parts(ref, tgt)

        assert len(result.matched) == 1
        assert [p.partName for p in result.missing] == ["Alto"]
        assert result.extra == []

    def test_target_only_part_is_extra(self):
        ref = [_part("P1", "Soprano")]
        tgt = [_part("Q1", "Soprano"), _part("Q2", "Descant")]

        result = match_parts(ref, tgt)

        assert len(result.matched) == 1
        assert result.missing == []
        assert [p.partName for p in result.extra] == ["Descant"]

    def test_empty_target_marks_all_reference_parts_missing(self):
        ref = [_part("P1", "Soprano"), _part("P2", "Alto")]

        result = match_parts(ref, [])

        assert result.matched == []
        assert len(result.missing) == 2
        assert result.extra == []
