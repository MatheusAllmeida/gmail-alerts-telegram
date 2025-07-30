# 📬 Gmail Alerts to Telegram Bot

Este projeto monitora automaticamente e-mails com uma label específica no Gmail e envia notificações formatadas para um grupo ou canal no Telegram, extraindo dados estruturados do conteúdo HTML da mensagem.

---

## 🚀 Funcionalidades

- Autenticação com a API do Gmail (OAuth 2.0)
- Leitura de e-mails não lidos com uma label específica
- Extração de dados (empresa, BA, status, título, etc.)
- Formatação em mensagem HTML para Telegram
- Envio automático para um grupo via Bot do Telegram
- Evita mensagens duplicadas com controle de processamento

---

## 🧩 Estrutura do Repositório


gmail-alerts-telegram/
├── ba_bot.py              # Script principal de monitoramento
├── listar_labels.py       # Lista todas as labels do Gmail
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore             # Arquivos a serem ignorados no versionamento
├── processados.txt        # Controle de mensagens processadas
└── README.md              # Este arquivo

⚙️ Pré-requisitos
Python 3.8+
Conta no Google com acesso à API do Gmail
Bot do Telegram criado e um grupo ou canal com ID

🔐 Variáveis de Ambiente
Crie um arquivo .env (baseado no .env.example) com os seguintes dados:


GMAIL_LABEL=Label_Exemplo
BOT_TOKEN=123456:ABCDEF...
CHAT_ID=-1001234567890
🔧 Instalação
Clone o repositório:


git clone https://github.com/seu-usuario/gmail-alerts-telegram.git
cd gmail-alerts-telegram
Crie um ambiente virtual (opcional mas recomendado):


python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows


🔑 Credenciais do Gmail
Acesse o Google Cloud Console

Crie um projeto e ative a Gmail API
Gere credenciais do tipo OAuth 2.0 Client ID (Desktop)
Salve como credentials.json na raiz do projeto
Ao rodar o script pela primeira vez, será gerado um token.pickle após login

📌 Uso
1. Ver labels disponíveis

python listar_labels.py
Use o nome da label retornado no .env.

2. Iniciar o monitoramento
python ba_bot.py
O script processa e-mails não lidos com a label definida, extrai os dados e envia ao Telegram. Ele roda em loop, checando a cada 30 minutos.


📄 Licença
Este projeto está licenciado sob a MIT License.
