# helpers.py - Versão Final para Deploy com st.secrets

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÃO DAS CREDENCIAIS VIA STREAMLIT SECRETS ---
try:
    # Pega as credenciais e chaves diretamente dos Secrets que você configurou no Streamlit Cloud
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GSPREAD_CREDENTIALS_DICT = st.secrets["gspread_credentials"]
except KeyError as e:
    st.error(f"Erro: Credencial '{e.args[0]}' não encontrada nos Secrets do Streamlit. Verifique a configuração no painel do seu app.")
    st.stop()
    
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- FUNÇÕES ---

def get_gspread_client():
    """Usa as credenciais dos Secrets para autorizar e retornar um cliente gspread."""
    try:
        creds = Credentials.from_service_account_info(GSPREAD_CREDENTIALS_DICT, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error("Falha na autorização com as credenciais do Google Sheets.")
        print(f"Erro de autorização GSpread: {e}")
        return None

def get_gemini_model():
    """Configura e retorna o modelo de IA do Gemini."""
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error("Falha ao configurar a API do Gemini. Verifique sua chave de API nos Secrets.")
        print(f"Erro de configuração Gemini: {e}")
        return None

# Funções que usam o cliente autorizado
@st.cache_data
def carregar_base_conhecimento():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("BASE_DE_CONHECIMENTO_DP")
            abas = {worksheet.title: pd.DataFrame(worksheet.get_all_records()) for worksheet in spreadsheet.worksheets()}
            return abas
        except Exception as e:
            st.error("Não foi possível abrir a planilha 'BASE_DE_CONHECIMENTO_DP'. Verifique o nome e as permissões de compartilhamento.")
            print(f"Erro ao carregar base de conhecimento: {e}")
    return None

@st.cache_data
def carregar_acessos():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("ACESSOS_ASSISTENTE_DP")
            worksheet = spreadsheet.get_worksheet(0)
            df = pd.DataFrame(worksheet.get_all_records())
            if 'Senha' in df.columns:
                df['Senha'] = df['Senha'].astype(str)
            return df
        except Exception as e:
            st.error("Não foi possível abrir a planilha 'ACESSOS_ASSISTENTE_DP'. Verifique o nome e as permissões de compartilhamento.")
            print(f"Erro ao carregar acessos: {e}")
    return None

def salvar_log(matricula, pergunta, resposta):
    client = get_gspread_client()
    if client:
        try:
            log_spreadsheet = client.open("LOGS_DE_CONVERSA_DP")
            log_worksheet = log_spreadsheet.get_worksheet(0)
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            nova_linha = [timestamp, matricula, pergunta, resposta]
            log_worksheet.append_row(nova_linha)
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

def verificar_login(matricula, senha, df_acessos):
    if df_acessos is not None and not df_acessos.empty:
        usuario = df_acessos[df_acessos['Matrícula_Colaborador'] == matricula]
        if not usuario.empty and usuario.iloc[0]['Senha'] == senha:
            return True
    return False
