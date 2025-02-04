from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager
from flask_migrate import Migrate
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.exceptions import ApiException
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
import os
from dotenv import load_dotenv
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:your_password@localhost/expenses'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# 加载环境变量
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# Plaid 配置
configuration = Configuration(
    host=f"https://{PLAID_ENV}.plaid.com",
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }
)
api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)


login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    plaid_items = db.relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")

class PlaidItem(db.Model):
    __tablename__ = "plaid_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # 外键
    access_token = db.Column(db.String(255), nullable=False)
    item_id = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", back_populates="plaid_items")  # 关联用户表

    def __repr__(self):
        return f"<PlaidItem {self.id}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# Dashboard route (protected by login)
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_data = db.session.query(User).filter_by(id=session['user_id']).first()
    accounts = db.session.query(PlaidItem).filter_by(user_id=user_data.id).all()

    return render_template('dashboard.html', user=user_data, accounts=accounts)

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/create_link_token', methods=['POST'])
def create_link_token():
    try:
        print(CountryCode)
        user = LinkTokenCreateRequestUser(client_user_id="unique_user_id")  # 替换为实际用户唯一 ID
        request = LinkTokenCreateRequest(
            user=user,
            client_name="Expense Tracker App",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )
        response = plaid_client.link_token_create(request)
        return jsonify(response.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/plaid')
def plaid_page():
    return render_template('plaid.html')

@app.route('/api/exchange_public_token', methods=['POST'])
def exchange_public_token():
    try:
        # 从请求体中提取 public_token
        data = request.get_json()
        public_token = data.get('public_token')
        if not public_token:
            return jsonify({'error': 'Missing public_token'}), 400

        # 构建请求对象
        request_data = ItemPublicTokenExchangeRequest(public_token=public_token)

        # 调用 Plaid API
        response = plaid_client.item_public_token_exchange(request_data)

        access_token = response.access_token
        item_id = response.item_id
        user_id = 1  # 假设你已经有用户系统

        # 保存到数据库
        plaid_item = PlaidItem(user_id=user_id, access_token=access_token, item_id=item_id)
        db.session.add(plaid_item)
        db.session.commit()

        # 返回 access_token 和其他信息
        return jsonify({
            'access_token': response.access_token,
            'item_id': response.item_id
        })

    except ApiException as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plaid_items', methods=['GET'])
def get_plaid_items():
    items = PlaidItem.query.all()
    return jsonify([{
        'id': item.id,
        'user_id': item.user_id,
        'access_token': item.access_token,
        'item_id': item.item_id,
        'created_at': item.created_at
    } for item in items])

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    app.logger.info(f"Received webhook: {data}")
    item_id = data.get('item_id')
    new_transactions = data.get('transactions', [])

    # 更新数据库
    for txn in new_transactions:
        new_txn = db.Transaction(
            plaid_item_id=item_id,
            transaction_id=txn['transaction_id'],
            amount=txn['amount'],
            description=txn['description'],
        )
        db.session.add(new_txn)

    db.session.commit()
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True)
