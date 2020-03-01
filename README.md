# AllRecipes Parser

Group Members: Faraaz Beyabani, Varun Ganglani, Raymond Liu, Brandon Lieuw

On Windows, run `win_setup.ps1` with Powershell to set up the proper virtual environment.
The script will install virtualenv, create a virtual environment, and download all of the necessary packages from the requirements.txt file.

If not on Windows, please create and activate a virtual environment (typically through virtualenv or conda), then install all necessary prerequisites like so: 

`pip install -r requirements.txt`

/////////////////////////////////////

Options: Make it vegetarian, make it non-vegetarian, make it healthier, make it unhealthier, make it Japanese style, make it Indian style, Dduble the servings, halve the servings.

Make it vegetarian replaces meats with certain meat substitutes, such as tofu and related products, or the Impossible Ground Beef Burger (TM).

Make it non-vegetarian replaces meat substitutes with meats, unless it can't find any, at which point it adds bacon bits to the recipe.

Make it healthier and unhealthier reduce and increase (respectively) the amount of sugar, cream, powder, paste, oil, and other typically 'fatty' or unhealthy ingredients.

Make it Japanese substitutes certain fruits, seasonings, and sauces with their Japanese variants (yuzu, mikan, rice vinegar, etc.).

Make it Indian substitutes certain seasonings, sauces, and additives (nuts, beans) with those commonly used in Indian dishes.

Double and halve the servings attempt to scale the number of ingredients in the recipe to serve more people.

/////////////////////////////////////

Repository: https://github.com/Faraaz-Beyabani/NU-recipe-transform
