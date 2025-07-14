import streamlit as st
# Adicionada a nova função no import
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model,
    carregar_empresas 
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
lista_de_empresas = carregar_empresas() # Carrega a nova lista de empresas

# --- TELA PRINCIPAL DA FERRAMENTA ---
st.title("Assistente de Respostas do DP")
st.markdown("Use esta ferramenta para gerar respostas padronizadas e precisas para as dúvidas dos colaboradores.")
st.divider()

# --- SEÇÃO DE INPUTS ---
with st.container(border=True):
    st.subheader("1. Detalhes do Chamado")
    
    col1, col2 = st.columns(2)
    with col1:
        colaborador_solicitante = st.text_input("Nome do Colaborador que perguntou:")

    with col2:
        # NOVIDADE: Trocado st.text_input por st.selectbox
        # Adiciona uma opção em branco no início
        opcoes_empresa = ["Selecione uma empresa..."] + lista_de_empresas
        empresa_solicitante = st.selectbox("Empresa do Colaborador:", options=opcoes_empresa)
    

    # NOVIDADE: Seleção de Canal de Comunicação
    canal_comunicacao = st.radio(
        "Selecione o canal da resposta:",
        ["💬 Chat Comum", "📧 E-mail", "📱 WhatsApp"],
        horizontal=True
    )
    
    # Seleção do Agente/Especialista
    if base_conhecimento:
        topicos = list(base_conhecimento.keys())
        agente_selecionado = st.selectbox(
            "Selecione o assunto da dúvida (Agente Especialista):", 
            topicos, 
            index=topicos.index("Geral") if "Geral" in topicos else 0
        )
    else:
        agente_selecionado = None

    # Campo da pergunta
    pergunta_colaborador = st.text_area(
        "Copie e cole aqui a pergunta do colaborador:", 
        height=100
    )

# --- BOTÃO DE AÇÃO E LÓGICA DA IA ---

# --- BOTÃO DE AÇÃO E LÓGICA DA IA ---
if st.button("🤖 Gerar Resposta Sugerida", use_container_width=True, type="primary"):
    # Adicionada validação para o novo campo de seleção
    if empresa_solicitante == "Selecione uma empresa...":
        st.warning("Por favor, selecione a empresa do colaborador.")
    # Validações dos campos
    if not all([nome_solicitante, empresa_solicitante, pergunta_colaborador, agente_selecionado]):
        st.warning("Por favor, preencha todos os campos do chamado antes de gerar a resposta.")
    elif base_conhecimento and model:
        with st.spinner("Vivi está personalizando a resposta..."):
            try:
                # NOVIDADE: Prompt dinâmico com base no canal e no nome
                df_topico = base_conhecimento[agente_selecionado]
                contexto = "\n".join([f"P: {row['Pergunta']}\nR: {row['Resposta_Oficial']}" for _, row in df_topico.iterrows()])
                
                instrucao_canal = ""
                if canal_comunicacao == "📧 E-mail":
                    instrucao_canal = "Formate a resposta como um e-mail profissional, começando com 'Prezado(a) {nome_solicitante},' e terminando com 'Atenciosamente, Equipe de DP.'."
                elif canal_comunicacao == "📱 WhatsApp":
                    instrucao_canal = "Formate a resposta para WhatsApp, usando texto em negrito (*texto*) e quebras de linha curtas para melhor leitura. Seja um pouco mais informal, mas ainda profissional."
                else: # Chat Comum
                    instrucao_canal = "Formate a resposta de forma direta e clara para um chat interno."

                prompt_para_ia = (
                    f"Você é um 'co-piloto' para a equipe de DP da VIVA. Sua tarefa é gerar uma sugestão de resposta para a pergunta de um colaborador. A resposta deve ser direcionada ao colaborador chamado '{nome_solicitante}'.\n"
                    f"{instrucao_canal}\n"
                    f"Baseie-se estritamente no contexto do especialista em '{agente_selecionado}'. Não invente informações.\n\n"
                    f"Contexto:\n{contexto}\n\n"
                    f"Pergunta do Colaborador: {pergunta_colaborador}\n\n"
                    f"Sugestão de Resposta:"
                )
                
                resposta_texto = model.generate_content(prompt_para_ia).text
                
                # Guarda tudo na sessão para os próximos passos
                st.session_state.ultima_resposta = resposta_texto
                st.session_state.ultima_pergunta = pergunta_colaborador
                st.session_state.dados_solicitante = {
                    "nome": nome_solicitante,
                    "empresa": empresa_solicitante
                }

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a resposta: {e}")
                st.session_state.ultima_resposta = None

# --- EXIBIÇÃO DA RESPOSTA E SISTEMA DE AVALIAÇÃO ---
if 'ultima_resposta' in st.session_state and st.session_state.ultima_resposta:
    st.divider()
    st.subheader("2. Resposta Sugerida pela IA")
    
    # NOVIDADE: Botão de cópia fácil
    st.code(st.session_state.ultima_resposta, language=None)
    st.divider()

    # NOVIDADE: Sistema de Avaliação
    st.subheader("3. Avaliação e Registro")
    
    # Inicializa o estado do feedback
    if 'feedback_comment' not in st.session_state:
        st.session_state.feedback_comment = ""
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Resposta Positiva", use_container_width=True):
            st.session_state.feedback_given = "Positiva"
    with col2:
        if st.button("👎 Resposta Negativa", use_container_width=True):
            st.session_state.feedback_given = "Negativa"

    # Mostra campo de comentário se a avaliação for negativa
    if st.session_state.feedback_given == "Negativa":
        st.session_state.feedback_comment = st.text_area(
            "O que pode ser melhorado? (Obrigatório para avaliação negativa)"
        )

    # Lógica para salvar
    if st.session_state.feedback_given:
        # Validação para comentário em avaliação negativa
        if st.session_state.feedback_given == "Negativa" and not st.session_state.feedback_comment:
            st.warning("Por favor, descreva o motivo da avaliação negativa antes de registrar.")
        else:
            if st.button("Salvar Avaliação e Registrar Log", use_container_width=True, type="primary"):
                with st.spinner("Salvando..."):
                    sucesso = salvar_log(
                        matricula_dp=st.session_state.get('matricula'),
                        nome_colaborador=st.session_state.dados_solicitante['nome'],
                        empresa=st.session_state.dados_solicitante['empresa'],
                        pergunta=st.session_state.get('ultima_pergunta'),
                        resposta=st.session_state.get('ultima_resposta'),
                        avaliacao=st.session_state.feedback_given,
                        comentario=st.session_state.feedback_comment
                    )
                    if sucesso:
                        st.success("Atendimento e avaliação registrados com sucesso!")
                        # Limpa tudo para o próximo atendimento
                        for key in ['ultima_resposta', 'ultima_pergunta', 'dados_solicitante', 'feedback_given', 'feedback_comment']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("Falha ao registrar o log.")

st.sidebar.markdown("---")
if st.sidebar.button("Sair da Sessão", use_container_width=True):
    st.session_state.clear()
    st.switch_page("1_Login.py")
