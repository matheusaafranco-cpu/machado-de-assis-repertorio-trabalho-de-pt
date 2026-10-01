import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuizRequest(BaseModel):
    tema: str = "Um Canário (Machado de Assis)"

@app.get("/", response_class=HTMLResponse)
def ler_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Portal do Machado de Assis</h1><p>index.html não encontrado no repositório.</p>"

# Perguntas de segurança garantidas para a apresentação da Etec
FALLBACK_QUIZZES = {
    "Um Canário": [
        {
            "question": "No conto 'Um Canário', qual é a principal reflexão trazida pelo diálogo sobre a ave engaiolada?",
            "options": [
                "A relatividade da liberdade e a adaptação ao cativeiro.",
                "A importância de alimentar animais exóticos.",
                "O valor comercial dos pássaros no século XIX.",
                "A superioridade dos animais sobre os seres humanos."
            ],
            "answer": 0,
            "explanation": "O conto explora de forma irônica como a percepção da liberdade muda consoante o ambiente em que o indivíduo se encontra."
        },
        {
            "question": "Quem é o interlocutor que conversa com o narrador acerca do canário?",
            "options": ["Um boticário", "Um negociante de aves", "Um poeta romântico", "Um vizinho curioso"],
            "answer": 0,
            "explanation": "O narrador dialoga com o dono do canário, identificado como sendo um boticário reformado."
        },
        {
            "question": "Em que ano foi publicado o conto 'Um Canário'?",
            "options": ["1881", "1883", "1899", "1906"],
            "answer": 1,
            "explanation": "O conto foi publicado originalmente em 1883, inserindo-se na fase de maturidade literária de Machado de Assis."
        }
    ],
    "Pai Contra Mãe": [
        {
            "question": "Qual é a profissão exercida por Cândido Neves, protagonista de 'Pai Contra Mãe'?",
            "options": ["Apanhador de escravos fugidos", "Professor de literatura", "Funcionário público", "Jornalista"],
            "answer": 0,
            "explanation": "Cândido Neves ganhava a vida capturando escravos fugidos, retratando a brutalidade do período escravocrata."
        },
        {
            "question": "Qual é o principal conflito dramático no desfecho do conto?",
            "options": [
                "A captura de Arminda para garantir o sustento da família de Cândido.",
                "A fuga bem-sucedida de todos os escravos da província.",
                "A desistência de Cândido em caçar escravos.",
                "O julgamento de Cândido em tribunal."
            ],
            "answer": 0,
            "explanation": "Cândido captura a escrava grávida Arminda, cujo prêmio de resgate resolve a sua aflição financeira, sacrificando o futuro do filho dela."
        },
        {
            "question": "Que crítica social central Machado de Assis faz em 'Pai Contra Mãe'?",
            "options": [
                "A crueldade do sistema escravocrata que obrigava os pobres livres a oprimir os escravizados por sobrevivência.",
                "A falta de escolas públicas no Rio de Janeiro.",
                "A corrupção na política imperial.",
                "O preço elevado dos géneros alimentícios."
            ],
            "answer": 0,
            "explanation": "A obra escancara como a escravidão corrompia e embrutecia toda a sociedade, colocando os oprimidos em conflito entre si."
        }
    ]
}

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Tenta usar a IA se a chave existir
    if api_key:
        try:
            prompt_text = (
                f"Gere 3 perguntas de múltipla escolha sobre o conto '{req.tema}' de Machado de Assis. "
                "Retorne APENAS um JSON válido em formato de array, sem blocos de markdown, sem texto antes ou depois. "
                "Estrutura exata:\n"
                "[\n"
                "  {\n"
                '    \"question\": \"Pergunta?\",\n'
                '    \"options\": [\"A\", \"B\", \"C\", \"D\"],\n'
                '    \"answer\": 0,\n'
                '    \"explanation\": \"Explicação.\"\n'
                "  }\n"
                "]"
            )

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
        except Exception as e:
            print(f"Aviso da IA (a usar fallback automático): {e}")

    # Se a IA falhar ou demorar, entrega o quiz predefinido instantaneamente
    tema_escolhido = req.tema if req.tema in FALLBACK_QUIZZES else "Um Canário"
    if "Ambos" in req.tema:
        return FALLBACK_QUIZZES["Um Canário"][:2] + FALLBACK_QUIZZES["Pai Contra Mãe"][:1]
    
    return FALLBACK_QUIZZES.get(tema_escolhido, FALLBACK_QUIZZES["Um Canário"])