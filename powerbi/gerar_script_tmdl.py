"""Gera o script para colar na Exibição TMDL do Power BI Desktop a partir da pasta do modelo.

python powerbi/gerar_script_tmdl.py  ->  powerbi/script-tmdl-view.tmdl
"""

from pathlib import Path

PASTA = Path(__file__).parent / "EnergiaONS.SemanticModel" / "definition"
arquivos = [
    PASTA / "expressions.tmdl",
    *sorted((PASTA / "tables").glob("*.tmdl")),
    PASTA / "relationships.tmdl",
]

blocos = []
for arquivo in arquivos:
    linhas = arquivo.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n").split("\n")
    blocos.append("\n".join(("\t" + linha) if linha.strip() else "" for linha in linhas))

script = "createOrReplace\n\n" + "\n\n".join(blocos) + "\n"
destino = Path(__file__).parent / "script-tmdl-view.tmdl"
destino.write_text(script, encoding="utf-8", newline="\n")
print(f"{destino.name}: {script.count(chr(10))} linhas")
