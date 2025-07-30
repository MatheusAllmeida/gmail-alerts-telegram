import os
from dotenv import load_dotenv
import pickle
import base64
import re
import requests
import time
import schedule
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv('variaveis.env')

# ========== CONFIGURAÇÕES ==========
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
GMAIL_LABEL = os.getenv('GMAIL_LABEL')
BOT_TOKEN = os.getenv('BOT_TOKEN')

CHAT_ID = int(os.getenv('CHAT_ID'))
PROCESSED_FILE = 'processados.txt'

# ========== AUTENTICAÇÃO ==========
def autenticar_gmail():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# ========== ARQUIVO DE CONTROLE ==========
def carregar_processados():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def salvar_processado(chave):
    with open(PROCESSED_FILE, 'a') as f:
        f.write(chave + '\n')

def ja_foi_processado(seq_ba, status):
    """Verifica se uma combinação SEQ_BA + STATUS já foi processada"""
    processados = carregar_processados()
    chave = f"{seq_ba}|{status}"
    return chave in processados

# ========== TELEGRAM ==========
def enviar_telegram(texto):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': texto,
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    return r.status_code == 200

# ========== GMAIL UTILS ==========
def marcar_como_lido(service, message_id):
    """Marca um email como lido (remove a label UNREAD)"""
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao marcar email como lido: {e}")
        return False

def obter_data_email(mensagem):
    """Extrai a data do email para ordenação"""
    try:
        headers = mensagem['payload'].get('headers', [])
        for header in headers:
            if header['name'].lower() == 'date':
                return header['value']
        # Se não encontrar, usa o internalDate (timestamp)
        return int(mensagem.get('internalDate', 0))
    except:
        return 0

# ========== EXTRAÇÃO DE DADOS COMPLETA ==========
def extrair_dados(html, assunto=''):
    soup = BeautifulSoup(html, 'html.parser')
    
    dados = {
        'seq_ba': '',
        'empresa': '',
        'ba_numero': '',
        'data_anormalidade': '',
        'empresa_ofensora': '',
        'ba_numero_ofensora': '',
        'data_acionamento': '',
        'titulo': '',
        'status': '',
        'motivo_primario': '',
        'motivo_secundario': '',
        'data_hora_solucao': ''
    }

    # Extrair SEQ. BA do assunto
    match_seq = re.search(r'Seq\.? BA: (\d+)', assunto, re.IGNORECASE)
    if match_seq:
        dados['seq_ba'] = match_seq.group(1)

    linhas = soup.find_all('tr')
    
    for i, tr in enumerate(linhas):
        tds = tr.find_all('td')
        if not tds:
            continue

        for j, td in enumerate(tds):
            texto = td.get_text(strip=True)
            texto_lower = texto.lower()
            
            if 'empresa:' in texto_lower and not dados['empresa']:
                for k in range(j+1, len(tds)):
                    valor = tds[k].get_text(strip=True)
                    if valor:
                        dados['empresa'] = valor
                        break
            elif ('ba nº:' in texto_lower or 'ba n°:' in texto_lower) and not dados['ba_numero']:
                for k in range(j+1, len(tds)):
                    valor = tds[k].get_text(strip=True)
                    if valor:
                        dados['ba_numero'] = valor
                        break
            elif 'data anormalidade:' in texto_lower:
                for k in range(j+1, len(tds)):
                    valor = tds[k].get_text(strip=True)
                    if valor:
                        dados['data_anormalidade'] = valor
                        break

    secao_atual = ""
    for tr in linhas:
        if 'DADOS DA EMPRESA OFENSORA' in tr.get_text():
            secao_atual = "ofensora"
            continue
        elif 'DESCRIÇÃO ANORMALIDADE' in tr.get_text():
            secao_atual = "descricao"
            continue
        elif 'MOTIVO RESOLUÇÃO/INDEVIDO' in tr.get_text():
            secao_atual = "motivo"
            continue
            
        tds = tr.find_all('td')
        if not tds:
            continue
            
        for j, td in enumerate(tds):
            texto = td.get_text(strip=True)
            texto_lower = texto.lower()
            
            if secao_atual == "ofensora":
                if 'empresa:' in texto_lower and not dados['empresa_ofensora']:
                    for k in range(j+1, len(tds)):
                        valor = tds[k].get_text(strip=True)
                        if valor:
                            dados['empresa_ofensora'] = valor
                            break
                elif ('ba nº:' in texto_lower or 'ba n°:' in texto_lower) and not dados['ba_numero_ofensora']:
                    for k in range(j+1, len(tds)):
                        valor = tds[k].get_text(strip=True)
                        if valor:
                            dados['ba_numero_ofensora'] = valor
                            break
                elif 'data acionamento:' in texto_lower:
                    for k in range(j+1, len(tds)):
                        valor = tds[k].get_text(strip=True)
                        if valor:
                            dados['data_acionamento'] = valor
                            break
            
            elif secao_atual == "descricao":
                if 'título:' in texto_lower and not dados['titulo']:
                    for k in range(j+1, len(tds)):
                        valor = tds[k].get_text(strip=True)
                        if valor:
                            dados['titulo'] = valor
                            break
                elif 'status:' in texto_lower and not dados['status']:
                    for k in range(j+1, len(tds)):
                        valor = tds[k].get_text(strip=True)
                        if valor:
                            dados['status'] = valor
                            break
            
            elif secao_atual == "motivo":
                if 'motivo primário:' in texto_lower:
                    match = re.search(r'motivo primário:\s*(.+?)(?:<br>|motivo secundário|$)', texto, re.IGNORECASE | re.DOTALL)
                    if match:
                        dados['motivo_primario'] = match.group(1).strip()
                if 'motivo secundário:' in texto_lower:
                    match = re.search(r'motivo secundário:\s*(.+?)$', texto, re.IGNORECASE | re.DOTALL)
                    if match:
                        dados['motivo_secundario'] = match.group(1).strip()

            if 'data/hora da solução:' in texto_lower:
                for k in range(j+1, len(tds)):
                    valor = tds[k].get_text(strip=True)
                    if valor:
                        if not dados['data_hora_solucao']:
                            dados['data_hora_solucao'] = valor
                        else:
                            dados['data_hora_solucao'] += ' ' + valor
                        if k < len(tds) - 1:
                            prox_valor = tds[k+1].get_text(strip=True)
                            if prox_valor and ':' in prox_valor:
                                dados['data_hora_solucao'] += ' ' + prox_valor
                        break

    for key in dados:
        if isinstance(dados[key], str):
            dados[key] = dados[key].replace('\n', ' ').replace('\r', '').strip()
            dados[key] = re.sub(r'&[^;]+;', '', dados[key])
    
    print("Dados extraídos:")
    for key, value in dados.items():
        print(f"  {key}: {value}")
    
    return dados

