"""Extração: baixa a curva de carga horária do bucket público do ONS (licença CC-BY)."""

import logging
import urllib.request
from pathlib import Path

log = logging.getLogger("pipeline.extrair")

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/curva-carga-ho/CURVA_CARGA_{ano}.csv"
COLUNAS_ESPERADAS = "id_subsistema;nom_subsistema;din_instante;val_cargaenergiahomwmed"


def baixar_ano(ano: int, pasta: Path, forcar: bool = False, abrir=urllib.request.urlopen) -> Path:
    """Baixa um ano (pula se já existe, a não ser que forcar=True) e confere o cabeçalho."""
    destino = pasta / f"CURVA_CARGA_{ano}.csv"
    if destino.exists() and not forcar:
        log.info("%s já existe, pulando", destino.name)
        return destino

    pasta.mkdir(parents=True, exist_ok=True)
    with abrir(URL.format(ano=ano), timeout=60) as resposta:
        conteudo = resposta.read()

    cabecalho = conteudo.decode("utf-8-sig").splitlines()[0].strip()
    if cabecalho != COLUNAS_ESPERADAS:
        raise ValueError(f"Formato inesperado em {ano}: {cabecalho!r}. O ONS mudou o layout?")

    # Grava em um temporário e renomeia: um download interrompido não deixa arquivo pela metade
    temporario = destino.with_suffix(".parcial")
    temporario.write_bytes(conteudo)
    temporario.replace(destino)
    log.info("%s baixado (%.1f MB)", destino.name, len(conteudo) / 1e6)
    return destino


def extrair(anos: range, pasta: Path, forcar_ultimo: bool = True) -> list[Path]:
    """O ano mais recente é sempre baixado de novo, porque o ONS continua atualizando."""
    return [baixar_ano(ano, pasta, forcar=forcar_ultimo and ano == anos[-1]) for ano in anos]
