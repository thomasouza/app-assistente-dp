import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime

# --- CONSTANTES ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENCIAL_JSON = 'google_credentials.json'

# Chave de API - Segurança: ideal carregar via secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "SUA_CHAVE_FALLBACK")  # Atualize ou use secrets.toml

# Nomes de planilhas
NOME_PLANILHA_CONHECIMENTO = "BASE_DE_CONHECIMENTO_DP"
NOME_PLANILHA_ACESSOS = "ACESSOS_ASSISTENTE_DP"
NOME_PLANILHA_LOGS = "LOGS_DE_CONVERSA_DP"


# --- AUTENTICAÇÃO ---
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_file(CREDENCIAL_JSON, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("Erro na autenticação com Google Sheets.")
        st.exception(e)
        return None


# --- FUNÇÕES DE DADOS ---
@st.cache_data
def carregar_base_conhecimento():
    try:
        client = get_gspread_client()
        spreadsheet = client.open(NOME_PLANILHA_CONHECIMENTO)
        abas = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
        return abas
    except Exception as e:
        st.error("Erro ao carregar base de conhecimento.")
        st.exception(e)
        return None

@st.cache_data
def carregar_acessos():
    try:
        client = get_gspread_client()
        worksheet = client.open(NOME_PLANILHA_ACESSOS).get_worksheet(0)
        df = pd.DataFrame(worksheet.get_all_records())
        if 'Senha' in df.columns:
            df['Senha'] = df['Senha'].astype(str)
        return df
    except Exception as e:
        st.error("Erro ao carregar planilha de acessos.")
        st.exception(e)
        return None


def salvar_log(matricula, pergunta, resposta):
    try:
        client = get_gspread_client()
        log_worksheet = client.open(NOME_PLANILHA_LOGS).get_worksheet(0)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_linha = [timestamp, matricula, pergunta, resposta]
        log_worksheet.append_row(nova_linha)
    except Exception as e:
        print(f"[LOG ERRO] Falha ao salvar log: {e}")


# --- GEMINI MODEL ---
def get_gemini_model():
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error("Erro ao configurar modelo da Google AI.")
        st.exception(e)
        return None


# --- LOGIN ---
def verificar_login(matricula, senha, df_acessos):
    if df_acessos is not None and not df_acessos.empty:
        usuario = df_acessos[df_acessos['Matrícula_Colaborador'] == matricula]
        if not usuario.empty and usuario.iloc[0]['Senha'] == senha:
            return True
    return False


# --- CSS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo {file_name} não encontrado.")
