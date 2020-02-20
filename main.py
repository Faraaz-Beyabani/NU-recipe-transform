import re
import random
import requests
import nltk

from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize


def fetch_recipe(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser').body

    name = soup.find('h1', id='recipe-main-content').text
    recipe = (soup.find('section', class_='ar_recipe_index'))

    ingredients = fetch_ingredients(recipe)
    directions = fetch_directions(recipe)

    return name, ingredients, directions

def fetch_ingredients(recipe):
    nltk.download('punkt')
    ing_lists = recipe.find_all('ul', id=re.compile(r'lst_ingredients.*'))
    ingredients = []
    for sub_list in ing_lists:
        ingredients += [i for i in [parse_ingredient(i) for i in sub_list] if i]
    temp_ing = [nltk.pos_tag(word_tokenize(i)) for i in ingredients]

    measurements = set()
    ing_stats = []
    for i, split_ing in enumerate(temp_ing):
        ing_dict = {'quantity':0, 'measure':'', 'item':'', 'prep':[], 'descriptor':[]}
        item = []
        measure = False
        for j, part in enumerate(split_ing):
            if j == 0:
                ing_dict['quantity'] = str(eval(part[0]))
            elif part[1] == 'CD' and not any(part[0] in v for v in ing_dict.values()):
                ing_dict['quantity'] = str(float(ing_dict['quantity']) + eval(part[0]))

            elif split_ing[j-1][1] == 'CD' and part[0] == '(':
                m = re.search(r'\(.*\) [a-zA-Z]*', ingredients[i]).group()
                if not ing_dict['measure']:
                    ing_dict['measure'] = m
                    measurements.add(m)
            elif (split_ing[j-1][1] == 'CD' 
                and ((part[1] == 'NNS' and float(ing_dict['quantity']) > 1) 
                    or (part[1] == 'NN' and float(ing_dict['quantity']) <= 1))
                    or (part[1] == 'JJ' and part[0] in measurements and not ing_dict['measure'])):
                if not ing_dict['measure']:
                    ing_dict['measure'] = part[0]
                    measurements.add(part[0])
            # elif part[1] != 'JJ' and not ing_dict['measure']:
            #     if part[1] == 'NNS' and float(ing_dict['quantity']) > 1:
            #         ing_dict['measure'] = part[0]
            #         measurements.add(part[0])
            #     elif part[1] == 'NN':
            #         ing_dict['measure'] = part[0]
            #         measurements.add(part[0])
            elif part[0] == ',':
                sub = split_ing[j+1:]
                for k, sub_part in enumerate(sub):
                    if sub_part[1] in ['VBD', 'VBN']:
                        if sub[k-1][1] == 'RB':
                            ing_dict['prep'] += [sub[k-1][0] + ' ' + sub_part[0]]
                        else:
                            ing_dict['prep'] += [sub_part[0]]
                break

        #     elif part[1] in ['VBD', 'VBN']:
        #         desc = part[0]
        #         pre = split_ing[j-1]
        #         if pre[1] == 'RB':
        #             desc = pre[0] + ' ' + desc
        #         ing_dict['descriptor'] += [desc]
            else:
                if not any(part[0] in v for v in ing_dict.values()) and len(part[0]) > 1:
                    item += [part[0]]
        if not ing_dict['measure']:
            ing_dict['measure']
        if item:
            ing_dict['item'] = ' '.join(item)
        else:
            ing_dict['item'] = ing_dict['measure']


        ing_stats.append(ing_dict)

    for i in range(len(temp_ing)):
        print(temp_ing[i])
        print(ing_stats[i])
        print('\n')
    return ing_stats

def parse_ingredient(ingredient):
    label = ingredient.find('label')
    if label != -1:
        return label.attrs.get('title')

    return None

def fetch_directions(recipe):
    dir_list = recipe.find('ol', class_='recipe-directions__list').find_all('li')
    return [d.span.text.strip() for d in dir_list]

def main():
    while True:
        recipe_url = input("Please enter the URL of a recipe from allrecipes.com or enter [q] to quit.\n")
        # https://www.allrecipes.com/recipe/213268/classic-goulash/
        # https://www.allrecipes.com/recipe/16212/chocolate-mint-candies-cookies/
        # https://www.allrecipes.com/recipe/273326/parmesan-crusted-shrimp-scampi-with-pasta/
        # https://www.allrecipes.com/recipe/268669/creamy-shrimp-scampi-with-half-and-half/
        # https://www.allrecipes.com/recipe/10477/chocolate-mint-cookies-i/


        
        if recipe_url == 'q':
            return
        if 'allrecipes.com/recipe' not in recipe_url:
            continue

        name, ingredients, directions = fetch_recipe(recipe_url)
        fresh = True

        openers = ['Wow!', 'Oh,', 'Huh,']
        closers = ['Sounds tasty!', 'Smells delicious.', 'Looks great!']
        options = ['Exit', 'Enter a new recipe', 'Make it vegetarian', 'Make it non-vegetarian', 
                    'Make it healthier', 'Make it unhealthier', 'Make it CUISINE TYPE', 'Make it CUISINE TYPE', 
                    'Double it', 'Halve the amount']
        
        print(f'\n{random.choice(openers)} {name}? {random.choice(closers)}\n')

        return

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
                # TODO actually do stuff
                pass

if __name__ == "__main__":
    main()
