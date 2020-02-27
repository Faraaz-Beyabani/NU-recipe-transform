import re
import random
import requests
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
        ingredients += [i for i in [scrape_ingredient(i) for i in sub_list] if i]
    pos_ings = [nltk.pos_tag(word_tokenize(i)) for i in ingredients]

    measurements = set()
    ing_stats = []
    for i, split_ing in enumerate(pos_ings):
        ing_dict = {'string':'', 'quantity':'', 'measure':'', 'item':'', 'prep':'', 'descriptor':[]}
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
                m = re.search(r'\(.*?\) [a-zA-Z]*', ingredients[i]).group()
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

        if item:
            ing_dict['item'] = ' '.join(item)
        else:
            ing_dict['item'] = ing_dict['measure']
        ing_dict['string'] = string

        ing_stats.append(ing_dict)

    # for i in range(len(pos_ings)):
    #     print(pos_ings[i])
    #     print(ing_stats[i])
    #     print('\n')
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

    # s = [sent_tokenize(i) for i in directions]
    # w = [nltk.ne_chunk(nltk.pos_tag(word_tokenize(i))) for i in directions]
    # print(w)

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
            word = re.sub(r'\W+', '', o_word)
            end = ''
            if ',' in o_word:
                end = ','
            elif '.' in o_word:
                end = '.'

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
                                split_step[i] = '{tool}'
                                split_step[i+1:i+j+1] = ['']*((i+j+1)-(i+1))
                                step_stats['tools'] += [t]
                        else:
                            split_step[i] = '{tool}'

            elif any(f' {word} ' in f' {m} ' for m in primary_methods) or any(f' {word} ' in f' {m} ' for m in secondary_methods):
                step_stats['methods'].append(word)
                split_step[i] = '{method}'+end

            elif any(any(word == part for part in ingredient.lower().split()) for ingredient in ingredients):
                step_stats['ingredients'].append(word)
                split_step[i] = '{ingredient}'+end

            elif word.isdigit() and re.sub(r'\W+', '', split_step[i+1]) in ['hours', 'hour', 'minutes', 'minute', 'seconds']:
                step_stats['times'].append(word)
                split_step[i] = '{time}'+end

        step_stats['string'] = ' '.join(split_step)
        split_steps.append(step_stats)

    # for x in split_steps:
    #     print(x)

    return split_steps

def scrape_directions(recipe):
    dir_list = recipe.find('ol', class_='recipe-directions__list').find_all('li')
    return [d.span.text.strip() for d in dir_list]

def reconstruct_ingredients(ingredients):
    item = 0
    prep = 0
    desc = 0
    meas = 0

def reconstruct_directions(directions):
    tool = 0
    method = 0
    ingredients = 0
    times = 0

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
                if t_ingredients[i][temp][-2:] in ['ch', 'sh'] or t_ingredients[i][temp][-1] in ['s', 'x', 'z', 'o']:
                    t_ingredients[i][temp] += 'es'
                elif 'loaf' in t_ingredients[i][temp]:
                    t_ingredients[i][temp] = t_ingredients[i][temp].replace('loaf', 'loaves')
                elif 'shrimp' not in t_ingredients[i][temp]:
                    t_ingredients[i][temp] += 's'
        except ValueError:
            pass

    print(t_ingredients)
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

    print(t_ingredients)
    return t_ingredients, t_directions

def make_it_vegetarian(ingredients, directions):
    t_ingredients = ingredients
    t_items = [i['item'] for i in t_ingredients]
    t_directions = directions
    meats = ['beef', 'pork', ' ham',  'lamb', 'sausage', 'veal',  'bison', 
             'fillet', 'filet', 'rib', 'sirloin', 'heart', 'brain', 'breast', 
             'steak', 'brisket', 'shank', 'flank', 'tenderloin', 'ribeye', 'mignon', 'skirt', 't-bone', 'belly', 
             'shoulder', 'head', 'spare rib', 'thigh', 'liver', 'giblets',  'wagyu', 'loin', 'spam']

    birds = ['chicken', 'turkey', 'duck', 'goose', 'drumstick', 'wing', 'rabbit', 'frog', 'leg'] # replace with tofurky

    tempeh = ['salami', 'pepperoni']

    fish = ['sockeye', 'sardine', 'mackerel', 'shad', ' eel','pollock', 'flounder', 'trout',  'crawfish', 'crayfish', 'rockfish',
            'bream', 'walleye', 'lightfish', 'carp', 'sturgeon', 'yellowtail', 'snapper', 'herring', 'perch', 'tilapia', 'tuna',
            'fish','salmon','anchovy', ' cod',  'halibut', 'bass', 'sardine'] # replace with tofu

    etc_fish = ['squid', 'octopus', 'cuddlefish', 'oyster', 'scallop', 'clam', 'mussel', 'shrimp'] # replace with king oyster mushrooms

    trans_meat = {'bacon':'tempeh bacon', 'lobster':'lobster mushrooms', 'crab':'lobster mushrooms'} # 1:1 replacements


    print(t_ingredients)
    print(t_directions)
    if ingredient in any(meats):
        ingredient = 'lab-grown ' + ingredient

    return t_ingredients, t_directions

