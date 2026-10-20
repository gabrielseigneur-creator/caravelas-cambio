# caravelas-cambio (piloto)

Robô sem IA (GitHub Actions) que, em dias úteis às 08:17 de São Paulo, busca a PTAX
(BCB, USD/BRL) e a taxa de referência do BCE (EUR/USD) e grava `dados/latest.json`.
Os agentes do Claude leem esse arquivo em vez de pesquisar o câmbio na web.

Só dados públicos; nenhuma credencial. Os valores em `tests/` são ilustrativos
(só testam a leitura do formato), não são cotações reais.

Leitura pelos agentes: `https://raw.githubusercontent.com/<dono>/caravelas-cambio/main/dados/latest.json`
