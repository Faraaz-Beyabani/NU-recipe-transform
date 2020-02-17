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
#    for i in range(len(ingredients)):
#        temp_ing = ingredients[i].split(',')
#        temp_ing[0] = temp_ing[0].split()
#        quantity = temp_ing[0][0]
#        descriptor = []
#        if temp_ing[0][1][0] == "(" and temp_ing[0][2][-1] == ")":
#            measurement = temp_ing[0][3]
#            paren = " ".join([temp_ing[0][1][1:], temp_ing[0][2][:-1]])
#            temp_ing[0] = temp_ing[0][:2] + temp_ing[0][3:]
#            temp_ing[0][1] = paren
#            descriptor += [paren]
            
        
    print(temp_ing)
        
    return ingredients

def parse_ingredient(ingredient):
    if (label := ingredient.find('label')) != -1:
        return label.attrs.get('title')

    return None

def fetch_directions(recipe):
    dir_list = recipe.find('ol', class_='recipe-directions__list').find_all('li')
    return [d.span.text.strip() for d in dir_list]

def main():
    while True:
        recipe_url = input("Please enter the URL of a recipe from allrecipes.com or enter [q] to exit.\n")
        # recipe_url = "https://www.allrecipes.com/recipe/213268/classic-goulash/?internalSource=popular&referringContentType=Homepage"
        
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
