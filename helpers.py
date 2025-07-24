import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime

# --- FUNÇÃO PARA CARREGAR CSS ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo '{file_name}' não encontrado.")

# --- CONFIGURAÇÃO DAS CREDENCIAIS VIA STREAMLIT SECRETS ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GSPREAD_CREDENTIALS_DICT = st.secrets["gspread_credentials"]
except KeyError as e:
    st.error(f"Erro: Credencial '{e.args[0]}' não encontrada nos Secrets do Streamlit.")
    st.stop()
    
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- FUNÇÕES DE CONEXÃO ---
def get_gspread_client():
    creds = Credentials.from_service_account_info(GSPREAD_CREDENTIALS_DICT, scopes=SCOPES)
    return gspread.authorize(creds)

def get_gemini_model():
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel('gemini-1.5-flash')

@st.cache_data(ttl=300)
def carregar_base_conhecimento():
    # ... (código da função permanece o mesmo)
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("BASE_DE_CONHECIMENTO_DP")
            return {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
        except Exception as e: print(f"Erro ao carregar base: {e}")
    return None

@st.cache_data
def carregar_acessos():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("ACESSOS_ASSISTENTE_DP")
            df = pd.DataFrame(spreadsheet.get_worksheet(0).get_all_records())
            if 'Senha' in df.columns: df['Senha'] = df['Senha'].astype(str)
            return df
        except Exception as e: print(f"Erro ao carregar acessos: {e}")
    return None

def salvar_log(matricula, pergunta, resposta):
    client = get_gspread_client()
    if client:
        try:
            log_sheet = client.open("LOGS_DE_CONVERSA_DP").get_worksheet(0)
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