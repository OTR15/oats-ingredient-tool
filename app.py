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
    flavor_query = None
    ingredient_query = None

    if request.method == 'POST':
        ingredient_aliases = load_aliases()
        variant_to_normal = get_variant_map(ingredient_aliases)
        all_ingredient_variants = list(variant_to_normal.keys()) + [i.lower() for i in all_ingredients]

        # If user submitted the flavor form
        if 'flavor_submit' in request.form:
            query = request.form['flavor_query'].strip()
            flavor_query = query
            query_lower = query.lower()

            matched_flavors = [f for f in all_flavors if query_lower in f.lower()]
            if query in flavor_to_ingredients:
                result = ("flavor", query, flavor_to_ingredients[query])
            elif len(matched_flavors) == 1:
                match = matched_flavors[0]
                result = ("flavor", match, flavor_to_ingredients[match])
            elif len(matched_flavors) > 1:
                suggestions = matched_flavors
            else:
                close_flavors = difflib.get_close_matches(query, all_flavors, n=5, cutoff=0.5)
                suggestions = close_flavors

            return render_template('index.html', result=result, suggestions=suggestions,
                                   flavor_query=flavor_query, ingredient_query=ingredient_query)

        # If user submitted the ingredient form
        if 'ingredient_submit' in request.form:
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
                flavors = set()
                for variant in all_variants:
                    flavors.update(ingredient_to_flavors.get(variant, []))
                if len(flavors) == len(all_flavors):
                    result = ("ingredient_all", normalized_query, sorted(flavors))
                elif len(flavors) == 0:
                    result = ("ingredient_none", normalized_query, [])
                else:
                    result = ("ingredient", normalized_query, sorted(flavors))
            elif query in ingredient_to_flavors:
                flavors = ingredient_to_flavors[query]
                if len(flavors) == len(all_flavors):
                    result = ("ingredient_all", query, flavors)
                elif len(flavors) == 0:
                    result = ("ingredient_none", query, flavors)
                else:
                    result = ("ingredient", query, flavors)
            else:
                matched_ingredients = [i for i in all_ingredients if query_lower in i.lower()]
                if len(matched_ingredients) == 1:
                    match = matched_ingredients[0]
                    flavors = ingredient_to_flavors.get(match, [])
                    result = ("ingredient", match, flavors)
                elif len(matched_ingredients) > 1:
                    suggestions = matched_ingredients
                else:
                    close_ingredients = difflib.get_close_matches(query, all_ingredient_variants, n=5, cutoff=0.5)
                    suggestions = close_ingredients

            return render_template('index.html', result=result, suggestions=suggestions,
                                   flavor_query=flavor_query, ingredient_query=ingredient_query)

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)