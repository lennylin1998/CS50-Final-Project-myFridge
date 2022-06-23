import os
import datetime
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from urllib import parse
import sqlite3
from flask import g
from tools import login_required
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure sqlite database
database = os.path.abspath(os.getcwd()) + '/myfridge.db'
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(database)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@login_required
@app.route('/grocery', methods=["GET", 'POST'])
def grocery():
    if request.method == 'POST':
        db = get_db()
        cart = []
        for key in request.form.keys():
            if key[3:] not in cart:
                cart.append(key[3:])
        item_list_query = db.execute('SELECT item FROM items').fetchall()
        item_list = [row['item'] for row in item_list_query]
        for n in cart:
            name = request.form[f'itm{n}']
            purchase_date = request.form[f'pcd{n}']
            best_before = request.form[f'bsb{n}']
            unit =  request.form[f'uni{n}']
            category = request.form[f'cat{n}']
            quantity = request.form[f"qty{n}"]
            if name not in item_list:
                db.execute('INSERT INTO items (item, unit, category) VALUES (?, ?, ?)', [name, unit, category])
                db.commit()
            # Match exact item name to query item's id
            item_id = db.execute('SELECT id FROM items WHERE item = ?', [name]).fetchone()[0]
            db.execute('INSERT INTO purchase (item_id, purchase_date, best_before) VALUES (?, ?, ?)', [item_id, purchase_date, best_before])
            db.commit()
            purchase_id = db.execute('SELECT id FROM purchase ORDER BY timestamp DESC, id DESC LIMIT 1').fetchone()[0]
            db.execute('INSERT INTO item_quantity (purchase_id, quantity) VALUES (?, ?)', (int(purchase_id), quantity))
        db.commit()
    return render_template('grocery.html')

@login_required
@app.route('/', methods=["GET", "POST"])
def fridge():
    db = get_db()
    if request.method == 'POST':
        item_keys = [key for key in request.form.keys() if key[:3] == 'qtn']
        if "Don't" not in request.form['submit-btn']:
            # Create a recipe
            recipe_name = request.form['recipe-name']
            db.execute('INSERT INTO recipes (name, count) VALUES (?, 1)', [recipe_name])
            db.commit()
            recipe_id = db.execute('SELECT id FROM recipes WHERE name = ? ORDER BY timestamp DESC, id DESC LIMIT 1', [recipe_name]).fetchone()[0]
            # Save the ingredients data
            for key in item_keys:
                db.execute('INSERT INTO ingredients (item_id, quantity, recipe_id) VALUES (?, ?, ?)', (key[4:], request.form[key], recipe_id))
        # Update item_quantity in fridge
        for key in item_keys:
            db.execute('INSERT INTO item_quantity (purchase_id, quantity) VALUES (?, ?)', (key[4:], -int(request.form[key])))
        db.commit()
    items = db.execute('SELECT p.id, item, category, unit, purchase_date, CAST (JULIANDAY(best_before) - JULIANDAY(DATE("now")) AS INT) AS days_diff, SUM(quantity) AS quantity\
                        FROM items i\
                        JOIN purchase p ON i.id = p.item_id\
                        JOIN item_quantity q ON p.id = q.purchase_id\
                        GROUP BY p.id\
                        HAVING days_diff >= 0 AND SUM(quantity) > 0').fetchall()
    recipe_count = db.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]
    return render_template('fridge.html', items=items, recipe_count=recipe_count)

@login_required
@app.route('/history', methods=["GET", "POST"])
def history():
    db = get_db()
    cook = db.execute('SELECT item, category, quantity, unit FROM item_quantity iq JOIN purchase p ON iq.purchase_id = p.id JOIN items i ON p.item_id = i.id WHERE quantity < 0').fetchall()
    recipes = db.execute('SELECT name, group_concat(item) AS ingredients, DATE(timestamp) AS date FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id JOIN items i ON ing.item_id = i.id').fetchall()
    purchase = db.execute('SELECT item, category, quantity, unit, purchase_date FROM purchase p JOIN items i ON p.item_id = i.id JOIN item_quantity iq ON iq.purchase_id = p.id WHERE quantity > 0').fetchall()
    overdue = db.execute('SELECT item, category, quantity, unit, best_before FROM items i JOIN (SELECT item_id, SUM(quantity) AS quantity, best_before FROM purchase p JOIN item_quantity iq ON iq.purchase_id = p.id GROUP BY p.id) AS m ON m.item_id = i.id WHERE best_before < DATE("now") AND quantity > 0').fetchall()
    return render_template('history.html', cook=cook, recipes=recipes, purchase=purchase, overdue=overdue)

