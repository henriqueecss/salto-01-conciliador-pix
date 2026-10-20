from datetime import datetime

from conciliador.matching import is_within_time_window, name_score


class TestIsWithinTimeWindow:
    def test_8_min_after(self):
        # P001: Pix 09:20, pedido 09:12 → True
        pix = datetime(2026, 10, 13, 9, 20)
        order = datetime(2026, 10, 13, 9, 12)
        assert is_within_time_window(pix, order) is True

    def test_9_min_before(self):
        # P013: Pix 08:41, pedido 08:50 → True (within 2h before)
        pix = datetime(2026, 10, 14, 8, 41)
        order = datetime(2026, 10, 14, 8, 50)
        assert is_within_time_window(pix, order) is True

    def test_next_day_within_48h(self):
        # P011: Pix 08:15 day 14, order 17:30 day 13 → True
        pix = datetime(2026, 10, 14, 8, 15)
        order = datetime(2026, 10, 13, 17, 30)
        assert is_within_time_window(pix, order) is True

    def test_3h_before_order(self):
        pix = datetime(2026, 10, 13, 6, 0)
        order = datetime(2026, 10, 13, 9, 0)
        assert is_within_time_window(pix, order) is False

    def test_exactly_2h_before(self):
        pix = datetime(2026, 10, 13, 7, 0)
        order = datetime(2026, 10, 13, 9, 0)
        assert is_within_time_window(pix, order) is True

    def test_exactly_48h_after(self):
        pix = datetime(2026, 10, 15, 9, 0)
        order = datetime(2026, 10, 13, 9, 0)
        assert is_within_time_window(pix, order) is True

    def test_beyond_48h(self):
        pix = datetime(2026, 10, 15, 9, 1)
        order = datetime(2026, 10, 13, 9, 0)
        assert is_within_time_window(pix, order) is False


class TestNameScore:
    def test_exact_match(self):
        score = name_score("MARIANA ALVES COSTA", "MARIANA ALVES COSTA")
        assert score >= 80

    def test_initial_expansion_p002(self):
        # JOAO P SILVA should expand P to PEDRO when compared to JOAO PEDRO SILVA
        score = name_score("JOAO P SILVA", "JOAO PEDRO SILVA")
        assert score >= 80

    def test_extra_surname_p006(self):
        # Bank has extra surname
        score = name_score("FERNANDA LIMA SOUZA", "FERNANDA LIMA")
        assert score >= 80

    def test_extra_surnames_p016(self):
        # Bank has extra surnames: EDUARDO SANTOS PEREIRA vs EDUARDO SANTOS
        score = name_score("EDUARDO SANTOS PEREIRA", "EDUARDO SANTOS")
        assert score >= 80

    def test_different_person_same_surname_p004(self):
        # Different people: CARLOS EDUARDO ROCHA vs ANA BEATRIZ ROCHA
        score = name_score("CARLOS EDUARDO ROCHA", "ANA BEATRIZ ROCHA")
        assert score < 80

    def test_empty_vs_name(self):
        assert name_score("", "JOAO SILVA") == 0

    def test_both_empty(self):
        assert name_score("", "") == 0

    def test_identical_short(self):
        score = name_score("SOFIA RAMOS", "SOFIA RAMOS")
        assert score >= 80
