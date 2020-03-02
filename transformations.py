import re

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
        except Exception:
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
        except Exception:
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

    simple = False
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
            simple = True
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

        replacement[temp] = ing['item'].replace('impossible ', '')
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
            elif any(b in sentence[i] for b in birds):
                sentence[i] = 'tofurky'
            elif any(f in sentence[i] for f in fish):
                sentence[i] = 'tofu'
            elif any(e in sentence[i] for e in etc_fish):
                sentence[i] = 'king oyster mushrooms'
            elif any(t in sentence[i] for t in tempeh):
                sentence[i] = 'tempeh'
            elif any(s in sentence[i] for s in misc_sea):
                sentence[i] = 'lobster mushrooms'
            elif any(m in sentence[i] for m in meats) and not simple:
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
        ing_dict = {'string':['{item}'], 'quantity':'', 'measure':'', 'item': 'bacon bits to taste', 'prep':'', 'descriptor':''}
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

def steps_replacer(steps, old, new):
    split_old = old.split()
    new_last = new.split()[-1]
    if len(split_old) >= 2:
        for i in range(len(split_old) - 1):
            ing = split_old[i] + ' ' + split_old[i+1]
            for step in steps:
                step['string'] = (step['string'].replace(ing, new)
                                                .replace(new_last+' '+new_last, new_last))
                step['string'] = re.sub(r'\b(\w+)( \1\b)+', r'\1', step['string'])

    return steps

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

        if not any('kinako' in i['item'] for i in t_ingredients):
            ing_dict = {'string':['{item}', '{desc}'], 'quantity':'', 'measure':'', 'item': 'kinako to taste', 'prep':'', 'descriptor':'(optional)'}
            dir_dict =  {'string':'{method} kinako until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['kinako'], 'times':[]}
            t_ingredients.append(ing_dict)
            t_directions.append(dir_dict)
    else: # savory 
        if any('meat' in d['string'] for d in t_directions) or any('beef' in d['string'] for d in t_directions):
            if not any('teriyaki' in i['item'] for i in t_ingredients):
                t_ingredients.append({'string':['{quantity}', '{measure}', '{item}', '{desc}'], 'quantity':'1', 'measure':'cup', 'item':'teriyaki sauce', 'prep':'', 'descriptor':'or to taste'})
                t_directions.insert(0, {'string':'{method} the meat for {time} minutes in teriyaki sauce.', 'tools':[], 'methods':['marinate'], 'ingredients':['meat'], 'times':['20']})

        for i in t_ingredients:
            original = i['item']
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

            if original != i['item']:
                t_directions = steps_replacer(t_directions, original, i['item'])

        if not any('furikake' in i['item'] for i in t_ingredients):
            ing_dict = {'string':['furikake to taste (optional)'], 'quantity':'', 'measure':'', 'item': 'furikake to taste', 'prep':'', 'descriptor':'(optional)'}
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
            if 'pecans' in i['item']:
                i['item'] = 'crushed pistachios'
                for d in t_directions:
                    d['string'].replace('pecans', 'crushed pistachios')

        if not any('pistachios' in i['item'] for i in t_ingredients):
            ing_dict = {'string':['{item}', '{desc}'], 'quantity':'', 'measure':'', 'item': 'crushed pistachios to taste', 'prep':'', 'descriptor':'(optional)'}
            dir_dict =  {'string':'{method} crushed pistachios until satisfied.', 'tools':[], 'methods':['sprinkle'], 'ingredients':['pistachios'], 'times':[]}
            t_ingredients.append(ing_dict)
            t_directions.append(dir_dict)
    else: # savory 
        if any('meat' in d['string'] for d in t_directions) or any('beef' in d['string'] for d in t_directions):
            if not any('masala' in i['item'] for i in t_ingredients):
                t_ingredients.append({'string':['{quantity}', '{measure}', '{item}', '{desc}'], 'quantity':'1', 'measure':'cup', 'item':'masala sauce', 'prep':'', 'descriptor':'or to taste'})
                t_directions.insert(0, {'string':'{method} the meat for {time} minutes in the masala sauce.', 'tools':[], 'methods':['marinate'], 'ingredients':['meat'], 'times':['20']})

        for i in t_ingredients:
            original = i['item']
            if 'yogurt' in i['item']:
                i['item'] = 'dahi yogurt'
            if 'pepper' in i['item'] and not 'black' in i['item']:
                i['item'] = 'mirchi chile pepper'
                if i['quantity'] and float(i['quantity']) > 1 and not i['measure']:
                    i['item'] += 's'
            if 'dressing' in i['item']:
                i['item'] = 'masala dressing'
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
                for d in t_directions:
                    d['string'].replace('pecans', 'crushed pistachios')
            if 'paprika' in i['item']:
                i['item'] = 'coriander seeds'
                for d in t_directions:
                    d['string'].replace('paprika', 'coriander seeds')

            if original != i['item']:
                t_directions = steps_replacer(t_directions, original, i['item'])

        if not any('curry' in i['item'] for i in t_ingredients):
            ing_dict = {'string':['{item}', '{desc}'], 'quantity':'', 'measure':'', 'item': 'curry powder to taste', 'prep':'', 'descriptor':'(optional)'}
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
        if any(u in ing['item'] for u in unhealthies) and ing['quantity']:
            ing['quantity'] = str(float(ing['quantity']) * 0.5)

    return t_ingredients, t_directions

def make_it_unhealthy(ingredients, directions):
    t_ingredients = ingredients
    t_directions = directions

    unhealthies = ['oil', 'salt', 'sugar', 'sauce', 'ketchup', 'mayo', 'butter', 'mustard', 'honey', 'chocolate', 'cream', 'fudge', 'marshmallow', 'caramel',
                    'yogurt', 'shortening', 'syrup', 'milk', 'cheese', 'seasoning', 'powder', 'molasses', 'beer', 'wine', 'gravy', 'dressing']

    for ing in t_ingredients:
        if any(u in ing['item'] for u in unhealthies) and ing['quantity']:
            ing['quantity'] = str(float(ing['quantity']) * 2)

    return t_ingredients, t_directions