@login_required
@app.route('/recipe', methods=["GET", "POST"])
def recipe():
    db = get_db()
    if request.method == "POST":
        recipe_id = request.form['recipe-id']
        if recipe_id:
            recipe_to_cook = db.execute('SELECT i.item_id, i.quantity FROM recipes r JOIN ingredients i ON r.id = i.recipe_id WHERE r.id = ?', (recipe_id)).fetchall()
            for row in recipe_to_cook:
                total = row['quantity']
                all_item = db.execute('SELECT p.id, quantity, CAST (JULIANDAY(best_before) - JULIANDAY(DATE("now")) AS INT) AS days_diff FROM purchase p JOIN items i ON p.item_id = i.id WHERE i.id = ? ORDER BY days_diff ASC', [row['item_id']]).fetchall()
                i = 0
                while total > 0:
                    if total > all_item[i]['quantity']:
                        db.execute('INSERT INTO item_quantity (purchase_id, quantity) VALUES (?, ?)', [all_item[i]['id'], -all_item[i]['quantity']])
                        total -= all_item[i]['quantity']
                    else:
                        db.execute('INSERT INTO item_quantity (purchase, quantity) VALUES (?, ?)', [all_item[i]['id'], -total])
                        total = 0
                    i += 1
    recipes = db.execute('SELECT r.id, name, count, group_concat(item) AS ingredients FROM recipes r JOIN ingredients ing ON r.id = ing.recipe_id JOIN items it ON ing.item_id = it.id GROUP BY r.id, name, count').fetchall()
    return render_template('recipe.html', recipes=recipes)

@login_required
@app.route('/recipe/create', methods=["GET", "POST"])
def create_recipe():
    db = get_db()
    if request.method == "POST":
        # Insert new recipe data
        recipe_name = request.form['recipe-name']
        db.execute('INSERT INTO recipes (name, count) VALUES (?, 0)', [recipe_name])
        db.commit()
        recipe_id = db.execute('SELECT id FROM recipes WHERE name = ? ORDER BY timestamp DESC, id DESC LIMIT 1', [recipe_name]).fetchone()[0]
        # Insert ingredients data
        for key in request.form.keys():
            if key[:3] == 'org':
                db.execute('INSERT INTO ingredients (item_id, quantity, recipe_id) VALUES (?, ?, ?)', [key[4:], request.form[key], recipe_id])
        new_recipe = []
        for key in request.form.keys():
            if key != 'recipe-name' and key[:3] != 'org':
                if key[3:] not in new_recipe:
                    new_recipe.append(key[3:])
        # Check if the input item is in the database
        item_list_query = db.execute('SELECT item FROM items').fetchall()
        item_list = [row['item'] for row in item_list_query]
        for n in new_recipe:
            name = request.form[f'itm{n}']
            unit =  request.form[f'uni{n}']
            category = request.form[f'cat{n}']
            quantity = request.form[f"qty{n}"]
            if name != '' and quantity != '':
                if name not in item_list:
                    db.execute('INSERT INTO items (item, unit, category) VALUES (?, ?, ?)', [name, unit, category])
                    db.commit()
                # Match exact item name to query item's id
                item_id = db.execute('SELECT id FROM items WHERE item = ?', [name]).fetchone()[0]
                db.execute('INSERT INTO ingredients (recipe_id, item_id, quantity) VALUES (?, ?, ?)', [recipe_id, item_id, int(quantity)])
        db.commit()
        return redirect('/recipe')
    id_list = parse.parse_qs(parse.urlparse(request.url).query)['id']
    items = []
    for id in id_list:
        item = db.execute('SELECT i.id, item, category, unit FROM purchase p JOIN items i ON p.item_id = i.id WHERE p.id = ?', [id]).fetchall()[0]
        items.append(item)
    recipe_count = db.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]
    return render_template('create_recipe.html', recipe_count=recipe_count, items=items)


