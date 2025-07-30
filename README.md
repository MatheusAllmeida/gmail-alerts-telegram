# Gmail Alerts Telegram Bot

Este projeto é um bot em Python que monitora emails do Gmail com uma label específica, extrai informações importantes dos emails e envia notificações formatadas para um grupo ou canal no Telegram.

## Funcionalidades

- Autenticação com a API do Gmail para acessar emails.
- Monitoramento contínuo de emails não lidos com uma label definida.
- Extração e formatação de dados importantes do conteúdo HTML dos emails.
- Envio de alertas para Telegram via bot.
- Controle para não enviar notificações duplicadas.

## Tecnologias utilizadas

- Python 3.x
- Google Gmail API
- Telegram Bot API
- BeautifulSoup (para parsing de HTML)
- Schedule (para agendamento de tarefas)
- python-dotenv (para gerenciar variáveis de ambiente)

## Como usar

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/gmail-alerts-telegram.git
   cd gmail-alerts-telegram
