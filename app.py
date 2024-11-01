from flask import Flask, render_template,request,session,redirect,flash,url_for
from config import Database
#for filter the data
import re
app = Flask(__name__)

app.secret_key = 'your_secret_key'
# Initialize Database
db = Database()

#Guest Block

@app.route("/")
def home():
    card_product_list = db.fetchall(f"""
            SELECT cpl.card_product_list_id, cpl.card_type_id, cpl.product_id, cpl.month, cpl.unit_price, cpl.max_unit, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            JOIN card_type c ON cpl.card_type_id = c.id
            JOIN product p ON cpl.product_id = p.product_id
        """)   
    print(f"this is the data:{card_product_list}")
    return render_template("guest/index.html", card_product_list = card_product_list)

@app.route("/index")
def index():
    card_product_list = db.fetchall(f"""
            SELECT cpl.card_product_list_id, cpl.card_type_id, cpl.product_id, cpl.month, cpl.unit_price, cpl.max_unit, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            JOIN card_type c ON cpl.card_type_id = c.id
            JOIN product p ON cpl.product_id = p.product_id
        """)   
    print(f"this is the data:{card_product_list}")

    return render_template("guest/index.html", card_product_list = card_product_list)

@app.route("/about")
def about():
    return render_template("guest/about.html")

@app.route("/search")
def search():
    return render_template("guest/search.html")

@app.route("/product_info")
def productinfo():
    card_product_list = db.fetchall("""
            SELECT cpl.card_product_list_id, cpl.card_type_id, cpl.product_id, cpl.month, cpl.unit_price, cpl.max_unit, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            JOIN card_type c ON cpl.card_type_id = c.id
            JOIN product p ON cpl.product_id = p.product_id
        """)
    return render_template("guest/product_info.html", card_product_list= card_product_list)

@app.route("/purchase_list")
def purchaselist():
    try:
        
        adhar_no = request.args.get('adhar_no')

        card_details = db.fetchone(f"""
                SELECT * 
                FROM card_details
                WHERE adhar_no = '{adhar_no}'     
            """)
        purchase_list = None
        if card_details:
            print(f"card details:{card_details}")
            card_details_id = card_details['card_details_id']
            print(f"card details:{card_details_id}")

            purchase_list_query = f"""
                            SELECT pl.purchase_details_id, pl.unit, pl.month, pl.amount, p.product_name, c.card_type_id, ct.card_type
                            FROM purchase_details AS pl
                            LEFT JOIN product AS p ON pl.product_id = p.product_id
                            LEFT JOIN card_details AS c ON pl.card_details_id = c.card_details_id
                            LEFT JOIN card_type AS ct ON c.card_type_id = ct.id
                            WHERE pl.card_details_id ={card_details_id}
                        """
            purchase_list = db.fetchall(purchase_list_query)
            print(f"purchase list:{purchase_list}")
    except Exception as e:
                flash(f"Failed to update category: {str(e)}", "danger")
                print(f"this is the error{e}")
    
    return render_template("guest/purchase_list.html",  purchase_details= purchase_list)

@app.route("/contact")
def contact():
    return render_template("guest/contact.html")

@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Fetch user from the database
        query = f"SELECT * FROM login WHERE username = '{username}' and password='{password}'"
        user = db.fetchone(query)

        if user:
            session['user_id'] = user['id']
            # Verify the password
            if user['type']=='admin':
                flash("Login successful!", "success")
                return redirect(url_for('adminhome'))  
            # elif user['type']=='user':
            #     flash("Login successful!", "success")
            #     return redirect(url_for('userhome'))
            else:
                flash("Invalid username or password.", "danger")
            
        else:
            flash("User not found.", "danger")

    return render_template("guest/login.html")


# @app.route("/register")
# def register():
#     return render_template("guest/register.html")


#admin Block

@app.route("/admin-home")
def adminhome():
    card_product_list = db.fetchall("""
            SELECT cpl.card_product_list_id, cpl.card_type_id, cpl.product_id, cpl.month, cpl.unit_price, cpl.max_unit, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            JOIN card_type c ON cpl.card_type_id = c.id
            JOIN product p ON cpl.product_id = p.product_id
        """)
    return render_template("admin/index.html", card_product_list=card_product_list)

