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
Crie um arquivo .env na raiz do projeto com as seguintes variáveis (use seus próprios tokens e IDs):

- GMAIL_LABEL=Label_XXXXXXXXXXXX
- BOT_TOKEN=seu_token_do_bot_telegram
- CHAT_ID=seu_chat_id_telegram

Instale as dependências:
pip install -r requirements.txt
Coloque o arquivo credentials.json (credenciais da API Google) na raiz do projeto.

Execute o script:
python seu_script.py

Observações:
O script salva um arquivo processados.txt para evitar envios duplicados.

Desenvolvido por Allmeida
