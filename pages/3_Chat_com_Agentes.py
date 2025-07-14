# pages/3_Chat_com_Agentes.py - Versão com Identificação do Chamado

import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model
)

# --- CONFIGURAÇÃO E VERIFICAÇÃO ---
st.set_page_config(layout="centered", initial_sidebar_state="collapsed")
load_css("style.css")

if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

# --- DADOS E MODELO ---
base_conhecimento = carregar_base_conhecimento()
model = get_gemini_model()

# --- TELA PRINCIPAL DA FERRAMENTA ---
st.title("Assistente de Respostas do DP")
st.markdown("Use esta ferramenta para gerar respostas padronizadas e precisas para as dúvidas dos colaboradores.")
st.divider()

# --- NOVIDADE: SEÇÃO DE IDENTIFICAÇÃO DO CHAMADO ---
st.subheader("1. Identificação do Chamado")
col1, col2 = st.columns(2)
with col1:
    colaborador_solicitante = st.text_input("Nome do Colaborador que perguntou:")

with col2:
    empresa_solicitante = st.text_input("Empresa do Colaborador:")

st.divider()

# --- SEÇÃO DE PERGUNTAS E RESPOSTAS ---
st.subheader("2. Dúvida do Colaborador")
if base_conhecimento:
    topicos = list(base_conhecimento.keys())
    agente_selecionado = st.selectbox(
        "Selecione o assunto da dúvida (Agente Especialista):", 
        topicos, 
        index=topicos.index("Geral") if "Geral" in topicos else 0
    )
else:
    agente_selecionado = None

pergunta_colaborador = st.text_area(
    "Copie e cole aqui a pergunta do colaborador:", 
    height=150
)

# --- BOTÃO DE AÇÃO E LÓGICA DA IA ---
if st.button("🤖 Gerar Resposta Sugerida", use_container_width=True, type="primary"):
    # Validações dos campos
    if not colaborador_solicitante or not empresa_solicitante:
        st.warning("Por favor, preencha o Nome e a Empresa do colaborador antes de continuar.")
    elif not pergunta_colaborador:
        st.warning("Por favor, insira a pergunta do colaborador.")
    elif base_conhecimento and model and agente_selecionado:
        with st.spinner("Vivi está pensando na melhor resposta..."):
            try:
                # Lógica da IA para gerar a resposta
                df_topico = base_conhecimento[agente_selecionado]
                contexto = "\n".join([f"P: {row['Pergunta']}\nR: {row['Resposta_Oficial']}" for _, row in df_topico.iterrows()])
                prompt_para_ia = (
                    f"Você é um 'co-piloto' para a equipe de DP da empresa VIVA. Sua função é gerar sugestões de respostas claras, profissionais e empáticas. "
                    f"Baseie-se estritamente no contexto do especialista em '{agente_selecionado}'.\n\n"
                    f"Contexto:\n{contexto}\n\n"
                    f"Pergunta do Colaborador: {pergunta_colaborador}\n\n"
                    f"Sugestão de Resposta:"
                )
                
                resposta_texto = model.generate_content(prompt_para_ia).text
                
                # Guarda as informações na sessão para usar depois
                st.session_state.ultima_resposta = resposta_texto
                st.session_state.ultima_pergunta = pergunta_colaborador
                st.session_state.ultimo_colaborador = colaborador_solicitante
                st.session_state.ultima_empresa = empresa_solicitante

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a resposta: {e}")
                st.session_state.ultima_resposta = None

# --- EXIBIÇÃO E LOG DA RESPOSTA ---
if 'ultima_resposta' in st.session_state and st.session_state.ultima_resposta:
    st.divider()
    st.subheader("3. Resposta Sugerida pela IA")
    
    st.code(st.session_state.ultima_resposta, language=None)

    if st.button("Registrar esta resposta no Log"):
        with st.spinner("Salvando..."):
            # Chama a nova função de salvar_log com todos os parâmetros
            sucesso = salvar_log(
                matricula_dp=st.session_state.get('matricula'),
                nome_colaborador=st.session_state.get('ultimo_colaborador'),
                empresa=st.session_state.get('ultima_empresa'),
                pergunta=st.session_state.get('ultima_pergunta'),
                resposta=st.session_state.get('ultima_resposta')
            )
            if sucesso:
                st.success("Atendimento registrado com sucesso no histórico!")
                # Limpa os campos para o próximo atendimento
                st.session_state.ultima_resposta = None
                st.rerun()
            else:
                st.error("Falha ao registrar o log. Verifique as permissões da planilha.")

st.sidebar.markdown("---")
if st.sidebar.button("Sair da Sessão", use_container_width=True):
    st.session_state.clear()
    st.switch_page("1_Login.py")
