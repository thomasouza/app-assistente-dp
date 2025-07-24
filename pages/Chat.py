import streamlit as st
from helpers import (
    load_css, 
    carregar_base_conhecimento, 
    salvar_log, 
    get_gemini_model,
    carregar_empresas,
    salvar_aprendizado
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
lista_de_empresas = carregar_empresas() 

# --- TELA PRINCIPAL DA FERRAMENTA ---
st.title("Assistente de Respostas do DP")
st.markdown("Use esta ferramenta para gerar respostas padronizadas e precisas para as dúvidas dos colaboradores.")
st.divider()

# --- SEÇÃO DE INPUTS ---
with st.container(border=True):
    st.subheader("1. Detalhes do Chamado")
    
    col1, col2 = st.columns(2)
    with col1:
        nome_solicitante = st.text_input("Nome do Colaborador que perguntou:")
    with col2:
        opcoes_empresa = [""] + lista_de_empresas if lista_de_empresas else [""]
        empresa_solicitante = st.selectbox("Empresa do Colaborador:", options=opcoes_empresa)

    canal_comunicacao = st.radio(
        "Selecione o canal da resposta:",
        ["💬 Discord", "📧 E-mail", "📱 WhatsApp"],
        horizontal=True
    )
    
    if base_conhecimento:
        topicos = list(base_conhecimento.keys())
        agente_selecionado = st.selectbox(
            "Selecione o assunto da dúvida (Agente Especialista):", 
            topicos, 
            index=topicos.index("Geral") if "Geral" in topicos else 0
        )
    else:
        agente_selecionado = None

    pergunta_colaborador = st.text_area("Copie e cole aqui a pergunta do colaborador:", height=100)

# --- BOTÃO DE AÇÃO E LÓGICA DA IA ---
if st.button("🤖 Gerar Resposta Sugerida", use_container_width=True, type="primary"):
    if not all([nome_solicitante, empresa_solicitante, pergunta_colaborador, agente_selecionado]):
        st.warning("Por favor, preencha todos os campos do chamado antes de gerar a resposta.")
    elif base_conhecimento and model:
        with st.spinner("Vivi está interpretando a pergunta e buscando a melhor resposta..."):
            try:
                df_topico = base_conhecimento[agente_selecionado]
                contexto = "\n".join([f"PERGUNTA REGISTRADA: {row['Pergunta']}\nRESPOSTA PADRÃO: {row['Resposta_Oficial']}\n---\n" for _, row in df_topico.iterrows()])
                
                instrucao_canal = ""
                if canal_comunicacao == "📧 E-mail":
                    instrucao_canal = f"Formate a resposta como um e-mail profissional, começando com 'Prezado(a) {nome_solicitante},' e terminando com 'Atenciosamente, Equipe de DP.'."
                elif canal_comunicacao == "📱 WhatsApp":
                    instrucao_canal = f"Formate a resposta para WhatsApp, começando com 'Olá, {nome_solicitante}! 👋'. Use quebras de linha curtas e emojis. Use *negrito* para destacar."
                elif canal_comunicacao == "💬 Discord":
                    instrucao_canal = f"Formate a resposta para Discord. Use markdown como **para negrito**. Seja amigável."

                prompt_para_ia = f"""
                **PERSONA:**
                Você é a Vivi, uma assistente de DP da empresa VIVA. Sua comunicação é precisa, clara, direta e empática.

                **DIRETRIZ PRINCIPAL:**
                Sua ÚNICA fonte de verdade é a lista de PERGUNTAS REGISTRADAS e RESPOSTAS PADRÃO no CONTEXTO TÉCNICO.

                **PROCESSO DE PENSAMENTO EM 2 ETAPAS:**
                ETAPA 1: ANÁLISE E BUSCA. Primeiro, leia a PERGUNTA DO COLABORADOR. Compare o significado e a intenção dessa pergunta com a lista de PERGUNTAS REGISTRADAS no CONTEXTO TÉCNICO. Identifique qual par de PERGUNTA/RESPOSTA do contexto melhor corresponde à dúvida do colaborador, mesmo que as palavras sejam diferentes.
                ETAPA 2: FORMULAÇÃO DA RESPOSTA. Use a RESPOSTA PADRÃO que você encontrou na Etapa 1 como base para sua resposta final.

                **REGRAS CRÍTICAS DE COMPORTAMENTO:**
                1.  **NÃO INVENTE:** É PROIBIDO inventar, inferir ou adicionar qualquer informação que não esteja na RESPOSTA PADRÃO encontrada.
                2.  **PASSO A PASSO:** Se a RESPOSTA PADRÃO contiver um passo a passo (lista numerada ou com marcadores), você deve reproduzir essa lista EXATAMENTE como ela está escrita, sem alterar a ordem, o texto ou o formato.
                3.  **SE NÃO ENCONTRAR:** Se, na Etapa 1, você não encontrar nenhuma PERGUNTA REGISTRADA no contexto que corresponda à intenção da PERGUNTA DO COLABORADOR, sua única resposta deve ser, sem exceções: "Não encontrei essa informação na minha base de conhecimento. Para te ajudar com precisão, por favor, abra um chamado com a equipe de DP."
                
                **FORMATAÇÃO DE SAÍDA:**
                Adapte o texto da RESPOSTA PADRÃO encontrada para o canal de comunicação solicitado, seguindo a INSTRUÇÃO DE CANAL. Direcione a resposta para o nome do colaborador.

                ---
                **INSTRUÇÃO DE CANAL:** {instrucao_canal}
                ---
                **CONTEXTO TÉCNICO:**
                {contexto}
                ---
                **PERGUNTA DO COLABORADOR:** {pergunta_colaborador}
                ---
                **RESPOSTA GERADA PELA VIVI:**
                """
                
                resposta_texto = model.generate_content(prompt_para_ia).text
                
                st.session_state.ultima_resposta = resposta_texto
                st.session_state.ultima_pergunta = pergunta_colaborador
                st.session_state.agente_usado = agente_selecionado
                st.session_state.dados_solicitante = {"nome": nome_solicitante, "empresa": empresa_solicitante}

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a resposta: {e}")

# --- EXIBIÇÃO DA RESPOSTA E SISTEMA DE AVALIAÇÃO ---
if 'ultima_resposta' in st.session_state and st.session_state.ultima_resposta:
    st.divider()
    st.subheader("2. Resposta Sugerida pela IA")
    
    st.text_area(
        label="Copia a resposta sugerida abaixo:",
        value=st.session_state.ultima_resposta,
        height=200,
        disabled=True
    )
    
    st.divider()

    st.subheader("3. Avaliação e Registro")
    
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = None

    col1, col2 = st.columns(2)
    if col1.button("👍 Resposta Positiva", use_container_width=True):
        st.session_state.feedback_given = "Positiva"
    if col2.button("👎 Resposta Negativa", use_container_width=True):
        st.session_state.feedback_given = "Negativa"

    if st.session_state.feedback_given == "Negativa":
        st.session_state.feedback_comment = st.text_area("O que pode ser melhorado? (Obrigatório para avaliação negativa)", key="feedback_comment_input")
    else:
        st.session_state.feedback_comment = ""
    
    if st.session_state.feedback_given:
        if st.session_state.feedback_given == "Negativa" and not st.session_state.get('feedback_comment'):
            st.warning("Por favor, descreva a resposta correta ou o motivo da avaliação negativa antes de registrar.")
        else:
            if st.button("Salvar Avaliação e Registrar Log", use_container_width=True, type="primary"):
                with st.spinner("Salvando registro e aprendizado..."):
                    
                    sucesso_log = salvar_log(
                        matricula_dp=st.session_state.get('matricula'),
                        nome_colaborador=st.session_state.dados_solicitante['nome'],
                        empresa=st.session_state.dados_solicitante['empresa'],
                        pergunta=st.session_state.get('ultima_pergunta'),
                        resposta=st.session_state.get('ultima_resposta'),
                        avaliacao=st.session_state.feedback_given,
                        comentario=st.session_state.get('feedback_comment', "")
                    )
                    
                    if st.session_state.feedback_given == "Negativa":
                        sucesso_aprendizado = salvar_aprendizado(
                            assunto=st.session_state.get('agente_usado'),
                            pergunta=st.session_state.get('ultima_pergunta'),
                            resposta_ia=st.session_state.get('ultima_resposta'),
                            comentario_humano=st.session_state.get('feedback_comment')
                        )
                        if sucesso_aprendizado: 
                            st.cache_data.clear()
                    
                    if sucesso_log:
                        st.success("Atendimento registrado e feedback salvo com sucesso!")
                    else:
                        st.error("Falha ao registrar o log do atendimento.")

                    for key in ['ultima_resposta', 'ultima_pergunta', 'dados_solicitante', 'feedback_given', 'feedback_comment', 'agente_usado']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Sair da Sessão", use_container_width=True):
    st.session_state.clear()
    st.switch_page("Login.py")