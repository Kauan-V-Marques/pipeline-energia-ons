import io
from datetime import date

import pytest

from pipeline import extrair, feriados


@pytest.mark.parametrize(
    ("ano", "esperado"),
    [
        (2016, date(2016, 3, 27)),
        (2019, date(2019, 4, 21)),
        (2024, date(2024, 3, 31)),
        (2025, date(2025, 4, 20)),
    ],
)
def test_pascoa(ano, esperado):
    assert feriados.pascoa(ano) == esperado


def test_feriados_moveis_dependem_da_pascoa():
    lista = {nome: data for data, nome, _ in feriados.feriados(2025)}

    assert lista["Carnaval (terça)"] == date(2025, 3, 4)
    assert lista["Sexta-feira Santa"] == date(2025, 4, 18)
    assert lista["Corpus Christi"] == date(2025, 6, 19)


def test_consciencia_negra_so_vira_feriado_nacional_em_2024():
    nomes = lambda ano: {nome for _, nome, _ in feriados.feriados(ano)}  # noqa: E731

    assert "Consciência Negra" not in nomes(2023)
    assert "Consciência Negra" in nomes(2024)


def test_seed_de_feriados(tmp_path):
    destino = tmp_path / "feriados.csv"

    total = feriados.gerar_seed(range(2016, 2026), destino)

    linhas = destino.read_text(encoding="utf-8").splitlines()
    assert linhas[0] == "data,nome,tipo"
    assert len(linhas) == total + 1
    assert total == 10 * 12 + 2  # 12 por ano + Consciência Negra em 2024 e 2025


CSV_OK = "\n".join([extrair.COLUNAS_ESPERADAS, "N;NORTE;2024-01-01 00:00:00;6539.56", ""]).encode()


class ServidorFalso:
    def __init__(self, conteudo: bytes):
        self.conteudo = conteudo
        self.urls: list[str] = []

    def __call__(self, url, timeout):
        self.urls.append(url)
        return io.BytesIO(self.conteudo)


def test_baixa_o_ano_e_confere_o_cabecalho(tmp_path):
    servidor = ServidorFalso(CSV_OK)

    destino = extrair.baixar_ano(2024, tmp_path, abrir=servidor)

    assert destino.read_bytes() == CSV_OK
    assert servidor.urls == [extrair.URL.format(ano=2024)]
    assert not list(tmp_path.glob("*.parcial"))


def test_nao_baixa_de_novo_o_que_ja_existe(tmp_path):
    (tmp_path / "CURVA_CARGA_2024.csv").write_bytes(CSV_OK)
    servidor = ServidorFalso(CSV_OK)

    extrair.baixar_ano(2024, tmp_path, abrir=servidor)

    assert servidor.urls == []


def test_layout_diferente_interrompe_sem_deixar_arquivo(tmp_path):
    servidor = ServidorFalso(b"coluna_nova;outra\n1;2\n")

    with pytest.raises(ValueError, match="mudou o layout"):
        extrair.baixar_ano(2024, tmp_path, abrir=servidor)

    assert list(tmp_path.iterdir()) == []