# ========== FORMATAÇÃO DA MENSAGEM ==========
def formatar_mensagem(dados):
    texto = f"""📌 <b>SEQ. BA:</b> {dados.get('seq_ba', 'N/A')}

📌 <b>DADOS DA EMPRESA</b>
🏢 Empresa: {dados.get('empresa', 'N/A')}
📄 BA Nº: {dados.get('ba_numero', 'N/A')}
📅 Data Anormalidade: {dados.get('data_anormalidade', 'N/A')}

🔍 <b>DADOS DA EMPRESA OFENSORA</b>
🏢 Empresa: {dados.get('empresa_ofensora', 'N/A')}
📄 BA Nº: {dados.get('ba_numero_ofensora', 'N/A')}
📅 Data Acionamento: {dados.get('data_acionamento', 'N/A')}

📋 <b>DESCRIÇÃO ANORMALIDADE</b>
📝 Título: {dados.get('titulo', 'N/A')}
⚙️ Status: {dados.get('status', 'N/A')}

❗ <b>MOTIVO RESOLUÇÃO</b>
🎯 Primário: {dados.get('motivo_primario', 'N/A')}
🎯 Secundário: {dados.get('motivo_secundario', 'N/A')}

🕐 <b>Data/Hora da Solução:</b> {dados.get('data_hora_solucao', 'N/A')}"""
    
    return texto

