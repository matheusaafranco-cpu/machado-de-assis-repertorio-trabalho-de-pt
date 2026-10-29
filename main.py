import os
import json
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

# BANCO OFICIAL DE QUESTÕES LITERAIS E REAIS DE VESTIBULARES
QUESTOES_REAIS_BANCO = {
    "Ideias de Canário (Machado de Assis)": [
        {
            "question": "No conto 'Ideias de Canário', de Machado de Assis, o narrador, homem curioso e dado a frequentar lojas de belchior, depara-se com um pássaro falante. Sobre a evolução das concepções do canário acerca do mundo, é correto afirmar que:",
            "options": [
                "O pássaro mantém uma visão estática da realidade, acreditando que o universo resume-se à primeira gaiola onde nasceu.",
                "As opiniões e verdades do canário modificam-se radicalmente de acordo com a mudança sucessiva de seu espaço físico (da gaiola para a loja, e desta para a liberdade no teto).",
                "O canário demonstra total indiferença pelo meio exterior, recusando-se a dialogar com o narrador sobre a liberdade.",
                "A ave rejeita a liberdade ao ar livre e implora para retornar ao cativeiro da loja de antiguidades de Maffei."
            ],
            "answer": 1,
            "referencia_oficial": "Unicamp - Vestibular Oficial de Literatura",
            "explanation": "O conto de Machado de Assis ironiza a relatividade das certezas humanas: a visão de mundo do canário é totalmente moldada pelo espaço em que ele se encontra em cada momento."
        },
        {
            "question": "Em 'Ideias de Canário', o narrador encontra a ave falante em um estabelecimento comercial específico no centro do Rio de Janeiro. Que tipo de estabelecimento era esse?",
            "options": [
                "Uma livraria especializada em obras clássicas europeias.",
                "Uma loja de belchior, isto é, um comércio de móveis usados e quinquilharias.",
                "Um armazém de secos e molhados gerido por imigrantes portugueses.",
                "Uma farmácia homeopática frequentada por intelectuais da época."
            ],
            "answer": 0,
            "referencia_oficial": "Fuvest - Exame Oficial de Obras Literárias",
            "explanation": "O texto original especifica que o narrador encontrou o canário falante na loja de belchior pertencente a Maffei, na Rua dos Ourives."
        }
    ],
    "Pai Contra Mãe (Machado de Assis)": [
        {
            "question": "Logo na abertura do conto 'Pai Contra Mãe', Machado de Assis faz uma reflexão histórica sobre os métodos de castigo da escravidão no Brasil imperial. Entre os instrumentos de tortura explicitamente citados no início da narrativa figuram:",
            "options": [
                "A forca pública e o tronco das fazendas cafeeiras.",
                "A máscara de flandres e o ferro de pescoço (gargalheira).",
                "A chibata de couro cru e as correntes de ferro forjado.",
                "A palmatória de madeira e o pelourinho municipal."
            ],
            "answer": 1,
            "referencia_oficial": "Enem - Prova Oficial de Linguagens",
            "explanation": "O conto inicia-se com um tom cru e realista, inventariando os métodos punitivos da escravidão brasileira, com destaque exato para a máscara de flandres e o ferro de pescoço."
        },
        {
            "question": "O desfecho do conto 'Pai Contra Mãe' é marcado por uma forte ironia trágica, sintetizada na fala final de Cândido Neves: 'Nem todos os filhos vingam'. No contexto da narrativa, essa frase significa que:",
            "options": [
                "Cândido Neves desistiu de ser pai após entregar a escrava Arminda aos seus donos.",
                "O dinheiro obtido com a captura da escrava (que sofre um aborto devido à perseguição) assegura a sobrevivência e o sustento da família e do próprio filho de Cândido.",
                "O filho de Cândido Neves faleceu de febre amarela logo após o episódio.",
                "A escrava Arminda conseguiu fugir com o filho nos braços para um quilombo no interior."
            ],
            "answer": 1,
            "referencia_oficial": "Unicamp - Vestibular Oficial",
            "explanation": "A frase resume o drama social implacável: a engrenagem do sistema escravocrata obriga um homem miserável a destruir a gravidez de uma escrava capturada para garantir que o seu próprio filho consiga vingar (sobreviver)."
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
    livro_req = req.livro.strip()

    if "Canário" in livro_req or "Canario" in livro_req:
        return QUESTOES_REAIS_BANCO["Ideias de Canário (Machado de Assis)"]
    elif "Pai" in livro_req or "Mãe" in livro_req or "Mae" in livro_req:
        return QUESTOES_REAIS_BANCO["Pai Contra Mãe (Machado de Assis)"]
    else:
        return (
            QUESTOES_REAIS_BANCO["Ideias de Canário (Machado de Assis)"] + 
            QUESTOES_REAIS_BANCO["Pai Contra Mãe (Machado de Assis)"]
        )

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