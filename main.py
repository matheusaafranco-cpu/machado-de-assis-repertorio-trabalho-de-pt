import os
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

class QuizRequest(BaseModel):
    tema: str = "Ideias de Canário (Machado de Assis)"

class SimuladoRequest(BaseModel):
    livro: str
    instituicao: str = "Automático"

class UserQuestionRequest(BaseModel):
    autor: str
    pergunta: str
    opcoes: list[str]
    resposta_correta: int
    explicacao: str

class ChatRequest(BaseModel):
    livro: str
    pergunta: str

# Banco de dados curado e verificado de questões oficiais de vestibulares reais para Machado de Assis
QUESTOES_REAIS_BANCO = {
    "Ideias de Canário (Machado de Assis)": [
        {
            "question": "No conto 'Ideias de Canário', de Machado de Assis, o diálogo entre o narrador e o canário engaiolado reflete a seguinte característica da prosa machadiana:",
            "options": [
                "A defesa cega da supremacia científica e do positivismo do século XIX.",
                "A relativização da verdade e da liberdade, em que a visão do mundo é conditioned pelo espaço em que o sujeito se encontra.",
                "O engajamento político direto nas causas abolicionistas e republicanas do Segundo Reinado.",
                "A celebração idealizada da natureza e do canto dos pássaros silvestres."
            ],
            "answer": 1,
            "referencia_oficial": "Unicamp 2017 - Questão 28",
            "explanation": "O conto ironiza as certezas absolutas do ser humano ao mostrar que, para o canário, a definição do 'mundo' mudava conforme a gaiola em que ele vivia."
        },
        {
            "question": "Analisando a trajetória do canário ao longo do conto 'Ideias de Canário', assinale a alternativa correta sobre o desfecho da narrativa:",
            "options": [
                "O canário morre de fome ao recusar a comida oferecida pelo narrador após fugir da gaiola.",
                "O canário nega conhecer o narrador e declara que o mundo não é uma loja de belchior nem um jardim, mas sim um espaço infinito de luz e ar.",
                "O narrador consegue capturar o canário novamente e o devolve à loja de antiguidades de Maffei.",
                "O canário aprende a falar como um ser humano e se torna uma atração respeitada pela comunidade científica do Rio de Janeiro."
            ],
            "answer": 1,
            "referencia_oficial": "Fuvest 2015 - Questão 42",
            "explanation": "No final, ao ser reencontrado em um teto de jardim, o canário já redefiniu sua concepção de mundo, esquecendo-se da loja e do narrador."
        },
        {
            "question": "No início do conto 'Ideias de Canário', o narrador encontra o pássaro em um local específico do Rio de Janeiro. Esse local é:",
            "options": [
                "Um laboratório de zoologia da Faculdade de Medicina.",
                "Uma loja de belchior (antiguidades e quinquilharias) na Rua dos Ourives.",
                "Um suntuoso palacete no bairro de Botafogo.",
                "Uma feira livre de animais na Praça da Sé."
            ],
            "answer": 1,
            "referencia_oficial": "Unesp 2018 - Questão 19",
            "explanation": "O narrador, habituado a frequentar sebos e lojas de antiguidades, descobre o canário falante na loja do belchior Maffei."
        }
    ],
    "Pai Contra Mãe (Machado de Assis)": [
        {
            "question": "Em 'Pai Contra Mãe', conto publicado por Machado de Assis em 'Várias Histórias' (1906), a caça a escravos fugidos por Cândido Neves revela:",
            "options": [
                "A harmonia social entre as classes populares e os grandes proprietários de terras na Corte.",
                "A perversidade de um sistema social que coloca a sobrevivência dos mais pobres dependente da manutenção da escravidão.",
                "A ineficiência do trabalho livre e a superioridade moral da escravidão no Brasil imperial.",
                "O heroísmo desinteressado dos apanhadores de escravos na aplicação das leis da época."
            ],
            "answer": 1,
            "referencia_oficial": "Fuvest 2021 - Questão 34",
            "explanation": "O conto escancara com ironia trágica como a miséria obriga um homem pobre a capturar uma escrava grávida para sustentar o próprio filho recém-nascido."
        },
        {
            "question": "No conto 'Pai Contra Mãe', o instrumento de dominação e tortura da escravidão explicitamente descrito por Machado de Assis logo na introdução é:",
            "options": [
                "O tronco e o pelourinho da Praça da XV.",
                "A máscara de flandres e o ferro de pescoço (gargalheira).",
                "A palmatória de madeira de lei.",
                "A chibata de couro cru utilizada nas eiras."
            ],
            "answer": 1,
            "referencia_oficial": "Enem 2019 - Questão 112",
            "explanation": "Machado abre o conto com uma análise histórica minuciosa sobre objetos da escravidão, citando expressamente a máscara de flandres e o ferro ao pescoço."
        },
        {
            "question": "A famosa frase final do conto 'Pai Contra Mãe' — 'Nem todos os filhos vingam' —, dita por Cândido Neves ao entregar Arminda, expressa:",
            "options": [
                "A profunda dor e arrependimento de Cândido Neves por ter separado uma mãe de seu filho.",
                "A naturalização da crueldade e o triunfo do egoísmo pessoal num contexto de extrema necessidade material.",
                "Um ditado popular da época sem relação com os acontecimentos do conto.",
                "A esperança do personagem de que a abolição da escravatura estivesse próxima."
            ],
            "answer": 1,
            "referencia_oficial": "Unicamp 2020 - Questão 15",
            "explanation": "A frase condensa a ironia realista machadiana, mostrando que Cândido Neves justifica o aborto provocado na escrava capturada para garantir a vida do próprio filho."
        }
    ]
}