# ========== PROCESSAMENTO ==========
def processar_emails():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de emails...")
    
    try:
        service = autenticar_gmail()
        
        # Busca emails não lidos com a label específica
        resultados = service.users().messages().list(
            userId='me', 
            labelIds=[GMAIL_LABEL], 
            q='is:unread'
        ).execute()
        
        mensagens = resultados.get('messages', [])

        if not mensagens:
            print("✅ Nenhum e-mail novo encontrado.")
            # Envia mensagem para o Telegram informando que não há novos e-mails
            mensagem_sem_email = "🔍 <b>Verificação de E-mails</b>\n\nNenhum novo e-mail encontrado na última verificação."
            enviar_telegram(mensagem_sem_email)
            return

        print(f"📧 {len(mensagens)} mensagens encontradas")

        # Busca os dados completos de cada mensagem para ordenação
        mensagens_completas = []
        for msg in mensagens:
            try:
                mensagem_completa = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='full'
                ).execute()
                mensagens_completas.append(mensagem_completa)
            except Exception as e:
                print(f"❌ Erro ao buscar mensagem {msg['id']}: {e}")
                continue

        # Ordena por data (mais antigo primeiro)
        mensagens_completas.sort(key=lambda x: int(x.get('internalDate', 0)))
        
        print(f"📋 Processando {len(mensagens_completas)} emails do mais antigo para o novo...")

        emails_processados = 0
        
        for mensagem in mensagens_completas:
            msg_id = mensagem['id']
            print(f"\n🔄 Processando mensagem: {msg_id}")

            try:
                # (1) Pega o assunto do e-mail
                assunto = ''
                for header in mensagem.get('payload', {}).get('headers', []):
                    if header['name'].lower() == 'subject':
                        assunto = header['value']
                        break

                # Verifica se tem partes HTML
                partes = mensagem['payload'].get('parts', [])
                
                # Se não tem partes, verifica o payload principal
                if not partes and mensagem['payload'].get('body', {}).get('data'):
                    partes = [mensagem['payload']]

                html_encontrado = False
                email_processado_com_sucesso = False
                
                for parte in partes:
                    if parte.get('mimeType') == 'text/html' and parte.get('body', {}).get('data'):
                        try:
                            html = base64.urlsafe_b64decode(parte['body']['data']).decode('utf-8')
                            html_encontrado = True
                            
                            print("✅ Conteúdo HTML encontrado")

                            # (2) Extrai os dados com base no assunto
                            dados = extrair_dados(html, assunto)

                            if dados and dados.get('ba_numero'):
                                seq_ba = dados.get('seq_ba', '') or dados.get('ba_numero', '')
                                status = dados.get('status', '')
                                
                                print(f"📄 SEQ BA: {seq_ba} | Status: {status}")
                                
                                # Verifica se já foi processado
                                if not ja_foi_processado(seq_ba, status):
                                    texto = formatar_mensagem(dados)
                                    
                                    # Envia para o Telegram
                                    if len(texto) > 4000:
                                        # Divide mensagem se for muito longa
                                        partes_msg = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
                                        sucesso_total = True
                                        
                                        for idx, parte_msg in enumerate(partes_msg):
                                            print(f"📤 Enviando parte {idx+1}/{len(partes_msg)}")
                                            if not enviar_telegram(parte_msg):
                                                print(f"❌ Falha ao enviar parte {idx+1}")
                                                sucesso_total = False
                                                break
                                            time.sleep(1)  # Evita rate limit
                                        
                                        if sucesso_total:
                                            chave = f"{seq_ba}|{status}"
                                            salvar_processado(chave)
                                            emails_processados += 1
                                            email_processado_com_sucesso = True
                                            print(f"✅ Email processado e salvo: {chave}")
                                        
                                    else:
                                        if enviar_telegram(texto):
                                            chave = f"{seq_ba}|{status}"
                                            salvar_processado(chave)
                                            emails_processados += 1
                                            email_processado_com_sucesso = True
                                            print(f"✅ Email processado e salvo: {chave}")
                                        else:
                                            print("❌ Falha ao enviar mensagem")
                                else:
                                    print(f"⏭️ Email já processado: {seq_ba}|{status}")
                                    email_processado_com_sucesso = True  # Marca como processado mesmo sendo duplicado
                            else:
                                print("⚠️ Não foi possível extrair dados suficientes")
                                email_processado_com_sucesso = True  # Marca como lido mesmo sem dados válidos
                                
                        except Exception as e:
                            print(f"❌ Erro ao processar HTML: {e}")
                            email_processado_com_sucesso = True  # Marca como lido mesmo com erro
                            
                        break  # Sai do loop de partes após processar HTML
                
                if not html_encontrado:
                    print("⚠️ Nenhum conteúdo HTML encontrado neste email")
                    email_processado_com_sucesso = True  # Marca como lido mesmo sem HTML
                
                # Marca o email como lido após processamento (sucesso ou falha)
                if email_processado_com_sucesso:
                    if marcar_como_lido(service, msg_id):
                        print("📖 Email marcado como lido")
                    else:
                        print("⚠️ Falha ao marcar email como lido")
                    
            except Exception as e:
                print(f"❌ Erro ao processar mensagem {msg_id}: {e}")
                # Mesmo com erro, marca como lido para evitar reprocessamento
                marcar_como_lido(service, msg_id)
                continue

        print(f"\n📊 Resumo: {emails_processados} emails novos processados")
        
    except Exception as e:
        print(f"❌ Erro geral no processamento: {e}")

# ========== AGENDAMENTO ==========
def executar_monitoramento():
    """Executa o monitoramento contínuo de emails"""
    print("🚀 Iniciando monitoramento de emails...")
    print("⏰ Verificações a cada 30 minutos")
    print("🛑 Para parar, pressione Ctrl+C\n")
    
    # Agenda a execução a cada 30 minutos
    schedule.every(30).minutes.do(processar_emails)
    
    # Executa uma vez imediatamente
    processar_emails()
    
    # Loop principal
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto se há tarefas agendadas
    except KeyboardInterrupt:
        print("\n🛑 Monitoramento interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no monitoramento: {e}")

# ========== EXECUÇÃO ==========
if __name__ == '__main__':
    executar_monitoramento()