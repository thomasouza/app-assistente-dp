# helpers.py - Versão Final com a função load_css incluída

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime
import json

# --- FUNÇÃO QUE ESTAVA FALTANDO ---
def load_css(file_name):
    """Carrega um arquivo CSS local para dentro do app Streamlit."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo '{file_name}' não encontrado. Verifique se ele foi enviado para o GitHub.")


# --- CONFIGURAÇÃO DAS CREDENCIAIS VIA STREAMLIT SECRETS ---
try:
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

# E SUBSTITUA por este novo bloco:

# A única mudança é nesta primeira linha, adicionando o (ttl=600)
@st.cache_data(ttl=600)
def carregar_acessos():
    """Carrega os dados da planilha de acessos, com cache que expira a cada 10 minutos."""
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

# Em helpers.py, adicione esta nova função:

@st.cache_data(ttl=600) # Cache para não recarregar a lista toda hora
def carregar_empresas():
    """Carrega a lista de empresas da planilha."""
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open("ACESSOS_ASSISTENTE_DP") # Ou o nome da planilha onde você criou a aba
            worksheet = spreadsheet.worksheet("EMPRESAS") # Abre a aba específica "EMPRESAS"
            # Pega todos os valores da primeira coluna, exceto o cabeçalho
            lista_empresas = worksheet.col_values(1)[1:] 
            return lista_empresas
        except gspread.exceptions.WorksheetNotFound:
            st.error("Aba 'EMPRESAS' não encontrada na planilha. Por favor, crie-a.")
            return []
        except Exception as e:
            st.error("Não foi possível carregar a lista de empresas.")
            print(f"Erro ao carregar empresas: {e}")
            return []
    return []

# Não se esqueça de importar a nova função nos arquivos que a usarão.
# Em 3_Chat_com_Agentes.py, o import ficará:
# from helpers import load_css, carregar_base_conhecimento, salvar_log, get_gemini_model, carregar_empresas

def salvar_log(matricula_dp, nome_colaborador, empresa, pergunta, resposta, avaliacao, comentario):
    """Salva um registro completo do atendimento, incluindo o feedback, na planilha de logs."""
    client = get_gspread_client()
    if client:
        try:
            log_spreadsheet = client.open("LOGS_DE_CONVERSA_DP")
            log_worksheet = log_spreadsheet.get_worksheet(0)
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # Nova linha com as informações de avaliação
            nova_linha = [timestamp, matricula_dp, nome_colaborador, empresa, pergunta, resposta, avaliacao, comentario]
            
            log_worksheet.append_row(nova_linha)
            return True
        except Exception as e:
            print(f"Erro ao salvar log: {e}")
            return False
    return False



def verificar_login(matricula, senha, df_acessos):
    if df_acessos is not None and not df_acessos.empty:
        usuario = df_acessos[df_acessos['Matrícula_Colaborador'] == matricula]
        if not usuario.empty and usuario.iloc[0]['Senha'] == senha:
            return True
    return False
