"""Exporta o modelo estrela em Parquet para o Power BI (lido direto do GitHub)."""

from pathlib import Path

import duckdb

TABELAS = ["fato_carga_horaria", "dim_calendario", "dim_subsistema"]


def exportar(banco: Path, pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = []
    with duckdb.connect(str(banco), read_only=True) as conn:
        for tabela in TABELAS:
            destino = pasta / f"{tabela}.parquet"
            conn.execute(
                f"COPY (SELECT * FROM main_marts.{tabela}) TO '{destino.as_posix()}' "
                "(FORMAT parquet, COMPRESSION zstd)"
            )
            arquivos.append(destino)
    return arquivos