@login_required
@app.route('/recipe/edit', methods=["GET", "POST"])
def edit_recipe():
    db = get_db()
    if request.method == 'POST':
        recipe_name = request.form['recipe-name']
        recipe_id = request.form['recipe-id']
        if recipe_name:
            db.execute('UPDATE recipes SET name = ? WHERE id = ?', [recipe_name, recipe_id])
        original = [key for key in request.form.keys() if key[:3] == 'org']
        for key in original:
            db.execute('UPDATE ingredients SET quantity = ? WHERE recipe_id = ? AND item_id = ?', [request.form[key], recipe_id, key[4:]])
        # Insert ingredients data
        new = []
        for key in request.form.keys():
            if key != 'recipe-name' and key != 'recipe-id' and key[:3] != 'org':
                if key[3:] not in new:
                    new.append(key[3:])
        # Check if the input item is in the database
        item_list_query = db.execute('SELECT item FROM items').fetchall()
        item_list = [row['item'] for row in item_list_query]
        for n in new:
            name = request.form[f'itm{n}']
            unit =  request.form[f'uni{n}']
            category = request.form[f'cat{n}']
            quantity = request.form[f"qty{n}"]
            if name != '' and quantity != '':
                if name not in item_list:
                    print('\n\n\n' + name)
                    db.execute('INSERT INTO items (item, unit, category) VALUES (?, ?, ?)', [name, unit, category])
                    db.commit()
                # Match exact item name to query item's id
                item_id = db.execute('SELECT id FROM items WHERE item = ?', [name]).fetchone()[0]
                db.execute('INSERT INTO ingredients (recipe_id, item_id, quantity) VALUES (?, ?, ?)', [recipe_id, item_id, int(quantity)])
        db.commit()
        return redirect('/recipe')
    recipe_id = request.args['id']
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', [recipe_id]).fetchall()[0]
    ingredients = db.execute('SELECT it.id, item, category, quantity, unit FROM ingredients ing JOIN items it ON ing.item_id = it.id WHERE recipe_id = ?', [recipe_id]).fetchall()
    return render_template('edit_recipe.html', recipe=recipe, ingredients=ingredients)


@login_required
@app.route('/ingredients', methods=["GET"])
def ingredients():
    recipe_id = request.args["id"]
    db = get_db()
    fridge_query = db.execute('SELECT i.id, CAST (JULIANDAY(best_before) - JULIANDAY(DATE("now")) AS INT) AS days_diff, SUM(quantity) AS quantity\
                    FROM items i\
                    JOIN purchase p ON p.item_id = i.id\
                    JOIN item_quantity q ON p.id = q.purchase_id\
                    GROUP BY i.id\
                    HAVING days_diff >= 0 AND SUM(quantity) > 0').fetchall()
    query = db.execute('SELECT it.id AS id, item, ing.quantity AS quantity, category, unit FROM ingredients ing JOIN items it ON it.id = ing.item_id WHERE recipe_id = ?', [recipe_id]).fetchall()
    ingredients = []
    for row in query:
        ingredient = {"item": row['item'], "category": row['category'], "quantity": row['quantity'], "unit": row['unit']}
        if row['id'] in [item['id'] for item in fridge_query]:
            for item in fridge_query:
                if row['id'] == item['id']:
                    if item['quantity'] >= row['quantity']:
                        ingredient['cookable'] = 'cookable'
                    else:
                        ingredient['cookable'] = 'shortage'
        else:
            ingredient['cookable'] = 'shortage'
        ingredients.append(ingredient)
    return jsonify(ingredients)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        query_users = db.execute('SELECT username FROM users').fetchall()
        users = [user['username'] for user in query_users]
        if username in users:
            query_user = db.execute('SELECT * FROM users WHERE username = ?', [username]).fetchone()
            if check_password_hash(query_user['hash'], password):
                session['user_id'] = query_user['id']
                return redirect('/')
    return render_template('login.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        db = get_db()
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirm']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not confirmation:
            error = 'Enter password again for confirmation.'
        elif password != confirmation:
            error = 'Password does not match.'

        if error is None:
            try:
                db.execute('INSERT INTO users (username, hash) VALUES (?, ?)', (username, generate_password_hash(password)))
                db.commit()
                return render_template('login.html')
            except db.IntegrityError:
                error = 'Username already exists.'
        flash(error)
    return render_template('register.html')


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('user_id', None)
    return redirect('/login')

@app.context_processor
def utility_processor():
    return dict(abs=abs)