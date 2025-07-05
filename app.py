from flask import Flask, render_template, request
import json
import difflib
import os

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

all_flavors = list(flavor_to_ingredients.keys())
all_ingredients = list(ingredient_to_flavors.keys())

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    suggestions = []
    query = ""

    if request.method == 'POST':
        query = request.form['query'].strip()
        query_lower = query.lower()

        ingredient_aliases = load_aliases()
        variant_to_normal = get_variant_map(ingredient_aliases)
        all_ingredient_variants = list(variant_to_normal.keys()) + [i.lower() for i in all_ingredients]

        # Try exact alias match first
        normalized_query = variant_to_normal.get(query_lower)

        # If not exact, try partial match to any alias variant
        if not normalized_query:
            for variant, normal in variant_to_normal.items():
                if query_lower in variant:
                    normalized_query = normal
                    break

        # Then, try fuzzy match to aliases
        if not normalized_query:
            close_match = difflib.get_close_matches(query_lower, variant_to_normal.keys(), n=1, cutoff=0.6)
            if close_match:
                normalized_query = variant_to_normal[close_match[0]]

        # If we found a normalized query, show all variants together
        if normalized_query:
            all_variants = ingredient_aliases.get(normalized_query, [])
            flavors = set()
            for variant in all_variants:
                flavors.update(ingredient_to_flavors.get(variant, []))
            if len(flavors) == len(all_flavors):
                result = ("ingredient_all", normalized_query, sorted(flavors))
            elif len(flavors) == 0:
                result = ("ingredient_none", normalized_query, [])
            else:
                result = ("ingredient", normalized_query, sorted(flavors))
        elif query in flavor_to_ingredients:
            result = ("flavor", query, flavor_to_ingredients[query])
        elif query in ingredient_to_flavors:
            flavors = ingredient_to_flavors[query]
            if len(flavors) == len(all_flavors):
                result = ("ingredient_all", query, flavors)
            elif len(flavors) == 0:
                result = ("ingredient_none", query, flavors)
            else:
                result = ("ingredient", query, flavors)
        else:
            matched_flavors = [f for f in all_flavors if query_lower in f.lower()]
            matched_ingredients = [i for i in all_ingredients if query_lower in i.lower()]
            suggestions = matched_flavors + matched_ingredients

            if not suggestions:
                close_flavors = difflib.get_close_matches(query, all_flavors, n=5, cutoff=0.5)
                close_ingredients = difflib.get_close_matches(query, all_ingredient_variants, n=5, cutoff=0.5)
                suggestions = close_flavors + close_ingredients

    return render_template('index.html', result=result, suggestions=suggestions, query=query)

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

if __name__ == '__main__':
    app.run(debug=True)
