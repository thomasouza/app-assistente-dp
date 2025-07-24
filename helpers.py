import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime
import json

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo '{file_name}' não encontrado.")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GSPREAD_CREDENTIALS_DICT = st.secrets["gspread_credentials"]
except KeyError as e:
    st.error(f"Erro: Credencial '{e.args[0]}' não encontrada nos Secrets do Streamlit.")
    st.stop()
    
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_gspread_client():
    creds = Credentials.from_service_account_info(GSPREAD_CREDENTIALS_DICT, scopes=SCOPES)
    return gspread.authorize(creds)

def get_gemini_model():
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel('gemini-1.5-flash')

@st.cache_data(ttl=300)
def carregar_base_conhecimento():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("BASE_DE_CONHECIMENTO_DP")
            abas = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
            return abas
        except Exception as e:
            print(f"Erro ao carregar base de conhecimento: {e}")
    return None

@st.cache_data(ttl=600)
def carregar_acessos():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("ACESSOS_ASSISTENTE_DP")
            df = pd.DataFrame(spreadsheet.get_worksheet(0).get_all_records())
            if 'Senha' in df.columns:
                df['Senha'] = df['Senha'].astype(str)
            return df
        except Exception as e:
            print(f"Erro ao carregar acessos: {e}")
    return None

def salvar_log(matricula_dp, nome_colaborador, empresa, pergunta, resposta, avaliacao, comentario):
    client = get_gspread_client()
    if client:
        try:
            log_sheet = client.open("LOGS_DE_CONVERSA_DP").get_worksheet(0)
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            nova_linha = [timestamp, matricula_dp, nome_colaborador, empresa, pergunta, resposta, avaliacao, comentario]
            log_sheet.append_row(nova_linha)
            return True
        except Exception as e:
            print(f"Erro ao salvar log: {e}")
    return False

def salvar_aprendizado(assunto, pergunta, resposta_ia, comentario_humano):
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("BASE_DE_CONHECIMENTO_DP")
            worksheet = spreadsheet.worksheet("Feedback_Aprendizado")
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            nova_linha = [timestamp, assunto, pergunta, resposta_ia, comentario_humano]
            worksheet.append_row(nova_linha)
            return True
        except Exception as e:
            print(f"Erro ao salvar aprendizado: {e}")
    return False

def verificar_login(matricula, senha, df_acessos):
    if df_acessos is not None and not df_acessos.empty:
        usuario = df_acessos[df_acessos['Matrícula_Colaborador'] == matricula]
        if not usuario.empty and usuario.iloc[0]['Senha'] == senha:
            return True
    return False

@st.cache_data(ttl=600)
def carregar_empresas():
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("ACESSOS_ASSISTENTE_DP")
            worksheet = spreadsheet.worksheet("EMPRESAS")
            return worksheet.col_values(1)[1:]
        except Exception as e:
            print(f"Erro ao carregar empresas: {e}")
            return []
    return []