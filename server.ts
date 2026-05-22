import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const SYSTEM_PROMPT = `
Tu es JARVIS, l'assistant IA de l'utilisateur. Tu es calme, précis, légèrement formel
mais jamais condescendant. Tu parles comme l'IA dans Iron Man : concis, factuel,
avec parfois une touche d'humour sec. Tu peux :
- Répondre à des questions
- Ouvrir des sites web (réponds avec un JSON {"action":"open_url","url":"..."})
- Décrire ce que tu vois via la caméra (commande "camera") ou sur l'écran du PC (commande "screen")
- Contrôler le PC (réponds avec un JSON {"action":"system","command":"..."})
- Chercher des infos
Sois bref. 1-3 phrases max sauf si on demande plus de détails.
Si on dit "ouvre [site]", "montre-moi [lieu]", "lis mon écran" ou active la vision, réponds avec un JSON. 
Exemples: {"action":"open_url","url":"https://maps.google.com"}, {"action":"system", "command":"camera"}, {"action":"system", "command":"screen"}
Ne réponds que le JSON si l'intention est technique, pour faciliter le parsing.
`;

const conversationHistory: any[] = [];

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Health Route
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", model: "GEMINI-1.5-PRO (WEB FALLBACK)" });
  });

  // API Chat Route
  app.post("/api/chat", async (req, res) => {
    try {
      const { message } = req.body;
      
      conversationHistory.push({ role: "user", parts: [{ text: message }] });
      if (conversationHistory.length > 20) {
        conversationHistory.shift();
      }

      if (!process.env.GEMINI_API_KEY) {
        throw new Error("Clé API Gemini non configurée (GEMINI_API_KEY dans .env)");
      }

      const response = await ai.models.generateContent({
        model: "gemini-1.5-pro",
        contents: [
            { role: "user", parts: [{ text: SYSTEM_PROMPT }] },
            { role: "model", parts: [{ text: "Compris. Je suis prêt." }] },
            ...conversationHistory
        ]
      });

      let reply = response.text || "";
      conversationHistory.push({ role: "model", parts: [{ text: reply }] });

      let action = null;
      if (reply.includes("{")) {
        try {
          const startIdx = reply.indexOf("{");
          const endIdx = reply.lastIndexOf("}") + 1;
          const jsonStr = reply.slice(startIdx, endIdx);
          action = JSON.parse(jsonStr);
          reply = reply.slice(0, startIdx).trim();
          if (!reply) {
            reply = "Bien sûr. J'exécute l'action.";
          }
        } catch (e) {
          console.error("JSON parse error", e);
        }
      }

      res.json({ reply, action, model_used: "gemini-1.5-pro" });
    } catch (e: any) {
      console.error(e);
      res.status(500).json({ reply: "Erreur serveur Web : " + e.message });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Serve static files in production
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
