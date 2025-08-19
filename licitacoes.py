# utils/licitacoes.py
from datetime import datetime, timedelta
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import DEFAULT_QTD

# ================================================
# Função para coletar licitações
# ================================================
def coletar_licitacoes(data_inicial, data_final, uf=None, modalidade=6, limite=DEFAULT_QTD):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    pagina = 1
    todos_dados = []
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": pagina,
        "codigoModalidadeContratacao": modalidade,
    }
    if uf:
        params["uf"] = uf.upper()

    while len(todos_dados) < limite:
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        todos_dados.extend(data.get("data", []))
        if data.get("paginasRestantes") == 0 or len(todos_dados) >= limite:
            break
        params["pagina"] += 1
    return todos_dados[:limite]

# ================================================
# Função para enviar licitações
# ================================================
async def enviar_licitacoes(query, dados):
    for idx, item in enumerate(dados, 1):
        # Seleciona o link correto
        url = item.get("linkSistemaOrigem") or item.get("linkProcessoEletronico")
        if not url:
            numero = item.get("numeroControlePNCP")
            if numero:
                url = f"https://pncp.gov.br/app/editais/{numero}"
            else:
                url = None

        texto = (
            f"📌 {item.get('modalidadeNome', 'Sem modalidade')}\n"
            f"📝 Objeto: {item.get('objetoCompra', 'Sem objeto')}\n"
            f"💰 Valor estimado: R$ {item.get('valorTotalEstimado', 0):,.2f}\n"
            f"🏢 Órgão: {item.get('orgaoEntidade', {}).get('razaoSocial', '-')}\n"
            f"📍 Local: {item.get('unidadeOrgao', {}).get('municipioNome', '')} - "
            f"{item.get('unidadeOrgao', {}).get('ufSigla', '')}\n"
            f"📅 Data publicação: {str(item.get('dataPublicacaoPncp', '')[:10])}\n"
        )

        if url:
            texto += f"🔗 <a href='{url}'>Acessar origem</a>\n"
        else:
            texto += "⚠️ Link de origem indisponível\n"

        texto += "----------------------------------------\n\n"

        await query.message.reply_text(texto, parse_mode="HTML")