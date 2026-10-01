package com.seuprojeto.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // Permite requisições vindas do GitHub Pages ou localhost
public class QuizController {

    // Lê a chave configurada no Render (GEMINI_API_KEY)
    @Value("${GEMINI_API_KEY:${gemini.api.key:SUA_CHAVE_AQUI}}")
    private String apiKey;

    @PostMapping("/quiz/gerar")
    public ResponseEntity<?> gerarQuiz(@RequestBody Map<String, String> request) {
        String tema = request.getOrDefault("tema", "Um Canário (Machado de Assis)");

        String promptText = "Gere 3 perguntas inéditas e criativas de múltipla escolha sobre o conto '" + tema + "' de Machado de Assis. "
                + "Responda EXCLUSIVAMENTE com um JSON no formato de Array de objetos (sem markdown, sem ```json ou texto adicional). "
                + "Estrutura obrigatória:\n"
                + "[\n"
                + "  {\n"
                + "    \"question\": \"Texto da pergunta?\",\n"
                + "    \"options\": [\"Opção 0\", \"Opção 1\", \"Opção 2\", \"Opção 3\"],\n"
                + "    \"answer\": 0,\n"
                + "    \"explanation\": \"Explicação sobre a resposta correta.\"\n"
                + "  }\n"
                + "]\n"
                + "O campo 'answer' deve ser um inteiro (0 a 3) indicando o índice da opção correta.";

        try {
            RestTemplate restTemplate = new RestTemplate();
            // URL corrigida da API Gemini
            String url = "[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=)" + apiKey;

            Map<String, Object> part = new HashMap<>();
            part.put("text", promptText);

            Map<String, Object> content = new HashMap<>();
            content.put("parts", Collections.singletonList(part));

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("contents", Collections.singletonList(content));

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);

            // Extrai a resposta
            List candidates = (List) response.getBody().get("candidates");
            Map firstCandidate = (Map) candidates.get(0);
            Map contentResp = (Map) firstCandidate.get("content");
            List partsResp = (List) contentResp.get("parts");
            Map firstPart = (Map) partsResp.get(0);

            String rawJson = (String) firstPart.get("text");
            // Limpa formatação de markdown se a API incluir
            rawJson = rawJson.replace("```json", "").replace("```", "").trim();

            return ResponseEntity.ok().contentType(MediaType.APPLICATION_JSON).body(rawJson);

        } catch (Exception e) {
            e.printStackTrace();
            Map<String, String> err = new HashMap<>();
            err.put("erro", "Não foi possível carregar o quiz. Verifique se a chave de API está correta.");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(err);
        }
    }
}