@app.route("/admin-category", methods=["GET", "POST"])
def admincategory():
    if request.method == "POST":
        category_id = request.form.get('category_id')
        category_name = request.form['category']
        details = request.form['details']

        if category_id:  # Update operation
            try:
                update_category_query = f"""
                UPDATE category 
                SET name = '{category_name}', details = '{details}'
                WHERE id = {category_id}
                """
                db.execute(update_category_query)
                flash("Category updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update category: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_category_query = f"""
                INSERT INTO category (name, details) 
                VALUES ('{category_name}', '{details}')
                """
                db.single_insert(insert_category_query)
                flash("Category added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add category: {str(e)}", "danger")
        
        return redirect(url_for('admincategory'))

    # Fetch all categories and the category to edit (if any)
    categories = db.fetchall("SELECT * FROM category")
    category_to_edit = None
    if 'edit' in request.args:
        category_id = request.args.get('edit')
        category_to_edit = db.fetchone(f"SELECT * FROM category WHERE id = {category_id}")
    
    return render_template("admin/category.html", categories=categories, category_to_edit=category_to_edit)

@app.route("/delete-category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    try:
        delete_query = f"DELETE FROM category WHERE id = {category_id}"
        db.execute(delete_query)
        flash("Category deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete category: {str(e)}", "danger")
    
    return redirect(url_for('admincategory'))

@app.route("/admin-cardtype", methods=["GET", "POST"])
def admincardtype():
    if request.method == "POST":
        cardtype_id = request.form.get('cardtype_id')
        cardtype_name = request.form['cardtype']

        if cardtype_id:  # Update operation
            try:
                update_cardtype_query = f"""
                UPDATE card_type 
                SET card_type = '{cardtype_name}'
                WHERE id = {cardtype_id}
                """
                print(update_cardtype_query)
                db.execute(update_cardtype_query)
                flash("cardtype updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update cardtype: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_cardtype_query = f"""
                INSERT INTO card_type (card_type) 
                VALUES ('{cardtype_name}')
                """
                db.single_insert(insert_cardtype_query)
                flash("cardtype added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add cardtype: {str(e)}", "danger")
        
        return redirect(url_for('admincardtype'))

    # Fetch all categories and the category to edit (if any)
    cardtypes = db.fetchall("SELECT * FROM card_type")
    cardtype_to_edit = None
    if 'edit' in request.args:
        cardtype_id = request.args.get('edit')
        cardtype_to_edit = db.fetchone(f"SELECT * FROM card_type WHERE id = {cardtype_id}")
    
    return render_template("admin/card-type.html", cardtypes=cardtypes, cardtype_to_edit=cardtype_to_edit)

@app.route("/delete_cardtype/<int:cardtype_id>", methods=["POST"])
def delete_cardtype(cardtype_id):
    try:
        delete_query = f"DELETE FROM card_type WHERE id = {cardtype_id}"
        db.execute(delete_query)
        flash("cardtype deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete cardtype: {str(e)}", "danger")
    
    return redirect(url_for('admincardtype'))

#admin manage products
@app.route("/admin-product", methods=["GET", "POST"])
def adminproduct():
    if request.method == "POST":
        product_id = request.form.get('product_id')
        product_name = request.form['product_name']
        category_id = request.form['category_id']
        unit = request.form['unit']
        print(f"this is category:{product_name}")
        print(f"this is unit:{unit}")
        print(f"this is category Id:{category_id}")
        if product_id:  # Update operation
            try:
                update_product_query = f"""
                UPDATE product 
                SET product_name = '{product_name}', 
                    category_id = {category_id}, 
                    unit = '{unit}'
                WHERE id = {product_id}
                """
                print(update_product_query)
                db.execute(update_product_query)
                flash("Product updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update product: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_product_query = f"""
                INSERT INTO product (product_name, category_id, unit) 
                VALUES ('{product_name}', {category_id}, '{unit}')
                """
                db.single_insert(insert_product_query)
                flash("Product added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
        
        return redirect(url_for('adminproduct'))

    # Fetch all products
    products = db.fetchall("""
        SELECT p.product_id, p.product_name, p.unit, c.name 
        FROM product p 
        JOIN category c ON p.category_id = c.id
    """)

    # Fetch all categories to display in the dropdown
    categories = db.fetchall("SELECT id,name FROM category")

    product_to_edit = None
    if 'edit' in request.args:
        product_id = request.args.get('edit')

        product_to_edit = db.fetchone(f"""
        SELECT p.*, c.name AS category_name 
        FROM product p 
        LEFT JOIN category c ON p.category_id = c.id 
        WHERE p.product_id = {product_id}
        """)

    print(f"product to edit:{product_to_edit}")
    print(f"product to edit:{products}")
    print(f"this is category: {categories}")
    return render_template("admin/product.html", products=products, categories=categories, product_to_edit=product_to_edit)

@app.route("/delete-product", methods=["POST"])
def delete_product():
    try:
        product_id= request.args.get('edit')
        print(f'this is product idv123:{product_id}')
        delete_product_query = f"DELETE FROM product WHERE product_id = {product_id}"
        db.execute(delete_product_query)
        flash("Product deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete product: {str(e)}", "danger")
        print(f"exeption:{e}")
    
    return redirect(url_for('adminproduct'))

@app.route("/admin-card", methods=["GET", "POST"])
def admincard():
    if request.method == "POST":
       
        card_details_id = request.form.get('card_details_id')
        adhar_no = request.form['adhar_no']
        card_type_id = request.form['card_type_id']

        if card_details_id:  # Update operation
            try:
                update_card_query = f"""
                UPDATE card_details 
                SET adhar_no = '{adhar_no}', 
                    card_type_id = {card_type_id}, 
                WHERE card_type_id = {card_details_id}
                """
                print(update_card_query)
                db.execute(update_card_query)
                flash("card updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update product: {str(e)}", "danger")
        else:  # Create operation
            try:

                print('hello1')
                insert_card_query = f"""
                INSERT INTO card_details (adhar_no, card_type_id) 
                VALUES ('{adhar_no}', {card_type_id})
                """
                db.single_insert(insert_card_query)
                flash("card added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
        
        return redirect(url_for('admincard'))

    # Fetch all cards
    cards = db.fetchall("""
        SELECT c.card_details_id, c.adhar_no, c.card_type_id, t.card_type 
        FROM card_details c 
        JOIN card_type t ON c.card_type_id = t.id
    """)

    # Fetch all card types to display in the dropdown
    card_types = db.fetchall("SELECT id, card_type FROM card_type")

    card_to_edit = None
    if 'edit' in request.args:
        card_details_id = request.args.get('edit')

        card_to_edit = db.fetchone(f"""
        SELECT c.*, t.card_type AS card_type 
        FROM card_details c 
        LEFT JOIN card_type t ON c.card_type_id = t.id 
        WHERE c.card_details_id = {card_details_id}
        """)

    print(f"cards to edit:{card_to_edit}")
    print(f"cards :{cards}")
    return render_template("admin/card_details.html", cards=cards, card_types=card_types, card_to_edit=card_to_edit)

@app.route("/delete-card", methods=["POST"])
def delete_card():
    try:
        card_details_id= request.args.get('card_details_id')
        print(f'this is card id:{card_details_id}')
        delete_card_query = f"DELETE FROM card_details WHERE card_details_id = {card_details_id}"
        db.execute(delete_card_query)
        flash("card deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete product: {str(e)}", "danger")
    
    return redirect(url_for('admincard'))



@app.route("/admin-stock", methods=["GET", "POST"])
def adminstock():
    if request.method == "POST":
       
        stock_id = request.form.get('stock_id')
        product_id = request.form['product_id']
        print(f'this is product id:{product_id}')
        # card_type_id = request.form['card_type_id']
        unit = request.form['unit']
        month = request.form['month']
        if stock_id:
            unit_to_edit = request.form['unit_to_edit']
            given_unit = int(re.sub(r'\D', '', unit))
            old_unit = int(re.sub(r'\D', '', unit_to_edit))
            print(f'Product Old Unit: {old_unit} product new unit:{given_unit}')
            product_unit =given_unit  - old_unit
            print(f"this is difference unit:{product_unit}")
            #unit in product table
            current_unit_query = f"""
                        SELECT unit FROM product WHERE product_id = '{product_id}'
                        """
            current_unit_result = db.fetchone(current_unit_query)

            if current_unit_result:
                current_unit_str = current_unit_result['unit']  
                #FILTER INTO INT 
                current_unit = int(re.sub(r'\D', '', current_unit_str))  
            else:
                        current_unit = 0 
            
            #new unit to add in product table
            print(f"current_unit:{current_unit}")
            new_unit = current_unit + product_unit
            print(f"new_unit:{new_unit}")

            update_product_query = f"""
                    UPDATE product
                    SET unit = '{new_unit}'
                    WHERE product_id = {product_id}
                    """
            db.execute(update_product_query)
        
            # Update operation
            print(f"THSI IS MONTH:{month}")
            try:
                update_stocks_query = f"""
                UPDATE stocks
                SET product_id = '{product_id}', 
                    unit = {unit},
                    month = '{month}'
                WHERE stock_id = {stock_id}
                """
               
                db.execute(update_stocks_query)
                flash("card updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update product: {str(e)}", "danger")
        else:  # Create operation
            try:
                print('hello123')
                current_unit_query = f"""
                    SELECT unit FROM product WHERE product_id = '{product_id}'
                    """
                current_unit_result = db.fetchone(current_unit_query)
                
                if current_unit_result:
                    current_unit_str = current_unit_result['unit']  
                    #FILTER INTO INT 
                    current_unit = int(re.sub(r'\D', '', current_unit_str))  
                else:
                    current_unit = 0 
                
                #new unit to add in product table
                new_unit = current_unit + int(re.sub(r'\D', '', unit))
                print(f"new_unit:{new_unit}")

                update_product_query = f"""
                UPDATE product
                SET unit = '{new_unit}'
                WHERE product_id = {product_id}
                """
                db.execute(update_product_query)
                

                print('hello1')
                insert_stocks_query = f"""
                INSERT INTO stocks (product_id, unit, month) 
                VALUES ('{product_id}', '{unit}', '{month}')
                """
                db.single_insert(insert_stocks_query)
                flash("stocks added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
        
        return redirect(url_for('adminstock'))

    # Fetch all cards
    stocks = db.fetchall("""
        SELECT s.stock_id, s.month, s.unit, s.product_id, p.product_name AS product_name
        FROM stocks s 
        JOIN product p ON s.product_id = p.product_id
    """)

    # Fetch all card types to display in the dropdown
    products = db.fetchall("SELECT product_id, product_name FROM product")

    stocks_to_edit = None
    if 'edit' in request.args:
        stock_id = request.args.get('edit')
        
        stocks_to_edit = db.fetchone(f"""
        SELECT s.*, p.product_name AS product_name 
        FROM stocks s 
        LEFT JOIN product p ON s.product_id = p.product_id
        WHERE s.stock_id = {stock_id}
        """)

    print(f"cards to edit:{stocks_to_edit}")
    print(f"cards :{stocks}")
    return render_template("admin/stocks.html", stocks=stocks, products=products, stocks_to_edit=stocks_to_edit)

@app.route("/delete-stock", methods=["POST"])
def delete_stock():
    try:
        stock_id= request.args.get('stock_id')
        print(f'this is card id:{stock_id}')
        delete_stock_query = f"DELETE FROM stocks WHERE stock_id = {stock_id}"
        db.execute(delete_stock_query)
        flash("stocks deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete stock: {str(e)}", "danger")
    
    return redirect(url_for('adminstock'))

@app.route("/admin-product-list", methods=["GET", "POST"])
def adminproductlist():
    if request.method == "POST":
       
        card_product_list_id = request.form.get('card_product_list_id')
        product_id = request.form['product_id']
        print(f'this is product id:{product_id}')
        # card_type_id = request.form['card_type_id']
        month = request.form['month']
        card_type_id = request.form['card_type_id']
        unit_price = request.form['unit_price']
        max_unit = request.form['max_unit']
        if card_product_list_id:
            print(f'card product id:{card_product_list_id}')       
            try:
                update_card_product_list_query = f"""
                UPDATE card_product_list
                SET card_type_id = {card_type_id},
                    product_id = {product_id},
                    month = '{month}',
                    unit_price = '{unit_price}',
                    max_unit = '{max_unit}'
                WHERE card_product_list_id = {card_product_list_id}
                """
               
                db.execute(update_card_product_list_query)
                flash("product_list updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update product: {str(e)}", "danger")
        else:  # Create operation
            try:
               
                print('hello1')
                insert_card_product_list_query = f"""
                INSERT INTO card_product_list (card_type_id, product_id, month, unit_price, max_unit) 
                VALUES ('{card_type_id}', '{product_id}', '{month}', '{unit_price}', '{max_unit}')
                """
                db.single_insert(insert_card_product_list_query)
                flash("card product list added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
        
        return redirect(url_for('adminproductlist'))

    # Fetch all cards
    card_product_list = db.fetchall("""
            SELECT cpl.card_product_list_id, cpl.card_type_id, cpl.product_id, cpl.month, cpl.unit_price, cpl.max_unit, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            JOIN card_type c ON cpl.card_type_id = c.id
            JOIN product p ON cpl.product_id = p.product_id
        """)

    # Fetch all card types to display in the dropdown
    products = db.fetchall("SELECT product_id, product_name FROM product")
    card_type= db.fetchall("SELECT card_type, id  FROM card_type")
    card_product_to_edit = None
    if 'edit' in request.args:
        card_product_list_id = request.args.get('edit')
        
        card_product_to_edit = db.fetchone(f"""
            SELECT cpl.*, p.product_name AS product_name, c.card_type AS card_type
            FROM card_product_list cpl
            LEFT JOIN card_type c ON cpl.card_type_id = c.id
            LEFT JOIN product p ON cpl.product_id = p.product_id
            WHERE cpl.card_product_list_id = {card_product_list_id}
        """)

    print(f"cards to edit:{card_product_to_edit}")
    print(f"card product list :{card_product_list}")
    return render_template("admin/product_list.html", card_type=card_type, products=products, card_product_list = card_product_list,  card_product_to_edit= card_product_to_edit)

@app.route("/delete-product-list", methods=["POST"])
def delete_product_list():
    try:
        card_product_list_id= request.args.get('card_product_list_id')
        print(f'this is card id:{card_product_list_id}')
        delete_product_list_query = f"DELETE FROM card_product_list WHERE card_product_list_id = {card_product_list_id}"
        db.execute(delete_product_list_query)
        flash("delete product list deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete stock: {str(e)}", "danger")
    
    return redirect(url_for('adminproductlist'))

@app.route("/admin-to-sell", methods=["GET", "POST"])
def admintosell():
    # Fetch all cards to display in the dropdown when searching
    cards = db.fetchall("""
        SELECT c.card_details_id, c.adhar_no, c.card_type_id, t.card_type 
        FROM card_details c 
        JOIN card_type t ON c.card_type_id = t.id
    """)
    
    # Fetch all products types to display in the dropdown
    products = db.fetchall("SELECT product_id, product_name FROM product")
    adhar_data = db.fetchall("SELECT card_details_id, adhar_no, card_type_id FROM card_details")
    # Fetch all card types to display in the dropdown
    stocks = db.fetchall(f"""
            SELECT 
            s.stock_id, 
            s.month, 
            s.product_id, 
            s.unit AS arrived_stock, 
            p.product_name, 
            p.unit AS current_stock
        FROM 
            stocks s
        JOIN 
            product p ON s.product_id = p.product_id
        WHERE 
            EXTRACT(YEAR FROM s.month) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM s.month) = EXTRACT(MONTH FROM CURRENT_DATE)
            """       
            )


    stocks_from_month = None
    if 'month' in request.args:
        stocks_from_month = 'no data'
        month_str = request.args.get('month') 
        print(f"this is mont_str:{month_str}")
        # Parse the month_str into a datetime object to extract month and year
        from datetime import datetime

        if month_str:
            # Convert string date to datetime object
            selected_date = datetime.strptime(month_str, '%Y-%m')
            
        # Extract the month and year
        selected_month = selected_date.month
        selected_year = selected_date.year
        stocks_from_month = db.fetchall(f"""
        SELECT 
            s.stock_id, 
            s.month, 
            s.product_id, 
            s.unit AS arrived_stock, 
            p.product_name, 
            p.unit AS current_stock
        FROM 
            stocks s
        JOIN 
            product p ON s.product_id = p.product_id
        WHERE 
            EXTRACT(YEAR FROM s.month) = '{selected_year}'
            AND EXTRACT(MONTH FROM s.month) = '{selected_month}'
        """)
        if not stocks_from_month:
           stocks_from_month = 'no data'

    print(f"cards to edit:{stocks_from_month}")
    print(f"cards :{stocks}")
    print(f"products :{products}")
    print(f"cards :{cards}")
    print(f"this is adhar data{adhar_data}")
    return render_template("admin/to_sell.html", adhar_data=adhar_data, products=products, cards=cards, stocks=stocks, stocks_from_month=stocks_from_month)

@app.route("/admin-sell-product", methods=["GET", "POST"])
def adminsellproduct():
    if request.method == "POST":
        purchase_data=None
        purchase_details= None
        product_list_info= None
        purchase_data_to_edit = None
        stock_id = request.form.get('stock_id')
        product_id = request.form['product_id']
        product_name = request.form['product_name']
        adhar_no = request.form['adhar_no']
        current_stock = request.form['current_stock']
        arrived_stock = request.form['arrived_stock']
        card_details_id = request.form['card_details_id']
        month_str = request.form['month']
        from datetime import datetime
        card_type_id = request.form['card_type_id']
        unit= request.form['unit']
        total_amount = request.form['total_amount']
        print(f"this is unit and total amount:{unit}and{total_amount}")
        print(f"card type id:{card_type_id}")

        try:
                select_purchase_details_query = f"""
                    SELECT pl.purchase_details_id, pl.month, pl.amount, p.product_name, c.card_type_id, ct.card_type
                    FROM purchase_details AS pl
                    LEFT JOIN product AS p ON pl.product_id = p.product_id
                    LEFT JOIN card_details AS c ON pl.card_details_id = c.card_details_id
                    LEFT JOIN card_type AS ct ON c.card_type_id = ct.id
                    WHERE pl.card_details_id = {card_details_id}
                """
                purchase_details = db.fetchall(select_purchase_details_query)
                print(f"purchase_details_info:{purchase_details}")
        except Exception as e:
                flash(f"Failed to delete stock: {str(e)}", "danger")
                print(f"purchase exeption: {str(e)}")
        print(f"this is purcahse details:{purchase_details}")

        if  total_amount != '1':
            try:
                current_unit_query = f"""
                        SELECT unit FROM product WHERE product_id = {product_id}
                        """
                current_unit_result = db.fetchone(current_unit_query)

                if current_unit_result:
                    current_unit_str = current_unit_result['unit']  
                    #FILTER INTO INT 
                    current_unit = int(re.sub(r'\D', '', current_unit_str))  
                else:
                            current_unit = 0 
                
                #new unit to add in product table
                purchased_unit = int(unit)
                print(f"current_unit:{current_unit}")
                new_unit = current_unit - purchased_unit
                print(f"new_unit:{new_unit}")

                update_product_query = f"""
                        UPDATE product
                        SET unit = '{new_unit}'
                        WHERE product_id = {product_id}
                        """
                db.execute(update_product_query)
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
                print(f'exeption unit:{str(e)}"')
               
            try:
                # Set the current date for 'month'
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                insert_purchase_query = f"""
                INSERT INTO purchase_details (stock_id, card_details_id, product_id, month, amount, unit)
                VALUES ({stock_id}, {card_details_id}, {product_id}, '{current_date}', '{total_amount}', '{unit}')
                """
                db.single_insert(insert_purchase_query)
                purchase_data=None
                purchase_details=None

                flash("Purchase details added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add product: {str(e)}", "danger")
                print(f'exeption purchase:{str(e)}"')
            return redirect(url_for('adminpurchaselist', card_details_id=card_details_id))

        else:
            month = datetime.strptime(month_str, "%Y-%m")
            purchase_data = {
                "stock_id": stock_id,
                "product_id": product_id,
                "product_name": product_name,
                "adhar_no": adhar_no,
                "current_stock": current_stock,
                "arrived_stock": arrived_stock,
                "card_details_id": card_details_id,
                "month": month,
                "card_type_id": card_type_id
            }
            print(f'this is product id:{product_id}')
            print(f"this is card_details_id:{card_details_id}")
            print(f"this is card_type_id:{card_type_id}")
            try:
                print(f"this is month details to fetch:{month}")
                select_product_list_query = f"""
                    SELECT unit_price, max_unit, month
                    FROM card_product_list
                    WHERE EXTRACT(YEAR FROM month) = '{month.year}'
                    AND EXTRACT(MONTH FROM month) = '{month.month}'
                    AND product_id = {product_id} 
                    AND card_type_id = {card_type_id}
                """
                product_list_info = db.fetchall(select_product_list_query)
                print(f"product_list_info:{product_list_info}")
            except Exception as e:
                flash(f"Failed to delete stock: {str(e)}", "danger")
                print(f"execption: {str(e)}")

            
        
    return render_template("admin/sell_product.html",purchase_details=purchase_details, purchase_data=purchase_data, product_list_info=product_list_info, purchase_data_to_edit= purchase_data_to_edit )

@app.route("/admin-purchase-list", methods=["GET", "POST"])
def adminpurchaselist():
    purchase_details= None
    if 'card_details_id' in request.args:
        card_details_id= request.args.get('card_details_id')
        purchase_details= None
        # month_str = request.form['month']
        # from datetime import datetime
        # card_type_id = request.form['card_type_id']
        try:
                select_purchase_details_query = f"""
                    SELECT pl.purchase_details_id, pl.unit, pl.month, pl.amount, p.product_name, c.card_type_id, c.adhar_no, ct.card_type
                    FROM purchase_details AS pl
                    LEFT JOIN product AS p ON pl.product_id = p.product_id
                    LEFT JOIN card_details AS c ON pl.card_details_id = c.card_details_id
                    LEFT JOIN card_type AS ct ON c.card_type_id = ct.id
                    WHERE pl.card_details_id = {card_details_id}
                """
                purchase_details = db.fetchall(select_purchase_details_query)
                print(f"purchase_details_info:{purchase_details}")
        except Exception as e:
                flash(f"Failed to delete stock: {str(e)}", "danger")
                print(f"purchase exeption: {str(e)}")
        print(f"this is purcahse details:{purchase_details}")
    elif 'adhar_no' in request.args:
        try:
                adhar_no= request.args.get('adhar_no')
                select_purchase_details_query = f"""
                    SELECT pl.purchase_details_id, pl.unit, pl.month, pl.amount, p.product_name, c.card_type_id, c.adhar_no, ct.card_type
                    FROM purchase_details AS pl
                    LEFT JOIN product AS p ON pl.product_id = p.product_id
                    LEFT JOIN card_details AS c ON pl.card_details_id = c.card_details_id
                    LEFT JOIN card_type AS ct ON c.card_type_id = ct.id
                    WHERE c.adhar_no = '{adhar_no}'
                """
                purchase_details = db.fetchall(select_purchase_details_query)
                print(f"purchase_details_info:{purchase_details}")
        except Exception as e:
                flash(f"Failed to delete stock: {str(e)}", "danger")
                print(f"purchase exeption: {str(e)}")
                print(f"this is purcahse details:{purchase_details}")

    
    else:
        try:
                select_purchase_details_query = f"""
                    SELECT pl.purchase_details_id, pl.unit, pl.month, pl.amount, p.product_name, c.card_type_id, c.adhar_no, ct.card_type
                    FROM purchase_details AS pl
                    LEFT JOIN product AS p ON pl.product_id = p.product_id
                    LEFT JOIN card_details AS c ON pl.card_details_id = c.card_details_id
                    LEFT JOIN card_type AS ct ON c.card_type_id = ct.id
                """
                purchase_details = db.fetchall(select_purchase_details_query)
                print(f"purchase_details_info:{purchase_details}")
        except Exception as e:
                flash(f"Failed to delete stock: {str(e)}", "danger")
                print(f"purchase exeption: {str(e)}")
        print(f"this is purcahse details:{purchase_details}")

        
    return render_template("admin/purchase_list.html",purchase_details=purchase_details)




# @app.route("/delete-stock", methods=["POST"])
# def delete_stock():
#     try:
#         stock_id= request.args.get('stock_id')
#         print(f'this is card id:{stock_id}')
#         delete_stock_query = f"DELETE FROM stocks WHERE stock_id = {stock_id}"
#         db.execute(delete_stock_query)
#         flash("stocks deleted successfully!", "success")
#     except Exception as e:
#         flash(f"Failed to delete stock: {str(e)}", "danger")
    
#     return redirect(url_for('adminstock'))


# running application 
if __name__ == '__main__': 
    app.run(debug=True) 