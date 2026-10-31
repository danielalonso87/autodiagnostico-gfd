"""
Converte a chave JSON da conta de serviço do Google no bloco [gcp_service_account]
do secrets.toml, sem precisar copiar campo por campo.

Uso:
    python ferramentas/json_para_secrets.py C:\\Users\\daniel\\Downloads\\minha-chave.json

Copie a saída e cole no final de .streamlit/secrets.toml (e nos Secrets do Streamlit Cloud).
"""

import json
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        chave = json.load(f)
    print("[gcp_service_account]")
    for campo, valor in chave.items():
        # json.dumps gera string com escapes compatíveis com TOML (\n na private_key)
        print(f"{campo} = {json.dumps(valor, ensure_ascii=False)}")
    print(f"\n# Compartilhe a planilha (como Editor) com: {chave.get('client_email')}", file=sys.stderr)


if __name__ == "__main__":
    main()