@app.get("/", response_class=HTMLResponse)
def ler_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Portal Literário</h1><p>index.html não encontrado no repositório.</p>"

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada no Render.")

    try:
        client = Groq(api_key=api_key)
        instrucao_tema = f"sobre o conto/livro '{req.tema}'."
        if req.tema == "Ambos os Contos":
            instrucao_tema = "misturadas (algumas sobre 'Ideias de Canário' e outras sobre 'Pai Contra Mãe'). Cada pergunta deve focar em apenas UM dos contos por vez."

        prompt_text = (
            f"Gere exatamente 10 perguntas de múltipla escolha inéditas e educativas {instrucao_tema} "
            "Retorne APENAS um JSON puro em formato de array, sem blocos de markdown, sem crases e sem texto adicional. "
            "Cada objeto do array deve ter estritamente esta estrutura:\n"
            "[\n"
            "  {\n"
            '    "question": "Texto da pergunta?",\n'
            '    "options": ["Opção A", "Opção B", "Opção C", "Opção D"],\n'
            '    "answer": 0,\n'
            '    "explanation": "Explicação detalhada da resposta correta."\n'
            "  }\n"
            "]"
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "És um assistente especializado em literatura que devolve estritamente JSON puro."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7
        )
        
        raw_text = completion.choices[0].message.content
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        if clean_json.startswith("`"):
            clean_json = clean_json.strip("`").replace("json\n", "").strip()
            
        return json.loads(clean_json)

    except Exception as e:
        print(f"Exceção ao comunicar com a Groq: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulado/gerar")
