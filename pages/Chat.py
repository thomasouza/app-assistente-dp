import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model,
    carregar_empresas,
    salvar_aprendizado
)

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")
load_css("style.css")

if not st.session_state.get('logged_in', False):
    st.error("Você precisa fazer login para acessar esta página.")
    st.stop()

base_conhecimento = carregar_base_conhecimento()
model = get_gemini_model()
lista_de_empresas = carregar_empresas() 

st.title("Assistente de Respostas do DP")
st.divider()

with st.container(border=True):
    st.subheader("1. Detalhes do Chamado")
    
    col1, col2 = st.columns(2)
    with col1:
        nome_solicitante = st.text_input("Nome do Colaborador que perguntou:")
    with col2:
        opcoes_empresa = [""] + lista_de_empresas if lista_de_empresas else [""]
        empresa_solicitante = st.selectbox("Empresa do Colaborador:", options=opcoes_empresa)

    canal_comunicacao = st.radio("Selecione o canal da resposta:", ["💬 Discord", "📧 E-mail", "📱 WhatsApp"], horizontal=True)
    
    if base_conhecimento:
        topicos = list(base_conhecimento.keys())
        agente_selecionado = st.selectbox("Selecione o assunto da dúvida:", topicos, index=topicos.index("Geral") if "Geral" in topicos else 0)
    else:
        agente_selecionado = None

    pergunta_colaborador = st.text_area("Copie e cole aqui a pergunta:", height=100)

if st.button("🤖 Gerar Resposta Sugerida", use_container_width=True, type="primary"):
    if not all([nome_solicitante, empresa_solicitante, pergunta_colaborador, agente_selecionado]):
        st.warning("Por favor, preencha todos os campos do chamado.")
    elif base_conhecimento and model:
        with st.spinner("Vivi está personalizando a resposta..."):
            try:
                df_topico = base_conhecimento[agente_selecionado]
                contexto = "\n".join([f"P: {row['Pergunta']}\nR: {row['Resposta_Oficial']}" for _, row in df_topico.iterrows()])
                instrucao_canal = ""
                if canal_comunicacao == "📧 E-mail":
                    instrucao_canal = f"Formate como um e-mail profissional para '{nome_solicitante}'."
                elif canal_comunicacao == "📱 WhatsApp":
                    instrucao_canal = f"Formate para WhatsApp para '{nome_solicitante}', com texto em *negrito*."
                elif canal_comunicacao == "💬 Discord":
                    instrucao_canal = f"Formate para Discord para '{nome_solicitante}', com texto em **negrito**."

                prompt_para_ia = (
                    f"Você é um assistente de DP. Responda à pergunta do colaborador com base estritamente no CONTEXTO. {instrucao_canal} "
                    f"REGRA CRÍTICA: Se a resposta não estiver no CONTEXTO, responda EXATAMENTE: 'Resposta não disponível na minha base de conhecimento.'\n\n"
                    f"CONTEXTO:\n{contexto}\n\n"
                    f"PERGUNTA: {pergunta_colaborador}\n\n"
                    f"RESPOSTA:"
                )
                
                resposta_texto = model.generate_content(prompt_para_ia).text
                st.session_state.ultima_resposta = resposta_texto
                st.session_state.ultima_pergunta = pergunta_colaborador
                st.session_state.agente_usado = agente_selecionado
                st.session_state.dados_solicitante = {"nome": nome_solicitante, "empresa": empresa_solicitante}

            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

if 'ultima_resposta' in st.session_state and st.session_state.ultima_resposta:
    st.divider()
    st.subheader("2. Resposta Sugerida pela IA")
    st.text_area("Resposta:", value=st.session_state.ultima_resposta, height=200, disabled=True)
    st.divider()
    st.subheader("3. Avaliação e Registro")
    
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = None
    col1, col2 = st.columns(2)
    if col1.button("👍 Positiva", use_container_width=True):
        st.session_state.feedback_given = "Positiva"
    if col2.button("👎 Negativa", use_container_width=True):
        st.session_state.feedback_given = "Negativa"

    if st.session_state.feedback_given == "Negativa":
        st.session_state.feedback_comment = st.text_area("O que pode ser melhorado?")
    else:
        st.session_state.feedback_comment = ""
    
    if st.session_state.feedback_given:
        if st.button("Salvar Log", use_container_width=True, type="primary"):
            with st.spinner("Salvando..."):
                salvar_log(st.session_state.get('matricula'), st.session_state.dados_solicitante['nome'], st.session_state.dados_solicitante['empresa'], st.session_state.get('ultima_pergunta'), st.session_state.get('ultima_resposta'), st.session_state.feedback_given, st.session_state.get('feedback_comment', ""))
                if st.session_state.feedback_given == "Negativa":
                    salvar_aprendizado(st.session_state.get('agente_usado'), st.session_state.get('ultima_pergunta'), st.session_state.get('ultima_resposta'), st.session_state.get('feedback_comment'))
                    st.cache_data.clear()
                st.success("Registrado com sucesso!")
                for key in ['ultima_resposta', 'ultima_pergunta', 'dados_solicitante', 'feedback_given', 'feedback_comment', 'agente_usado']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()

st.sidebar.divider()
if st.sidebar.button("Sair da Sessão", use_container_width=True):
    st.session_state.clear()
    st.switch_page("Login.py")