def main():
    while True:
        recipe_url = input("Please enter the URL of a recipe from allrecipes.com or enter [q] to quit.\n")
        # recipe_url = 'https://www.allrecipes.com/recipe/213268/classic-goulash/'
        # recipe_url = 'https://www.allrecipes.com/recipe/273326/parmesan-crusted-shrimp-scampi-with-pasta/'
        # recipe_url = 'https://www.allrecipes.com/recipe/230117/gluten-free-thanksgiving-stuffing/'
        # recipe_url = 'https://www.allrecipes.com/recipe/88921/shrimp-wellington/'
        # recipe_url = 'https://www.allrecipes.com/recipe/268669/creamy-shrimp-scampi-with-half-and-half/'
        # recipe_url = 'https://www.allrecipes.com/recipe/257914/taro-boba-tea/'
        # recipe_url = 'https://www.allrecipes.com/recipe/193307/easy-mochi/'
        # recipe_url = 'https://www.allrecipes.com/recipe/266015/boba-coconut-milk-black-tea-with-tapioca-pearls/'
        recipe_url = 'https://www.allrecipes.com/recipe/222340/chef-johns-roast-christmas-goose/'
        # recipe_url = 'https://www.allrecipes.com/recipe/212892/alligator-animal-italian-bread/'
        # recipe_url = 'https://www.allrecipes.com/recipe/232908/chef-johns-meatless-meatballs/'
        # recipe_url = 'https://www.allrecipes.com/recipe/10477/chocolate-mint-cookies-i/'          # BUG: NEW STYLE
        # recipe_url = 'https://www.allrecipes.com/recipe/82439/pork-and-pepper-stir-fry/'          # BUG: NEW STYLE
        # recipe_url = 'https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/'               # BUG: NEW STYLE
        # recipe_url = 'https://www.allrecipes.com/recipe/16212/chocolate-mint-candies-cookies/'    # BUG: NEW STYLE

        if recipe_url == 'q':
            return
        if 'allrecipes.com/recipe' not in recipe_url:
            continue

        name, o_ingredients, o_directions = fetch_recipe(recipe_url)
        ingredients = o_ingredients
        directions = o_directions
        fresh = True

        openers = ['Wow!', 'Oh,', 'Huh,', 'Mmm,']
        closers = ['Sounds tasty!', 'Smells delicious.', 'Looks great!']
        options = ['Exit', 'Enter a new recipe', 'Make it vegetarian', 'Make it nonvegetarian',
                    'Make it healthier', 'Make it unhealthier', 'Make it Japanese', 'Make it Pan Asian',
                    'Double it', 'Half it']
        
        print(f'\n{random.choice(openers)} {name}? {random.choice(closers)}\n')

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
                ingredients, directions = eval(options[n].lower().replace(' ', '_')+'(ingredients, directions)')
                pass

'''
NOTES

For Parsing into steps, maybe slice the og stuff out, transform separately, then splice it back in

MAYBE JUST MAYBE
Pull a bunch of recipes from allrecipes with the same genre as the desired transformation
Then scrape the stuff from it

--------------------------------------------------------------------------------------------

*** To Vegetarian:
Hardcode a list of common meats (chicken, beef, turkey?)
Eliminate from recipe (easy)
Substitute (tofu, vegetarian bacon, tofurkey) if possible

Keep a search string, append dish name to it
find similar dishes without meat
Bit redundant

--------------------------------------------------------------------------------------------

*** From Vegetarian:
Hardcode a list of common Substitute (tofu, vegetarian bacon, tofurkey) if possible
Eliminate from recipe (easy)
Substitute common meats (chicken, beef, turkey?)

Recommend a meat?
Maybe search all recipes for a similar recipe and find the meat with the most occurences

--------------------------------------------------------------------------------------------

*** To Healthy:
Do the same stuff, keep a map of unhealthy stuff to healthy stuff

--------------------------------------------------------------------------------------------

*** From Healthy:
Add a bunch of butter

--------------------------------------------------------------------------------------------

*** Scaling (double and cut in half):
Just multiply/divide the quantities

--------------------------------------------------------------------------------------------

*** To/From Japanese:
mochi stuff

--------------------------------------------------------------------------------------------

*** To/From {OTHER CUISINE}

--------------------------------------------------------------------------------------------

?? *** List Calorie Count Assoc. With Meal

--------------------------------------------------------------------------------------------

?? *** To/From Vegan

'''

if __name__ == "__main__":
    main()
