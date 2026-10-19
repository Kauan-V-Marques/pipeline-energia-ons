"""Roda o pipeline inteiro: python -m pipeline [--inicio 2016 --fim 2025]

1. extrai os CSV do ONS
2. gera o calendário de feriados (seed do dbt)
3. dbt build: modelos + testes de qualidade
4. exporta as tabelas para o Power BI (Parquet)
5. gera o relatório web
"""

import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path

from pipeline import exportar, extrair, feriados, relatorio

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ / "dados" / "raw"
BANCO = RAIZ / "dados" / "energia.duckdb"


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inicio", type=int, default=2016)
    parser.add_argument("--fim", type=int, default=date.today().year - 1, help="último ano completo")
    parser.add_argument("--sem-download", action="store_true")
    args = parser.parse_args(argv)
    anos = range(args.inicio, args.fim + 1)

    if not args.sem_download:
        extrair.extrair(anos, PASTA_RAW)
    feriados.gerar_seed(anos, RAIZ / "dbt" / "seeds" / "feriados.csv")

    comando = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "build",
        "--project-dir",
        str(RAIZ / "dbt"),
        "--profiles-dir",
        str(RAIZ / "dbt"),
        "--vars",
        f"{{ano_inicio: {args.inicio}, ano_fim: {args.fim}}}",
    ]
    subprocess.run(comando, check=True, cwd=RAIZ / "dbt")

    exportar.exportar(BANCO, RAIZ / "powerbi" / "dados")
    relatorio.gerar(BANCO, RAIZ / "site" / "index.html")
    logging.getLogger("pipeline").info("Pronto: powerbi/dados/ e site/index.html atualizados")


if __name__ == "__main__":
    main()
