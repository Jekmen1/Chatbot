
from flask import Flask, request, render_template, session, redirect
import openai
from flask_sqlalchemy import SQLAlchemy

OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
app.secret_key = "T.M"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    chat_history = db.relationship('Message', backref='user', lazy=True)

    def __init__(self, email):
        self.email = email


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, sender, content, user_id):
        self.sender = sender
        self.content = content
        self.user_id = user_id


class Chatbot:
    def generate_response(self, prompt):
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            stop=["\nUser: ", "\nChatbot: "]
        )
        return response.choices[0].text.strip()

chatbot = Chatbot()

@app.route("/")
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        chat_history = Message.query.filter_by(user_id=user_id).all()
        return render_template("chatbot.html", chat_history=chat_history)
    return render_template("home.html")

@app.route("/chatbot_route", methods=["POST"])
def chatbot_route():
    if 'user_id' in session:
        user_id = session['user_id']

        user_input = request.form["message"]
        prompt = f"User: {user_input}\nChatbot: "
        bot_response = chatbot.generate_response(prompt)
        message = Message(sender="user", content=user_input, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        message = Message(sender="bot", content=bot_response, user_id=user_id)
        db.session.add(message)
        db.session.commit()
        chat_history = Message.query.filter_by(user_id=user_id).all()
        return render_template("chatbot.html", chat_history=chat_history)
    return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
        else:
            new_user = User(email=email)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
        return redirect('/')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')



if __name__ == "__main__":
    db.create_all()
    chatbot = Chatbot()
    app.run(debug=True)
