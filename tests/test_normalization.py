from conciliador.normalization import is_masked_cpf, normalize_name


class TestNormalizeName:
    def test_accents_and_preposition(self):
        assert normalize_name("João Pedro da Silva") == "JOAO PEDRO SILVA"

    def test_accents_conceicao(self):
        assert normalize_name("Maria da Conceição Ribeiro") == "MARIA CONCEICAO RIBEIRO"

    def test_accent_patricia(self):
        assert normalize_name("Patrícia Gomes") == "PATRICIA GOMES"

    def test_no_change_needed(self):
        assert normalize_name("Eduardo Santos") == "EDUARDO SANTOS"

    def test_preposition_dos(self):
        assert normalize_name("EDUARDO DOS SANTOS PEREIRA") == "EDUARDO SANTOS PEREIRA"

    def test_accent_vinicius(self):
        assert normalize_name("Vinícius Araújo") == "VINICIUS ARAUJO"

    def test_accent_thais(self):
        assert normalize_name("Thaís Nogueira") == "THAIS NOGUEIRA"

    def test_already_uppercase(self):
        assert normalize_name("MARIANA ALVES COSTA") == "MARIANA ALVES COSTA"

    def test_empty(self):
        assert normalize_name("") == ""

    def test_extra_spaces(self):
        assert normalize_name("  Ana   Beatriz   Rocha  ") == "ANA BEATRIZ ROCHA"

    def test_multiple_prepositions(self):
        assert normalize_name("Maria de Jesus das Dores") == "MARIA JESUS DORES"


class TestIsMaskedCpf:
    def test_masked_cpf(self):
        assert is_masked_cpf("CPF ***.482.917-**") is True

    def test_normal_name(self):
        assert is_masked_cpf("MARIANA ALVES COSTA") is False

    def test_empty(self):
        assert is_masked_cpf("") is False
