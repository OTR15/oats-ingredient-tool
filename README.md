
# 🥣 Oat Flavor Ingredient Finder

This tool lets you explore ingredients in different oat flavors — or find all the flavors that contain a specific ingredient.

### 🔗 Live App
Hosted on [Render](https://oats-ingredient-tool.onrender.com)

---

## 🔍 Features

- Search by **flavor** to view its ingredients
- Search by **ingredient** to view matching flavors
- ✅ Supports ingredient aliases (e.g. "monk fruit" = "MONKFRUIT", "MONK-FRUIT")
- ✅ Fuzzy & token-based fallback (handles "strawberries" vs "strawberry")
- ✅ Toggle to view flavors that **don’t contain** an ingredient
- Inline alias editor via `/aliases`

---

## 🛠 Setup (Local)

1. Clone the repo

```bash
git clone https://github.com/OTR15/oats-ingredient-tool.git
cd oats-ingredient-tool
```

2. Install dependencies

```bash
pip install flask pandas
```

3. Run it

```bash
python app.py
```

Then open: `http://localhost:5000`

---

## 📊 Updating Flavors & Ingredients

We recommend using a Google Sheet to manage your flavor data.

### Step 1: Use this template

[Google Sheets Template](https://docs.google.com/spreadsheets/d/1RhtmF4vl9l7-3wx_S7y2_YXKNuTLU1JrLT5jcBrFn5U/copy)

### Step 2: Download it as CSV

File → Download → CSV

### Step 3: Convert it to JSON

Run:

```bash
python run_converter.py
```

This will update:
- `data/flavor_to_ingredients.json`
- `data/ingredient_to_flavors.json`

Then commit and push the changes to update the live app.

---

## 🧠 File Structure

```
├── app.py                      # Flask app
├── run_converter.py           # Converts CSV → JSON
├── csv_to_flavor_json_converter.py
├── data/
│   ├── flavor_to_ingredients.json
│   ├── ingredient_to_flavors.json
│   └── ingredient_aliases.json
├── templates/
│   ├── index.html              # Search UI
│   └── alias_editor.html       # /aliases editor
├── requirements.txt
└── render.yaml                 # For deployment on Render
```

---

## 🧪 Alias System

Aliases allow you to group variations under one name:

```json
"MONK FRUIT": [
  "MONKFRUIT",
  "MONK FRUIT",
  "MONK-FRUIT"
]
```

Edit them live at: `/aliases`  
Download and commit changes to persist.

---

## 📦 Deploying to Render

1. Push to GitHub
2. Link the repo to [Render](https://render.com)
3. Use this as your `render.yaml`:

```yaml
services:
  - type: web
    name: oat-flavor-app
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
```

---

## 🤝 Contributing

PRs welcome! Suggest features, fixes, or just ideas.

---

## 🧁 Built by [OTR15](https://github.com/OTR15)

Using Python + Flask + fuzzy logic + clean ingredients.
