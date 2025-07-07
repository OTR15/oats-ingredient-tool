
from flask import Flask, render_template, request, send_file
import json
import difflib
import os
import re
from collections import defaultdict

app = Flask(__name__)

with open('data/flavor_to_ingredients.json') as f:
    flavor_to_ingredients = json.load(f)

with open('data/ingredient_to_flavors.json') as f:
    ingredient_to_flavors = json.load(f)

def load_aliases():
    with open('data/ingredient_aliases.json') as f:
        return json.load(f)

def get_variant_map(ingredient_aliases):
    vmap = {}
    for normal, variants in ingredient_aliases.items():
        for v in variants:
            vmap[v.lower()] = normal
    return vmap

def normalize_word(word):
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word)
    if word.endswith('ies'):
        word = word[:-3] + 'y'
    elif word.endswith('s') and not word.endswith('ss'):
        word = word[:-1]
    return word

def extract_normalized_tokens(ingredient):
    text = ingredient.lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = text.split()
    return [normalize_word(t) for t in tokens]

def build_token_index(ingredient_to_flavors):
    token_index = defaultdict(set)
    for ingredient, flavors in ingredient_to_flavors.items():
        tokens = extract_normalized_tokens(ingredient)
        for token in tokens:
            token_index[token].update(flavors)
    return token_index

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    suggestions = []
    flavor_query = None
    ingredient_query = None
    missing_flavors = []

    ingredient_aliases = load_aliases()
    variant_to_normal = get_variant_map(ingredient_aliases)
    token_index = build_token_index(ingredient_to_flavors)
    all_flavors = list(flavor_to_ingredients.keys())
    all_ingredients = list(ingredient_to_flavors.keys())
    all_ingredient_variants = list(variant_to_normal.keys()) + [i.lower() for i in all_ingredients]

    if request.method == 'POST':
        if 'flavor_submit' in request.form:
            query = request.form['flavor_query'].strip()
            flavor_query = query
            query_lower = query.lower()
            matched_flavors = [f for f in all_flavors if query_lower in f.lower()]
            if query in flavor_to_ingredients:
                result = ("flavor", query, flavor_to_ingredients[query])
            elif len(matched_flavors) == 1:
                result = ("flavor", matched_flavors[0], flavor_to_ingredients[matched_flavors[0]])
            elif len(matched_flavors) > 1:
                suggestions = matched_flavors
            else:
                suggestions = difflib.get_close_matches(query, all_flavors, n=5, cutoff=0.5)

        elif 'ingredient_submit' in request.form:
            query = request.form['ingredient_query'].strip()
            ingredient_query = query
            query_lower = query.lower()
            normalized_query = variant_to_normal.get(query_lower)

            if not normalized_query:
                for variant, normal in variant_to_normal.items():
                    if query_lower in variant:
                        normalized_query = normal
                        break

            if not normalized_query:
                close_match = difflib.get_close_matches(query_lower, variant_to_normal.keys(), n=1, cutoff=0.6)
                if close_match:
                    normalized_query = variant_to_normal[close_match[0]]

            matched_flavors = set()

            if normalized_query:
                all_variants = ingredient_aliases.get(normalized_query, [])
                for variant in all_variants:
                    matched_flavors.update(ingredient_to_flavors.get(variant, []))
            else:
                user_tokens = extract_normalized_tokens(query)
                for token in user_tokens:
                    matched_flavors.update(token_index.get(token, []))

            matched_flavors = sorted(matched_flavors)
            missing_flavors = sorted(set(all_flavors) - set(matched_flavors))

            if len(matched_flavors) == len(all_flavors):
                result = ("ingredient_all", normalized_query or query, matched_flavors)
            elif not matched_flavors:
                result = ("ingredient_none", normalized_query or query, [])
            else:
                result = ("ingredient", normalized_query or query, matched_flavors)

    return render_template('index.html', result=result, suggestions=suggestions,
                           flavor_query=flavor_query, ingredient_query=ingredient_query,
                           missing_flavors=missing_flavors)

@app.route('/aliases', methods=['GET', 'POST'])
def aliases_page():
    aliases = load_aliases()
    if request.method == 'POST':
        if 'add_new' in request.form:
            new_name = request.form['new_name'].strip()
            new_aliases = [a.strip() for a in request.form['new_aliases'].split(',') if a.strip()]
            if new_name and new_aliases:
                aliases[new_name] = new_aliases
        else:
            total = int(request.form['total'])
            updated = {}
            for i in range(total):
                name = request.form.get(f'name_{i}', '').strip()
                variants = request.form.get(f'alias_{i}', '').strip()
                if name and variants:
                    updated[name] = [v.strip() for v in variants.split(',') if v.strip()]
            aliases = updated
        with open('data/ingredient_aliases.json', 'w') as f:
            json.dump(aliases, f, indent=2)
    return render_template('alias_editor.html', aliases=aliases)

@app.route('/download-aliases')
def download_aliases():
    return send_file("data/ingredient_aliases.json", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