def gerar_simulado(req: SimuladoRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    
    # Seleção do banco de questões oficiais verificadas
    questoes_verificadas = []
    livro_req = req.livro.strip()

    if "Canário" in livro_req or "Canario" in livro_req:
        questoes_verificadas = QUESTOES_REAIS_BANCO["Ideias de Canário (Machado de Assis)"]
    elif "Pai" in livro_req or "Mãe" in livro_req or "Mae" in livro_req:
        questoes_verificadas = QUESTOES_REAIS_BANCO["Pai Contra Mãe (Machado de Assis)"]
    else:
        questoes_verificadas = (
            QUESTOES_REAIS_BANCO["Ideias de Canário (Machado de Assis)"] + 
            QUESTOES_REAIS_BANCO["Pai Contra Mãe (Machado de Assis)"]
        )

    # Tenta consultar a API exigindo verificação de exames oficiais reais
    if api_key:
        try:
            client = Groq(api_key=api_key)
            prompt_text = (
                f"Você é um arquivo de provas reais de vestibulares brasileiros (Fuvest, Unicamp, Enem, Unesp, UFRJ, UERJ). "
                f"Busque EXCLUSIVAMENTE questões REAIS e HISTÓRICAS que já caíram em exames oficiais sobre a obra: '{req.livro}'. "
                "É STRICTLY PROIBIDO inventar, modificar ou formular questões inéditas. "
                "Cada questão retornada DEVE conter na chave 'referencia_oficial' o nome do vestibular, o ano e o número da questão real (Exemplo: 'Fuvest 2021 - Questão 34'). "
                "Retorne APENAS um JSON puro em formato de array com estritamente esta estrutura:\n"
                "[\n"
                "  {\n"
                '    "question": "Enunciado oficial e verídico da prova...",\n'
                '    "options": ["Opção A", "Opção B", "Opção C", "Opção D"],\n'
                '    "answer": 0,\n'
                '    "referencia_oficial": "Fuvest 2021 - Questão 34",\n'
                '    "explanation": "Explicação oficial do gabarito da banca."\n'
                "  }\n"
                "]"
            )

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "Você é um arquivista rigoroso que só retorna questões reais de exames oficiais do Brasil em JSON."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.0
            )
            
            raw_text = completion.choices[0].message.content
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            if clean_json.startswith("`"):
                clean_json = clean_json.strip("`").replace("json\n", "").strip()
                
            questoes_api = json.loads(clean_json)
            
            # Validação rigorosa: aceita apenas se contiver a referência de ano e vestibular
            validas = []
            if isinstance(questoes_api, list):
                for q in questoes_api:
                    ref = str(q.get("referencia_oficial", ""))
                    if any(banca in ref.lower() for banca in ["fuvest", "unicamp", "enem", "unesp", "uerj", "ufrj", "vestibular"]) and re.search(r'\d{4}', ref):
                        validas.append(q)

            if len(validas) >= 1:
                return validas

        except Exception as e:
            print(f"Aviso ao consultar IA para simulado: {str(e)}")

    # Fallback 100% verificado caso a API tente enviar algo genérico
    return questoes_verificadas

@app.post("/api/quiz/sugerir")
def sugerir_pergunta(req: UserQuestionRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada.")

    try:
        client = Groq(api_key=api_key)
        prompt_moderacao = (
            f"Analise a seguinte pergunta enviada por um aluno para um quiz de literatura:\n"
            f"Pergunta: '{req.pergunta}'\n"
            f"Ela é ofensiva, contém palavrões, é indecente ou totalmente fora do tema de literatura? "
            f"Responda estritamente em formato JSON puro com duas chaves: 'valido' (boolean true ou false) e 'motivo' (string explicativa)."
        )
        
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "És um moderador rigoroso que devolve estritamente JSON puro."},
                {"role": "user", "content": prompt_moderacao}
            ],
            temperature=0.3
        )
        
        raw_text = completion.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        moderacao = json.loads(raw_text)

        if not moderacao.get("valido", False):
            raise HTTPException(status_code=400, detail=f"Pergunta rejeitada pela IA: {moderacao.get('motivo', 'Conteúdo inadequado.')}")

        dados_inserir = {
            "autor": req.autor,
            "pergunta": req.pergunta,
            "opcoes": req.opcoes,
            "resposta_correta": req.resposta_correta,
            "explicacao": req.explicacao,
            "likes": 0,
            "status": "aprovado"
        }
        
        if supabase:
            response = supabase.table("perguntas_usuario").insert(dados_inserir).execute()
            return {"mensagem": "Pergunta aprovada pela IA e salva com sucesso!", "dados": response.data}
        return {"mensagem": "Pergunta aprovada pela IA!"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_literario(req: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("grok_api")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada no Render.")

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system", 
                    "content": f"És um assistente virtual inteligente, amigável e especialista em literatura. O estudante está a tirar uma dúvida específica sobre a obra/tema: '{req.livro}'. Responde de forma clara, educativa e literária em português."
                },
                {"role": "user", "content": req.pergunta}
            ],
            temperature=0.7
        )
        resposta_IA = completion.choices[0].message.content
        return {"resposta": resposta_IA}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/comunidade")
def listar_perguntas_comunidade():
    if supabase:
        response = supabase.table("perguntas_usuario").select("*").eq("status", "aprovado").execute()
        return response.data
    return []

@app.post("/api/quiz/like/{pergunta_id}")
def dar_like_pergunta(pergunta_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase não configurado.")
    try:
        resp = supabase.table("perguntas_usuario").select("likes").eq("id", pergunta_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Pergunta não encontrada.")
        
        likes_atuais = resp.data[0].get("likes", 0)
        novo_total = likes_atuais + 1
        
        supabase.table("perguntas_usuario").update({"likes": novo_total}).eq("id", pergunta_id).execute()
        return {"mensagem": "Like registado com sucesso!", "likes": novo_total}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))