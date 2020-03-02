import re
import random
import requests
import copy
from fractions import Fraction

import transformations

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

def reconstruct_ingredients(ingredients, original = False):
    intro = '\nYour ingredients were:\n' if original else '\nYour new ingredients are:\n'
    print(intro)
    i_copy = copy.deepcopy(ingredients)

    for ing in i_copy:
        q=i=p=d=m = False   # quantity, item, prep, desc, and measure trackers

        sentence = ing['string']
        for j in range(len(sentence)):
            if '{quantity}' in sentence[j] and not q:
                sentence[j] = sentence[j].replace('{quantity}', str(Fraction(float(ing['quantity'])).limit_denominator()))
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
        fixed_string = (re.sub(' +', ' ', ' '.join(sentence).replace(',,', ',')
                                                            .replace(' ,', ',')
                                                            .replace("''", 'inch')
                                                            .replace(' -', '-')
                                                            .replace(" '", "'")))

        print(fixed_string)

def reconstruct_directions(directions, original = False):
    intro = '\nYour steps were:\n' if original else '\nYour new steps are:\n'
    print(intro)
    d_copy = copy.deepcopy(directions)

    for l, step in enumerate(d_copy):
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

        print(f'{l+1}.', ' '.join(sentence).replace('  ', ' ').replace(',,', ' '))

def main():
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    while True:
        recipe_url = input("Please enter the URL of a recipe from allrecipes.com or enter [q] to quit.\n")

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
        
        print(f'\n{random.choice(openers)} {name}? {random.choice(closers)}')

        print('\n'+'*'*20)
        reconstruct_ingredients(o_ingredients, True)
        print('\n'+'-'*20)
        reconstruct_directions(o_directions, True)
        print()

        while True:
            for i,o in enumerate(options):
                print(f'[{i}] {o}')

            try:
                n = int(input('\nWhat do you want to do with it?\n'))
            except Exception:
                print('Please enter a valid number.')
                continue

            if n == 0:
                return
            elif n == 1:
                break
            elif n >= len(options):
                print(f'\nInvalid selection: {n}\n')
            else:
                new_trans = options[n].lower().replace(' ', '_')
                if new_trans == 'make_it_nonvegetarian' and any(h == 'make_it_vegetarian' for h in history):
                    for i in range(len(history)):
                        if 'make_it_vegetarian' == history[i]:
                            del history[i]
                            break

                    ingredients = copy.deepcopy(o_ingredients)
                    directions = copy.deepcopy(o_directions)
                    for h in history:
                        trans_fun = f"transformations.{h}(ingredients, directions)"
                        ingredients, directions = eval(trans_fun)

                elif new_trans == 'make_it_vegetarian' and any(h == 'make_it_nonvegetarian' for h in history):
                    for i in range(len(history)):
                        if 'make_it_nonvegetarian' == history[i]:
                            del history[i]
                            break

                    ingredients = copy.deepcopy(o_ingredients)
                    directions = copy.deepcopy(o_directions)
                    for h in history:
                        trans_fun = f"transformations.{h}(ingredients, directions)"
                        ingredients, directions = eval(trans_fun)

                else:
                    temp_i, temp_d = copy.deepcopy(ingredients), copy.deepcopy(directions)
                    trans_fun = f"transformations.{new_trans}(ingredients, directions)"
                    ingredients, directions = eval(trans_fun)
                    if temp_i != ingredients or temp_d != directions:
                        history.append(new_trans)

                print('\n'+'*'*20)
                reconstruct_ingredients(ingredients)
                print('\n'+'-'*20)
                reconstruct_directions(directions)
                print()

if __name__ == "__main__":
    main()
