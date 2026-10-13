# Menu Translator

![Menu Translator Banner](banner.jpg)

Translates restaurant menu dishes using a local open-source model (Llama 3.2 via Ollama). Runs offline, no API cost, menu data stays private.

## Screenshot

![App Screenshot](screenshot.jpg)

## Safety

This tool is designed to reduce allergen misinformation in translated menus:

- The model **only uses ingredients explicitly written** in the restaurant notes you provide. It never guesses ingredients from a dish name.
- The model **never claims a dish is allergen-free** (e.g. "peanut-free", "gluten-free") unless the notes explicitly say so.
- Any detail not confirmed by the notes is flagged with **(unconfirmed, owner please verify)**.
- A visible warning reminds users to review all output before printing.

> **Always review translations with your chef or menu owner before publishing.**

## Setup
1. Install Ollama from ollama.com
2. ollama pull llama3.2
3. pip install -r requirements.txt
4. python app.py
5. Open http://localhost:5000