"""Normalizacao de nomes com suporte a aliases e RapidFuzz."""

import json
from pathlib import Path


def load_aliases() -> dict:
    alias_path = Path(__file__).with_name("aliases.json")
    return json.loads(alias_path.read_text(encoding="utf-8"))


def main() -> None:
    aliases = load_aliases()
    print(f"Aliases carregados: {len(aliases)} marcas")


if __name__ == "__main__":
    main()
