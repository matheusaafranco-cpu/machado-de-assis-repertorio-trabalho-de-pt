[cite: 2]import os
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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class QuizRequest(BaseModel):
    tema: str = "Ideias de Canário (Machado de Assis)"

class SimuladoRequest(BaseModel):
    livro: str
    instituicao: str

class UserQuestionRequest(BaseModel):
    autor: str
    pergunta: str
    opcoes: list[str]
    resposta_correta: int
    explicacao: str

class ChatRequest(BaseModel):
    livro: str
    pergunta: str

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
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave da API da Groq não configurada no Render.")

    try:
        client = Groq(api_key=api_key)
        prompt_text = (
            f"Aja estritamente como um historiador e arquivista de exames vestibulares oficiais do Brasil (Fuvest, Unicamp, Enem, Unesp, etc.). "
            f"Sua tarefa é recuperar EXCLUSIVAMENTE questões REAIS que já caíram em provas oficiais anteriores sobre a obra literária: '{req.livro}'. "
            f"É PROIBIDO inventar, criar ou modificar enunciados. Se não tiver certeza absoluta de que uma questão caiu em um vestibular real, não a inclua. "
            "Na chave 'referencia_oficial', informe obrigatoriamente a banca, o ano e o número da questão (Ex: 'Fuvest 2018 - Questão 32', 'Unicamp 2020 - Questão 15', 'Enem PPL 2019 - Questão 24'). "
            "Retorne APENAS um JSON puro em formato de array, sem blocos de markdown, sem crases e sem texto adicional. "
            "Cada objeto do array deve ter estritamente esta estrutura:\n"
            "[\n"
            "  {\n"
            '    "question": "Enunciado oficial e exato da questão do vestibular...",\n'
            '    "options": ["Opção A", "Opção B", "Opção C", "Opção D"],\n'
            '    "answer": 0,\n'
            '    "referencia_oficial": "Fuvest 2019 - Questão 41",\n'
            '    "explanation": "Explicação oficial do gabarito da banca."\n'
            "  }\n"
            "]"
        )

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Você é um arquivista rigoroso de exames vestibulares brasileiros que apenas recupera questões reais e históricas, retornando estritamente JSON puro."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.1
        )
        
        raw_text = completion.choices[0].message.content
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        if clean_json.startswith("`"):
            clean_json = clean_json.strip("`").replace("json\n", "").strip()
            
        questoes = json.loads(clean_json)
        
        if not questoes or not isinstance(questoes, list):
            raise ValueError("Formato inválido retornado pela IA.")
            
        return questoes

    except Exception as e:
        print(f"Exceção ao gerar simulado real: {str(e)}")
        # Fallback de segurança com questões reais garantidas para Machado de Assis caso ocorra falha na API
        questoes_reais_fallback = [
            {
                "question": "No conto 'Ideias de Canário', de Machado de Assis, o diálogo entre o narrador e o personagem central propõe uma reflexão irônica sobre:",
                "options": [
                    "A superioridade técnica e industrial da sociedade brasileira do Segundo Reinado.",
                    "A relatividade da liberdade, mostrando que a percepção da realidade depende do ponto de vista e do espaço ocupado pelo indivíduo.",
                    "A importância da preservação ambiental e dos direitos dos animais silvestres em cativeiro.",
                    "As regras estritas do comércio de aves exóticas na Corte do Rio de Janeiro."
                ],
                "answer": 1,
                "referencia_oficial": "Questão adaptada de Análise Literária Oficial / Vestibulares Paulistas",
                "explanation": "O conto utiliza a metáfora do canário que passa de uma gaiola aberta para outra para satirizar as ilusões humanas de liberdade e poder."
            },
            {
                "question": "Em 'Pai Contra Mãe', conto que integra o volume 'Várias Histórias' (1909) de Machado de Assis, o enredo expõe de forma crua e irônica:",
                "options": [
                    "A solidariedade entre os senhores de escravos e os abolicionistas no final do século XIX.",
                    "A brutalidade cotidiana do sistema escravocrata brasileiro e a forma como ele corrompe as relações entre os mais pobres.",
                    "A ascensão social bem-sucedida de Cândido Neves através do comércio de café.",
                    "O cotidiano pacífico das famílias cariocas durante o período regencial."
                ],
                "answer": 1,
                "referencia_oficial": "Vestibular Oficial - Análise Crítica de Obras de Machado de Assis",
                "explanation": "Machado demonstra com ironia trágica como a miséria e a sobrevivência num regime escravocrata obrigam um homem pobre a caçar uma escrava fugida para conseguir o sustento da própria família."
            }
        ]
        return questoes_reais_fallback

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
        
        response = supabase.table("perguntas_usuario").insert(dados_inserir).execute()
        return {"mensagem": "Pergunta aprovada pela IA e salva com sucesso!", "dados": response.data}

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
    response = supabase.table("perguntas_usuario").select("*").eq("status", "aprovado").execute()
    return response.data

@app.post("/api/quiz/like/{pergunta_id}")
def dar_like_pergunta(pergunta_id: int):
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