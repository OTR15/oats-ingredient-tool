
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

def normalize_ingredient(text):
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r's$', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_token_index(ingredient_to_flavors):
    norm_index = defaultdict(set)
    for ingredient, flavors in ingredient_to_flavors.items():
        norm = normalize_ingredient(ingredient)
        norm_index[norm].update(flavors)
    return norm_index

token_index = build_token_index(ingredient_to_flavors)

all_flavors = list(flavor_to_ingredients.keys())
all_ingredients = list(ingredient_to_flavors.keys())

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    suggestions = []
    flavor_query = None
    ingredient_query = None

    if request.method == 'POST':
        ingredient_aliases = load_aliases()
        variant_to_normal = get_variant_map(ingredient_aliases)
        all_ingredient_variants = list(variant_to_normal.keys()) + [i.lower() for i in all_ingredients]

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

            if normalized_query:
                all_variants = ingredient_aliases.get(normalized_query, [])
                matched_flavors = set()
                for variant in all_variants:
                    matched_flavors.update(ingredient_to_flavors.get(variant, []))

                if len(matched_flavors) == len(all_flavors):
                    result = ("ingredient_all", normalized_query, sorted(matched_flavors))
                elif not matched_flavors:
                    result = ("ingredient_none", normalized_query, [])
                else:
                    result = ("ingredient", normalized_query, sorted(matched_flavors))

            else:
                norm_query = normalize_ingredient(query)
                token_matches = {ing: list(flavors) for ing, flavors in token_index.items() if norm_query in ing}
                if token_matches:
                    flavors = set()
                    for match_flavors in token_matches.values():
                        flavors.update(match_flavors)
                    result = ("ingredient", query, sorted(flavors))
                else:
                    matched_ingredients = [i for i in all_ingredients if query_lower in i.lower()]
                    if len(matched_ingredients) == 1:
                        result = ("ingredient", matched_ingredients[0], ingredient_to_flavors[matched_ingredients[0]])
                    elif len(matched_ingredients) > 1:
                        suggestions = matched_ingredients
                    else:
                        suggestions = difflib.get_close_matches(query, all_ingredient_variants, n=5, cutoff=0.5)

    return render_template('index.html', result=result, suggestions=suggestions,
                           flavor_query=flavor_query, ingredient_query=ingredient_query)

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