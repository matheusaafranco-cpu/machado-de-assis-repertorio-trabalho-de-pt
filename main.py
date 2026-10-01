import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

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

@app.post("/api/quiz/gerar")
def gerar_quiz(req: QuizRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave GEMINI_API_KEY não configurada no servidor.")

    try:
        # Configura a IA do Google oficialmente
        genai.configure(api_key=api_key)
        
        # Usa o modelo Gemini Flash mais recente e rápido
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt_text = (
            f"Gere exatamente 3 perguntas de múltipla escolha inéditas e educativas sobre o conto '{req.tema}' de Machado de Assis. "
            "Retorne APENAS um JSON válido em formato de array, sem blocos de markdown, sem crases e sem texto adicional. "
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

        response = model.generate_content(prompt_text)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # Converte a resposta da IA para JSON puro
        quiz_data = json.loads(clean_text)
        return quiz_data

    except Exception as e:
        print(f"Erro crítico ao gerar com a IA do Google: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao comunicar com a IA do Google: {str(e)}")