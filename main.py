import re
import random
import requests
import copy
from fractions import Fraction 

import nltk
import unicodedata

from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize
import numpy as np

def strip_accents(text):

    try:
        text = unicode(text, 'utf-8')
    except NameError: # unicode is a default on python 3 
        pass

    text = (unicodedata.normalize('NFD', text)
            .encode('ascii', 'ignore')
            .decode("utf-8"))

    return str(text)


def fetch_recipe(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser').body

    name = soup.find('h1', id='recipe-main-content').text
    recipe = (soup.find('section', class_='ar_recipe_index'))

    ingredients = parse_ingredients(recipe)
    directions = parse_directions(scrape_directions(recipe), ingredients)

    return name, ingredients, directions

def parse_ingredients(recipe):
    nltk.download('punkt')
    ing_lists = recipe.find_all('ul', id=re.compile(r'lst_ingredients.*'))
    ingredients = []
    for sub_list in ing_lists:
        ingredients += [i.lower() for i in [scrape_ingredient(i) for i in sub_list] if i]
    pos_ings = [nltk.pos_tag(word_tokenize(i)) for i in ingredients]

    measurements = set()
    ing_stats = []
    for i, split_ing in enumerate(pos_ings):
        ing_dict = {'string':'', 'quantity':'', 'measure':'', 'item':'', 'prep':'', 'descriptor':''}
        item = []
        string = [''] * len(split_ing)
        for j, part in enumerate(split_ing):
            if j == 0 and part[1] == 'CD': # the first thing is always a number
                ing_dict['quantity'] = str(eval(part[0]))
                string[j] = '{quantity}'
            elif j == 1 and part[1] == 'CD' and not any(part[0] in v for v in ing_dict.values()): # there might be a fractional quantity, get it if its not already used
                ing_dict['quantity'] = str(float(ing_dict['quantity']) + eval(part[0]))
                string[j] = '{quantity}'

            elif split_ing[j-1][1] == 'CD' and part[0] == '(': # either look for paranthesis for measurements
                m = re.search(r'\(.*?\)', ingredients[i])
                if m:
                    m = m.group()
                else:
                    continue
                if ing_dict['quantity']:
                    word = None
                    for k in range(j, len(split_ing)):
                            if split_ing[k-1][0] == ')':
                                word = split_ing[k]
                                break
                    if float(ing_dict['quantity']) > 1 and word[0] in ['cans', 'packages', 'jiggers', 'bottles', 'jars', 'pieces', 'bags', 'envelopes']:
                        ing_dict['measure'] = m + ' ' + word[0]
                    elif float(ing_dict['quantity']) <= 1 and word[0] in ['can', 'package', 'jigger', 'bottle', 'jar', 'piece', 'bag', 'envelope']:
                        ing_dict['measure'] = m + ' ' + word[0]
                    else:
                        ing_dict['measure'] = m

                if not ing_dict['measure']:
                    ing_dict['measure'] = m
                    measurements.add(m)
            elif (split_ing[j-1][1] == 'CD' # or look for the thing directly following a number
                and ((part[1] == 'NNS' and float(ing_dict['quantity']) > 1) 
                    or (part[1] == 'NN' and float(ing_dict['quantity']) <= 1))
                    or (part[1] == 'JJ' and part[0] in measurements and not ing_dict['measure'])):
                if not ing_dict['measure']:
                    ing_dict['measure'] = part[0]
                    measurements.add(part[0])
                    string[j] = '{measure}'

            elif part[0] == ',': # look for any prep after a comma
                sub = split_ing[j+1:]
                if any(s[1] in ['VB', 'VBD', 'VBN', 'VBG'] for s in sub):
                    ing_dict['prep'] += ' '.join([s[0] for s in sub])
                    string[j] = '{prep}'
                break

        for k, part in enumerate(split_ing): # get every unused thing and use it as the item
            if len(part[0]) <= 1:
                continue

            if part[0] in ing_dict['measure']:
                string[k] = '{measure}'
            elif part[0] in ing_dict['prep']:
                string[k] = '{prep}'
            elif not any(part[0] in v for v in ing_dict.values()) and part[1] != 'CD':
                item += [part[0]]
                string[k] = '{item}'
            
            if k < len(split_ing) - 1 and split_ing[k+1][0] == ',':
                string[k] += ','


        if item:
            ing_dict['item'] = ' '.join(item)
        else:
            ing_dict['item'] = ing_dict['measure']
        ing_dict['string'] = string

        ing_stats.append(ing_dict)

    return ing_stats

def scrape_ingredient(ingredient):

    label = ingredient.find('label')

    if label != -1:
        ng_class = label.attrs.get('ng-class')
        if ng_class and 'false' in label.attrs.get('ng-class'):
            return None
        return label.attrs.get('title')

    return None

def parse_directions(directions, ingredient_stats):
    tools = ["knife", "spoon", "bowl", 'muffin pan', 'cake pan', 'baking sheet', "pan", 
            "pot", "whisk", "peeler", "cutting board", "can opener", "measuring cup", 
            "measuring spoon", "plate", "colander", "masher", "grater", 'spatula',
            'tongs', 'oven mitts', 'ladle', 'thermometer', 'blender', 'aluminum foil', 
            'parchment paper', 'oven', 'dutch oven', 'skillet', 'sauce pan']

    tools = sorted(tools, key=lambda x: len(x.split()), reverse=True)

    primary_methods = ['saute', 'simmer', 'boil', 'poach', 'bake', 'broil', 'grill', 'stew', 'braise', 'roast', 'sear', 
                        'blanche', 'smoke', 'brine', 'barbecue', 'caramelize', 'fry', 'deep fry', 'stir fry', 'pan fry', 
                        'fillet', 'sous-vide']

    secondary_methods = ['chop', 'grate', 'stir', 'shake', 'mince', 'crush', 'squeeze', 'brown', 'baste', 'drain', 
                        'cream', 'mix', 'dip', 'dry', 'frost', 'garnish', 'glaze', 'julienne', 'juice', 'press', 
                        'microwave', 'marinate', 'pickle', 'puree', 'reduce', 'reduction', 'season', 'separate', 
                        'beat', 'shuck', 'skim', 'stuff', 'melt', 'tenderize', 'thicken', 'whisk', 'combine',
                        'cover', 'refridgerate', 'break']

    split_steps = []
    ingredients = [i['item'] for i in ingredient_stats]

    for direction in directions:
        step_stats = {'string':'', 'tools':[], 'methods':[], 'ingredients':[], 'times':[]}
        split_step = direction.lower().split()

        for i in range(len(split_step)):
            o_word = split_step[i]
            if ',' in o_word:
                end = ','
            elif '.' in o_word:
                end = '.'
            else:
                end = ''
            word = re.sub(r'\W+', '', o_word)

            if any(f' {word} ' in f' {t} ' for t in tools):
                for t in tools:
                    if f' {word} ' in f' {t} ':
                        split_t = t.split()
                        if len(split_t) > 1:
                            idx = split_t.index(word)
                            j = 0
                            for j in range(len(split_t)):
                                if split_t[j] != split_step[i+j]:
                                    break
                            else:
                                split_step[i] = '{tool}'+end
                                split_step[i+1:i+j+1] = ['']*((i+j+1)-(i+1))
                                step_stats['tools'] += [t]
                        else:
                            split_step[i] = '{tool}'+end
                            step_stats['tools'] += [t]

            elif any(f' {word} ' in f' {m} ' for m in primary_methods) or any(f' {word} ' in f' {m} ' for m in secondary_methods):
                step_stats['methods'].append(word)
                split_step[i] = '{method}'+end

            elif any(any(word == part for part in ingredient.lower().split()) for ingredient in ingredients):
                step_stats['ingredients'].append(word)

            elif word.isdigit() and re.sub(r'\W+', '', split_step[i+1]) in ['hours', 'hour', 'minutes', 'minute', 'seconds']:
                step_stats['times'].append(word)
                split_step[i] = '{time}'+end

        step_stats['string'] = ' '.join(split_step)
        split_steps.append(step_stats)

    return split_steps

def scrape_directions(recipe):
    dir_list = recipe.find('ol', class_='recipe-directions__list').find_all('li')
    return [d.span.text.strip() for d in dir_list]

def double_it(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions
    for i in range(len(ingredients)):
        try:
            old_num = float(t_ingredients[i]['quantity'])
            t_ingredients[i]['quantity'] = str(float(t_ingredients[i]['quantity']) * 2)
            if 0.5 < old_num and old_num <= 1:
                temp = 'measure'
                if not t_ingredients[i][temp]:
                    temp = 'item'

                if t_ingredients[i][temp][-1] == ')':
                    continue

                if t_ingredients[i][temp][-2:] in ['ch', 'sh'] or t_ingredients[i][temp][-1] in ['s', 'x', 'z', 'o']:
                    t_ingredients[i][temp] += 'es'
                elif 'loaf' in t_ingredients[i][temp]:
                    t_ingredients[i][temp] = t_ingredients[i][temp].replace('loaf', 'loaves')
                elif 'shrimp' not in t_ingredients[i][temp]:
                    t_ingredients[i][temp] += 's'
        except ValueError:
            pass

    return t_ingredients, t_directions

def half_it(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions
    for i in range(len(ingredients)):
        try:
            old_num = float(t_ingredients[i]['quantity'])
            t_ingredients[i]['quantity'] = str(float(t_ingredients[i]['quantity']) / 2)
            if 2 >= old_num and old_num > 1:
                temp = 'measure'
                if not t_ingredients[i][temp]:
                    temp = 'item'
                if t_ingredients[i][temp][-4:] in ['ches', 'shes'] or t_ingredients[i][temp][-3:] in ['xes', 'zes', 'oes']:
                    t_ingredients[i][temp] = t_ingredients[i][temp][:-2]
                elif 'loaves' in t_ingredients[i][temp]:
                    t_ingredients[i][temp] = t_ingredients[i][temp].replace('loaves', 'loaf')
                elif t_ingredients[i][temp][-1] == 's':
                    t_ingredients[i][temp] = t_ingredients[i][temp][:-1]
        except ValueError:
            pass

    return t_ingredients, t_directions

def make_it_vegetarian(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    meats = ['beef', 'pork',  'lamb',  'veal',  'bison', 'turkey', 'chicken']

    birds = ['chicken', 'turkey', 'duck', 'goose', 'drumstick', 'wing', 'thigh', 'rabbit', 'frog', 'breast'] # replace with tofurky

    tempeh = ['salami', 'pepperoni', 'sausage', 'spam', 'liver', ' ham', 'bacon']

    fish = ['sockeye', 'sardine', 'mackerel', 'shad', ' eel','pollock', 'flounder', 'trout',  'crawfish', 'crayfish', 'rockfish',
            'bream', 'walleye', 'lightfish', 'carp', 'sturgeon', 'yellowtail', 'snapper', 'herring', 'perch', 'tilapia', 'tuna',
            'fish','salmon','anchovy', ' cod',  'halibut', 'bass', 'sardine'] # replace with tofu

    etc_fish = ['squid', 'octopus', 'cuddlefish', 'oyster', 'scallop', 'clam', 'mussel', 'shrimp'] # replace with king oyster mushrooms

    misc_sea = ['lobster', 'crab'] # replace with lobster mushrooms

    replacement = {}
    v = ['tempeh', 'mushrooms', 'mushroom', 'tofu', 'tofurky']

    for ing in t_ingredients:
        temp = ing['item']

        if 'broth' in ing['item']:
            ing['item'] = 'veggie broth'
        elif 'stock' in ing['item']:
            ing['item'] = 'veggie stock'
        elif 'steak' in ing['item']:
            ing['item'] = 'cauliflower steak'
        elif 'ground' in ing['item'] and any(m in ing['item'] for m in meats):
            ing['item'] = 'impossible ground beef'
        elif any(b in ing['item'] for b in birds):
            ing['item'] = 'tofurky'
        elif any(f in ing['item'] for f in fish):
            ing['item'] = 'tofu'
        elif any(e in ing['item'] for e in etc_fish):
            ing['item'] = 'king oyster mushrooms'
        elif any(t in ing['item'] for t in tempeh):
            ing['item'] = 'tempeh'
        elif any(s in ing['item'] for s in misc_sea):
            ing['item'] = 'lobster mushrooms'
        elif any(m in ing['item'] for m in meats):
            ing['item'] = 'tofu'
        else:
            continue

        ing['prep'] = []
        replacement[temp] = ing['item']
        if ing['measure'] and ing['measure'][-1] == ')':
            ing['measure'] += (' packages' if float(ing['quantity']) > 1 else ' package')

    w = (' '.join(replacement.keys())).split()

    for step in t_directions:
        sentence = step['string'].split()
        for i in range(len(sentence)):

            if i > 0 and sentence[i] in w and sentence[i-1] in v:
                sentence[i] = ''

            if sentence[i] == 'meat' or sentence[i] == 'fish':
                sentence[i] = list(replacement.values())[0]

            if any(b in sentence[i] for b in birds):
                sentence[i] = 'tofurky'
            elif any(f in sentence[i] for f in fish):
                sentence[i] = 'tofu'
            elif any(e in sentence[i] for e in etc_fish):
                sentence[i] = 'king oyster mushrooms'
            elif any(t in sentence[i] for t in tempeh):
                sentence[i] = 'tempeh'
            elif any(s in sentence[i] for s in misc_sea):
                sentence[i] = 'lobster mushrooms'
            elif any(m in sentence[i] for m in meats):
                sentence[i] = 'tofu'
            else:
                continue

        step['string'] = (' '.join(sentence)).replace('  ', ' ')

    return t_ingredients, t_directions

def make_it_nonvegetarian(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    if any('bacon bits' in b['item'] for b in t_ingredients): # already transformed
        return t_ingredients, t_directions

    for i in range(len(t_ingredients)):
        if 'eggplant' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
        elif 'tofu' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
        elif 'jackfruit' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
        elif 'tempeh' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
        elif 'mushroom' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
        elif 'tofurky' in t_ingredients[i]['item']:
            t_ingredients[i]['item'] = 'ground beef'
            break
    else:
        ing_dict = {'string':'{item}', 'quantity':'', 'measure':'', 'item': 'bacon bits to taste', 'prep':'', 'descriptor':''}
        dir_dict =  {'string':'{method} bacon bits until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':[], 'times':[]}
        t_ingredients.append(ing_dict)
        t_directions.append(dir_dict)
        return t_ingredients, t_directions

    if t_ingredients[i]['measure'] and t_ingredients[i]['measure'][-1] == ')':
        t_ingredients[i]['measure'] += ' packages' if float(t_ingredients[i]['quantity']) > 1 else ' package'

    for step in t_directions:
        sentence = step['string'].split()
        for k in range(len(sentence)):
            if 'eggplant' in sentence[k]:
                sentence[k] = 'ground beef'
            elif 'tofu' in sentence[k]:
                sentence[k] = 'ground beef'
            elif 'jackfruit' in sentence[k]:
                sentence[k] = 'ground beef'
            elif 'tempeh' in sentence[k]:
                sentence[k] = 'ground beef'
            elif 'mushroom' in sentence[k]:
                sentence[k] = 'ground beef'
            elif 'tofurky' in sentence[k]:
                sentence[k] = 'ground beef'
            else:
                continue
        
            step['string'] = (' '.join(sentence)).replace('  ', ' ')

    return t_ingredients, t_directions

def make_it_japanese(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    sweet = ['sugar', 'fruit', 'honey', 'cream', 'chocolate', 'fudge', 'marshmallow', 'caramel', 'syrup', 'sweet']
    savor = ['vegetable', 'cabbage', 'mushroom', 'onion', 'peppers', 'tofu', 'cauliflower', 'eggplant', 
            'broth', 'steak', 'meat', 'fish', 'beef', 'pork', 'chicken', 'salt', 'pepper', 'tempeh', 'tofurky',
            'vinegar', 'ketchup', 'mayo', 'mustard', 'gravy', 'dressing', 'hot sauce', 'sriracha', 'tobasco', 
            'barbecue', 'spinach', 'salad' ,'olive oil']

    recipe_sweet = 0
    recipe_savor = 0

    for step in t_directions:
        for s in step['string'].split():
            if any(sw in s for sw in sweet):
                recipe_sweet += 1
            if any(sv in s for sv in savor):
                recipe_savor += 1
    for ing in t_ingredients:
        if any(s in ing['item'] for s in sweet):
            recipe_sweet += 1
        if any(s in ing['item'] for s in savor):
            recipe_savor += 1

    print('\n\n\n')
    print('sweety:', recipe_sweet)
    print('savory:', recipe_savor)
    print('\n\n\n')
        
    for d in t_directions:
        d['string'].replace('lemon', 'yuzu').replace('lime', 'yuzu').replace('orange', 'mikan')
    for i in t_ingredients:
        if 'lemon' in i['item'] or 'lime' in i['item']:
            i['item'].replace('lemon', 'yuzu').replace('lime', 'yuzu').replace('orange', 'mikan')

    if recipe_sweet > 0 and recipe_savor <= 4: # sweet
        for i in t_ingredients:
            if 'flour' in i['item']:
                i['item'] = 'mochiko flour'
            if 'sugar' in i['item']:
                i['item'] = 'wasanbon sugar'

        ing_dict = {'string':'{item} {desc}', 'quantity':'', 'measure':'', 'item': 'kinako to taste', 'prep':'', 'descriptor':'(optional)'}
        dir_dict =  {'string':'{method} kinako until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['kinako'], 'times':[]}
        t_ingredients.append(ing_dict)
        t_directions.append(dir_dict)
    else: # savory 
        if any('meat' in d['string'] for d in t_directions):
            t_ingredients.append({'string':'{quantity} {measure} {item}, desc', 'quantity':'0.5', 'measure':'cup', 'item':'teriyaki sauce', 'prep':'', 'descriptor':'or to taste'})
            t_directions.insert(0, {'string':'{method} the meat for {time} minutes.', 'tools':[], 'methods':['marinate'], 'ingredients':['meat'], 'times':['20']})

        for i in t_ingredients:
            if 'dressing' in i['item']:
                i['item'] = 'wafu dressing'
            if 'breadcrumbs' in i['item']:
                i['item'] = 'panko breadcrumbs'
            if 'vinegar' in i['item']:
                i['item'] = 'rice vinegar'
            if 'broth' in i['item']:
                i['item'] = 'dashi broth'
            if 'stock' in i['item']:
                i['item'] = 'dashi stock'
            if 'hot sauce' in i['item']:
                i['item'] = 'wasabi hot sauce'
            if 'beans' in i['item']:
                i['item'] = 'edamame beans'
            if 'sugar' in i['item']:
                i['item'] = 'brown sugar'

        ing_dict = {'string':'furikake to taste (optional)', 'quantity':'', 'measure':'', 'item': 'furikake to taste', 'prep':'', 'descriptor':'(optional)'}
        dir_dict =  {'string':'{method} furikake until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['furikake'], 'times':[]}
        t_ingredients.append(ing_dict)
        t_directions.append(dir_dict)

    return t_ingredients, t_directions

def make_it_indian(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    sweet = ['sugar', 'fruit', 'honey', 'cream', 'chocolate', 'fudge', 'marshmallow', 'caramel', 'syrup']
    savor = ['vegetable', 'cabbage', 'mushroom', 'onion', 'peppers', 'tofu', 'cauliflower', 'eggplant', 
            'broth', 'steak', 'meat', 'fish', 'beef', 'pork', 'chicken', 'salt', 'pepper', 'tempeh', 'tofurky',
            'vinegar', 'ketchup', 'mayo', 'mustard', 'gravy', 'dressing', 'hot sauce', 'sriracha', 'tobasco', 
            'barbecue', 'spinach', 'salad', 'olive oil']

    recipe_sweet = 0
    recipe_savor = 0

    for step in t_directions:
        if any(s in step['string'] for s in sweet):
            recipe_sweet += 1
        elif any(s in step['string'] for s in savor):
            recipe_savor += 1
    for ing in t_ingredients:
        if any(s in ing['item'] for s in sweet):
            recipe_sweet += 1
        elif any(s in ing['item'] for s in savor):
            recipe_savor += 1
        
    for d in t_directions:
        d['string'].replace('butter', 'ghee')
    for i in t_ingredients:
        i['item'].replace('butter', 'ghee')

    if recipe_sweet > 0 and recipe_savor <= 4: # sweet
        for i in t_ingredients:
            if 'flour' in i['item']:
                i['item'] = random.choice(['maida flour', 'chick pea flour'])
            if 'sugar' in i['item']:
                i['item'] = 'jaggery sugar'

        ing_dict = {'string':'{item} {desc}', 'quantity':'', 'measure':'', 'item': 'crushed pistachios to taste', 'prep':'', 'descriptor':'(optional)'}
        dir_dict =  {'string':'{method} crushed pistachios until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['pistachios'], 'times':[]}
        t_ingredients.append(ing_dict)
        t_directions.append(dir_dict)
    else: # savory 
        if any('meat' in d['string'] for d in t_directions):
            t_ingredients.append({'string':'{quantity} {measure} {item}, {desc}', 'quantity':'0.5', 'measure':'cup', 'item':'teriyaki sauce', 'prep':'', 'descriptor':'or to taste'})
            t_directions.insert(0, {'string':'{method} the meat for {time} minutes.', 'tools':[], 'methods':['marinate'], 'ingredients':['meat'], 'times':['20']})

        for i in t_ingredients:
            if 'yogurt' in i['item']:
                i['item'] = 'dahi yogurt'
            if 'pepper' in i['item']:
                i['item'] = 'mirchi chile pepper'
            if 'dressing' in i['item']:
                i['item'] = 'masala dressing'
            if 'beans' in i['item']:
                i['item'] = 'lentils'
            if 'broth' in i['item']:
                i['item'] = 'mutton broth'
            if 'stock' in i['item']:
                i['item'] = 'mutton stock'
            if 'hot sauce' in i['item']:
                i['item'] = 'spicy chutney sauce'
            if 'rice' in i['item']:
                i['item'] = 'basmati rice'
            if 'pecans' in i['item']:
                i['item'] = 'crushed pistachios'
            if 'paprika' in i['item']:
                i['item'] = 'coriander seeds'

        ing_dict = {'string':'{item} {desc}', 'quantity':'', 'measure':'', 'item': 'curry powder to taste', 'prep':'', 'descriptor':'(optional)'}
        dir_dict =  {'string':'{method} curry powder until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['curry powder'], 'times':[]}
        t_ingredients.append(ing_dict)
        t_directions.append(dir_dict)

    return t_ingredients, t_directions

def make_it_healthy(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    unhealthies = ['oil', 'salt', 'sugar', 'sauce', 'ketchup', 'mayo', 'butter', 'mustard', 'honey', 'chocolate', 'cream', 'fudge', 'marshmallow', 'caramel',
                    'yogurt', 'shortening', 'syrup', 'milk', 'cheese', 'seasoning', 'powder', 'molasses', 'beer', 'wine', 'gravy', 'dressing']

    for ing in t_ingredients:
        if any(u in ing['item'] for u in unhealthies):
            ing['quantity'] = str(float(ing['quantity']) * 0.5)

    return t_ingredients, t_directions

def make_it_unhealthy(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    unhealthies = ['oil', 'salt', 'sugar', 'sauce', 'ketchup', 'mayo', 'butter', 'mustard', 'honey', 'chocolate', 'cream', 'fudge', 'marshmallow', 'caramel',
                    'yogurt', 'shortening', 'syrup', 'milk', 'cheese', 'seasoning', 'powder', 'molasses', 'beer', 'wine', 'gravy', 'dressing']

    for ing in t_ingredients:
        if any(u in ing['item'] for u in unhealthies):
            ing['quantity'] = str(float(ing['quantity']) * 2)

    return t_ingredients, t_directions



def reconstruct_ingredients(ingredients):
    print('\nYour new ingredients are:\n')

    for ing in ingredients:
        q=i=p=d=m = False   # quantity, item, prep, desc, and measure trackers

        sentence = ing['string']
        for j in range(len(sentence)):
            if '{quantity}' in sentence[j] and not q:
                sentence[j] = sentence[j].replace('{quantity}', str(Fraction(float(ing['quantity']))))
                q = True
            elif '{prep}' in sentence[j] and not p:
                sentence[j] = sentence[j].replace('{prep}', ing['prep'])
                p = True
            elif '{desc}' in sentence[j] and not d:
                sentence[j] = sentence[j].replace('{desc}', ing['descriptor'])
                d = True
            elif '{measure}' in sentence[j] and not m:
                sentence[j] = sentence[j].replace('{measure}', ing['measure'])
                m = True
            elif '{item}' in sentence[j] and not i:
                sentence[j] = sentence[j].replace('{item}', ing['item']+',') if ing['prep'] else sentence[j].replace('{item}', ing['item'])
                i = True

        sentence = list(filter(lambda word: not '{' in word, sentence))

        print(' '.join(sentence))

def reconstruct_directions(directions):
    print('\nYour new steps are:\n')

    for step in directions:
        tools=methods=times = 0   # tools, methods, and times counters

        sentence = step['string'].split()
        for j in range(len(sentence)):
            if '{tool}' in sentence[j] and tools < len(step['tools']):
                sentence[j] = sentence[j].replace('{tool}', step['tools'][tools])
                tools += 1
            elif '{method}' in sentence[j] and methods < len(step['methods']):
                sentence[j] = sentence[j].replace('{method}', step['methods'][methods])
                methods += 1
            elif '{time}' in sentence[j] and times < len(step['times']):
                sentence[j] = sentence[j].replace('{time}', step['times'][times])
                times += 1

            if j == 0 or '.' in sentence[j-1]:
                sentence[j] = sentence[j].capitalize()

        print(' '.join(sentence))

def main():
    while True:
        recipe_url = input("Please enter the URL of a recipe from allrecipes.com or enter [q] to quit.\n")
        # recipe_url = 'https://www.allrecipes.com/recipe/213268/classic-goulash/'
        # recipe_url = 'https://www.allrecipes.com/recipe/256662/jackfruit-curry-kathal-subzi/'
        # recipe_url = 'https://www.allrecipes.com/recipe/14069/vegan-lasagna-i/'
        recipe_url = 'https://www.allrecipes.com/recipe/77215/roasted-beets-n-sweets/'
        # recipe_url = 'https://www.allrecipes.com/recipe/212636/japanese-beef-stir-fry/'
        # recipe_url = 'https://www.allrecipes.com/recipe/220067/3-cheese-eggplant-lasagna/'
        # recipe_url = 'https://www.allrecipes.com/recipe/273326/parmesan-crusted-shrimp-scampi-with-pasta/'
        # recipe_url = 'https://www.allrecipes.com/recipe/230117/gluten-free-thanksgiving-stuffing/'
        # recipe_url = 'https://www.allrecipes.com/recipe/88921/shrimp-wellington/'
        # recipe_url = 'https://www.allrecipes.com/recipe/268669/creamy-shrimp-scampi-with-half-and-half/'
        # recipe_url = 'https://www.allrecipes.com/recipe/257914/taro-boba-tea/'
        # recipe_url = 'https://www.allrecipes.com/recipe/193307/easy-mochi/'
        # recipe_url = 'https://www.allrecipes.com/recipe/266015/boba-coconut-milk-black-tea-with-tapioca-pearls/'
        # recipe_url = 'https://www.allrecipes.com/recipe/222340/chef-johns-roast-christmas-goose/'
        # recipe_url = 'https://www.allrecipes.com/recipe/109297/cedar-planked-salmon/'
        # recipe_url = 'https://www.allrecipes.com/recipe/132814/easy-yet-romantic-filet-mignon/'
        # recipe_url = 'https://www.allrecipes.com/recipe/212892/alligator-animal-italian-bread/'
        # recipe_url = 'https://www.allrecipes.com/recipe/232908/chef-johns-meatless-meatballs/'
        # recipe_url = 'https://www.allrecipes.com/recipe/235901/peppercorn-roast-beef/'
        # recipe_url = 'https://www.allrecipes.com/recipe/255545/ground-turkey-taco-meat/'
        # recipe_url = 'https://www.allrecipes.com/recipe/16409/spinach-and-strawberry-salad/'

        if recipe_url == 'q':
            return
        if 'allrecipes.com/recipe' not in recipe_url:
            continue

        name, o_ingredients, o_directions = fetch_recipe(recipe_url)
        ingredients = copy.deepcopy(o_ingredients)
        directions = copy.deepcopy(o_directions)
        fresh = True

        openers = ['Wow!', 'Oh,', 'Huh,', 'Mmm,']
        closers = ['Sounds tasty!', 'Smells delicious.', 'Looks great!']
        options = ['Exit', 'Enter a new recipe', 'Make it vegetarian', 'Make it nonvegetarian',
                    'Make it healthy', 'Make it unhealthy', 'Make it Japanese', 'Make it Indian',
                    'Double it', 'Half it']
        history = []
        
        print(f'\n{random.choice(openers)} {name}? {random.choice(closers)}\n')

        reconstruct_ingredients(o_ingredients)
        print()
        reconstruct_directions(o_directions)

        while True:
            for i,o in enumerate(options):
                print(f'[{i}] {o}')

            n = int(input('\nWhat do you want to do with it?\n'))

            if n == 0:
                return
            elif n == 1:
                break
            elif n >= len(options):
                print(f'\nInvalid selection: {n}\n')
            else:
                new_trans = options[n].lower().replace(' ', '_')
                if 'nonvegetarian' in new_trans and any(h == 'make_it_vegetarian' for h in history):
                    for i in range(len(history)):
                        if 'make_it_vegetarian' == history[i]:
                            del history[i]
                            break

                    ingredients = copy.deepcopy(o_ingredients)
                    directions = copy.deepcopy(o_directions)
                    for h in history:
                        trans_fun = f"{h}(ingredients, directions)"
                        ingredients, directions = eval(trans_fun)

                elif 'vegetarian' in new_trans and any(h == 'make_it_nonvegetarian' for h in history):
                    for i in range(len(history)):
                        if 'make_it_nonvegetarian' == history[i]:
                            del history[i]
                            break

                    ingredients = copy.deepcopy(o_ingredients)
                    directions = copy.deepcopy(o_directions)
                    for h in history:
                        trans_fun = f"{h}(ingredients, directions)"
                        ingredients, directions = eval(trans_fun)

                else:
                    temp_i, temp_d = copy.deepcopy(ingredients), copy.deepcopy(directions)
                    trans_fun = f"{new_trans}(ingredients, directions)"
                    ingredients, directions = eval(trans_fun)
                    if temp_i != ingredients or temp_d != directions:
                        history.append(new_trans)

                print('\n'+'*'*20)
                reconstruct_ingredients(ingredients)
                print('\n'+'-'*20)
                reconstruct_directions(directions)
                print()

'''
NOTES

MAYBE JUST MAYBE
We can keep a history of all transformations, and if two opposite transformations happen, remove them from the history and rerun all trans on the og ingredients and steps

For Parsing into steps, maybe slice the og stuff out, transform separately, then splice it back in

MAYBE JUST MAYBE
Pull a bunch of recipes from allrecipes with the same genre as the desired transformation
Then scrape the stuff from it

--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------

?? *** To/From Vegan

'''

if __name__ == "__main__":
    main()
