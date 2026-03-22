"""Extrai a whitelist da LARC ITTF e gera `larc_whitelist.json`."""

from pathlib import Path


def main() -> None:
    output_path = Path("data/raw/larc_whitelist.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not output_path.exists():
        output_path.write_text("[]", encoding="utf-8")

    print(f"Arquivo preparado em {output_path}")


if __name__ == "__main__":
    main()
