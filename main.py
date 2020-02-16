import re
import random
import requests

from bs4 import BeautifulSoup


def fetch_recipe(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser').body

    name = soup.find('h1', id='recipe-main-content').text
    recipe = (soup.find('section', class_='ar_recipe_index'))

    ingredients = fetch_ingredients(recipe)
    directions = fetch_directions(recipe)

    return name, ingredients, directions

def fetch_ingredients(recipe):
    ing_lists = recipe.find_all('ul', id=re.compile(r'lst_ingredients.*'))
    ingredients = []
    for sub_list in ing_lists:
        ingredients += [i for i in [parse_ingredient(i) for i in sub_list] if i]

    return ingredients

def parse_ingredient(ingredient):
    if (label := ingredient.find('label')) != -1:
        return label.attrs.get('title')

    return None

def fetch_directions(recipe):
    dir_list = recipe.find('ol', class_='recipe-directions__list').find_all('li')
    return [d.span.text.strip() for d in dir_list]


if __name__ == "__main__":
    # recipe_url = input("Please enter the URL of a recipe from allrecipes.com.")
    recipe_url = "https://www.allrecipes.com/recipe/213268/classic-goulash/?internalSource=popular&referringContentType=Homepage"
    name, ingredients, directions = fetch_recipe(recipe_url)
    fresh = True

    openers = ['Wow!', 'Oh,', 'Huh,']
    closers = ['Sounds tasty!', 'Smells delicious.', 'Looks great!']
    options = ['Exit', 'Make it vegetarian', 'Make it non-vegetarian', 'Make it healthier', 
                'Make it unhealthier', 'Make it CUISINE TYPE', 'Make it CUISINE TYPE', 'Double it', 
                'Halve the amount']
    
    print(f'\n{random.choice(openers)} {name}? {random.choice(closers)}\n')

    while True:
        for i,o in enumerate(options):
            print(f'[{i}] {o}')

        n = int(input('What do you want to do with it?\n'))

        if n == 0 or n >= len(options):
            break
