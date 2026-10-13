from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German", "Italian",
    "Portuguese", "Japanese", "Chinese", "Korean", "Arabic", "Russian",
    "Thai", "Vietnamese", "Turkish", "Dutch", "Swedish", "Greek"
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu Translator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f1117;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        h1 {
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
        }
        .subtitle {
            color: #9ca3af;
            font-size: 1rem;
            margin-bottom: 32px;
        }
        .container {
            width: 100%;
            max-width: 900px;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        label {
            font-weight: 600;
            font-size: 0.9rem;
            color: #c9cdd4;
            margin-bottom: 4px;
            display: block;
        }
        select, textarea {
            width: 100%;
            padding: 12px 14px;
            background: #1a1d27;
            border: 1px solid #2d3140;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        select:focus, textarea:focus {
            border-color: #6366f1;
        }
        textarea { resize: vertical; }
        .row {
            display: flex;
            gap: 18px;
        }
        .row > div { flex: 1; }
        button {
            padding: 14px 28px;
            background: #6366f1;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            align-self: flex-start;
        }
        button:hover { background: #4f46e5; }
        button:disabled {
            background: #3b3e52;
            cursor: not-allowed;
        }
        .output-box {
            margin-top: 28px;
            padding: 20px;
            background: #1a1d27;
            border: 1px solid #2d3140;
            border-radius: 8px;
            white-space: pre-wrap;
            line-height: 1.7;
            font-size: 0.95rem;
        }
        .output-box h2 {
            font-size: 1.1rem;
            color: #ffffff;
            margin-bottom: 12px;
        }
        .safety-warning {
            margin-top: 10px;
            padding: 8px 12px;
            font-size: 0.82rem;
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.2);
            border-radius: 6px;
            line-height: 1.4;
        }
        .footer {
            margin-top: 40px;
            font-size: 0.8rem;
            color: #555;
        }
        @media (max-width: 640px) {
            .row { flex-direction: column; gap: 14px; }
        }
    </style>
</head>
<body>
    <h1>Menu Translator</h1>
    <p class="subtitle">Translate any restaurant menu dish instantly using AI</p>

    <div class="container">
        <form method="POST" action="/translate">
            <div>
                <label for="language">Translate to</label>
                <select id="language" name="language">
                    {% for lang in languages %}
                    <option value="{{ lang }}" {{ 'selected' if lang == selected_lang }}>{{ lang }}</option>
                    {% endfor %}
                </select>
            </div>

            <div class="row">
                <div>
                    <label for="dishes">Paste menu items (one per line)</label>
                    <textarea id="dishes" name="dishes" rows="7" placeholder="Pad Thai&#10;Paneer Tikka&#10;Crème Brûlée">{{ dishes }}</textarea>
                </div>
                <div>
                    <label for="notes">Restaurant notes (allergens, ingredients, etc.)</label>
                    <textarea id="notes" name="notes" rows="7" placeholder="Optional: e.g. Pad Thai contains peanuts">{{ notes }}</textarea>
                </div>
            </div>

            <button type="submit">Translate</button>
        </form>

        {% if output %}
        <div class="output-box">
            <h2>Translation</h2>
            {{ output }}
        </div>
        <div class="safety-warning">
            ⚠ Review all translations and allergen information before printing. This tool can make mistakes.
        </div>
        {% endif %}
    </div>

    <p class="footer">Powered by Llama 3.2 via Ollama</p>
</body>
</html>
"""


def build_prompt(dishes_text, notes_text, target_language):
    """Build the translation prompt with allergen safety rules."""
    notes_section = notes_text.strip() if notes_text.strip() else "(none provided)"

    return f"""You are a restaurant menu translator. Translate the dishes below into {target_language}.

Restaurant notes:
{notes_section}

Rules (you must follow every rule strictly):
1. Only state ingredients if they are explicitly written in the Restaurant notes above. Never guess or infer ingredients from the dish name alone.
2. Never claim a dish is free of any ingredient or allergen. Do not write "peanut-free", "vegan", "gluten-free", "dairy-free", "nut-free", or any similar claim unless the Restaurant notes explicitly say so.
3. If you include any detail in the description that is not directly confirmed by the Restaurant notes, you must append "(unconfirmed, owner please verify)" after that detail.
4. If the Restaurant notes contain information about a specific dish, add a "Source note:" line immediately after that dish's translation showing the relevant note.
5. Keep descriptions short (one sentence). Do not add extra commentary.

Output format for each dish (follow exactly):
Original name -> Translated name: short description
Source note: ... (only if the Restaurant notes mention this dish)

Dishes:
{dishes_text}
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        HTML_TEMPLATE,
        languages=LANGUAGES,
        selected_lang="English",
        dishes="",
        notes="",
        output=None
    )


@app.route("/translate", methods=["POST"])
def translate():
    dishes_text = request.form.get("dishes", "").strip()
    notes_text = request.form.get("notes", "").strip()
    target_language = request.form.get("language", "English")

    output = ""
    if dishes_text:
        prompt = build_prompt(dishes_text, notes_text, target_language)
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=120)
            resp.raise_for_status()
            output = resp.json().get("response", "No response from model.")
        except requests.ConnectionError:
            output = "Error: Cannot connect to Ollama. Make sure it is running (ollama serve)."
        except requests.Timeout:
            output = "Error: Request timed out. The model may be loading — try again."
        except Exception as e:
            output = f"Error: {e}"

    return render_template_string(
        HTML_TEMPLATE,
        languages=LANGUAGES,
        selected_lang=target_language,
        dishes=dishes_text,
        notes=notes_text,
        output=output
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
