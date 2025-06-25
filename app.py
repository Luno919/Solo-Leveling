import logging
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, login_required, UserMixin, logout_user
from math import ceil
import random
import requests
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import main 


# Function to fetch solved problems from the new API
def get_leetcode_solved_problems():
    url = "https://leetcode-api-faisalshohag.vercel.app/oomanish459"  # URL with JSON data
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return str(data['totalSolved'])
    return "0"


# Flask app setup
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://9jkRCv2eZwMykA5d:9jkRCv2eZwMykA5d@cluster0.midi5xt.mongodb.net/SoloLevling?retryWrites=true&w=majority&appName=Cluster0"
app.config['SECRET_KEY'] = 'pVO5gnZLnRhQIM2opVO5gnZLnRhQIM2o'

mongo = PyMongo(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Flask-Login User class wrapper for MongoDB user document
class User(UserMixin):
    def __init__(self, user_doc):
        self.user_doc = user_doc
        self.id = str(user_doc['_id'])
        self.uid = user_doc['uid']
        self.IQ = user_doc.get('IQ', 0)
        self.strength = user_doc.get('strength', 0)
        self.speed = user_doc.get('speed', 0)
        self.consistency = user_doc.get('consistency', 0)
        self.level = user_doc.get('level', 0)

    def get_id(self):
        return str(self.uid)


@login_manager.user_loader
def load_user(user_id):
    user_doc = mongo.db.users.find_one({'uid': int(user_id)})
    if user_doc:
        return User(user_doc)
    return None


@app.route('/signup')
def signup_page():
    return render_template('signup.html', val="")


@app.route("/signupauth", methods=['POST'])
def signup():
    
    val = random.randint(1000000000, 9999999999)
    new_user = {
        'uid': val,
        'quest_count':0,
        'quest':[],
        'tip':[],
    }
    daily_task = {
        'uid': val,
        'Pushups': 0,
        'Squats': 0,
        'Planks': 0,
        f'Leetcode {get_leetcode_solved_problems()}': 0,

    }

    mongo.db.users.insert_one(new_user)
    mongo.db.daily_tasks.insert_one(daily_task)
    return render_template('signup.html', val=val)


@app.route('/')
def index():
    return render_template('login.html')
@app.route('/loginauth', methods=['POST'])
def login():
    uid = request.form.get('myuid')
    if uid:
        user_doc = mongo.db.users.find_one({'uid': int(uid)})
        if user_doc:
            user = User(user_doc)
            login_user(user)
            return redirect(url_for('home'))
        else:
            return "User not found"
    return "UID is required!"
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user_doc = mongo.db.users.find_one({'uid': current_user.uid})

    categories = ['IQ', 'strength', 'speed', 'consistency']
    stats = {}

    for category in categories:
        stat = mongo.db.statistics.find_one(sort=[("date", -1)], filter={'category': category})
        stats[category] = stat if stat else None

    if request.method == 'POST':
        # Update user stats in MongoDB
        mongo.db.users.update_one(
            {'uid': current_user.uid},
            {'$set': {
                'IQ': int(request.form.get('IQ', user_doc.get('IQ', 0))),
                'strength': int(request.form.get('strength', user_doc.get('strength', 0))),
                'speed': int(request.form.get('speed', user_doc.get('speed', 0))),
                'consistency': int(request.form.get('consistency', user_doc.get('consistency', 0)))
            }}
        )
    # Reload user_doc to reflect updated data
    user_doc = mongo.db.users.find_one({'uid': current_user.uid})
    return render_template('home.html', stats=stats, user=user_doc)

@app.route('/quest', methods=['GET'])
@login_required
def quest():
    tasks = list(mongo.db.quests.find({'uid': current_user.uid}))
    print(tasks)  # Now will print a list of documents
    return render_template('quest.html', tasks=tasks)

@app.route('/daily_task')
@login_required
def daily_task():
    daily_task = (mongo.db.daily_tasks.find_one({'uid': current_user.uid}))
    return render_template('daily_task.html', tasks=daily_task)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    quest=(mongo.db.users.find_one({'uid':current_user.uid}))
    rivals=list(mongo.db.Rivals.find({'uid':current_user.uid}))
    print("this is Quest---------------------------------------------------------------------------")
    skills=""
    for rival in rivals:
        skills+=str(rival['desc'])
    task=main.dynamic_quest(quest['quest'],skills)
    task['uid']=current_user.uid
    mongo.db.quests.insert_one(task)
    mongo.db.users.update_one({'uid':task['uid']},{'$push':{'quest':str(task['description'])}})
    mongo.db.users.update_one({'uid':task['uid']},{'$push':{'tip':str(task['tip'])}})
    return redirect(url_for('quest'))

    


@app.route('/update_daily_task/<task>', methods=['POST'])
@login_required
def update_daily_task(task):
    

    if "leetcode" in task.lower():
        number = int(task.split(' ')[1])
        solved = int(get_leetcode_solved_problems())
        if number < solved:
            mongo.db.daily_tasks.update_one({'uid': current_user.uid}, {'$rename': {f'Leetcode {number}': f'Leetcode {get_leetcode_solved_problems()}'}})
            mongo.db.daily_tasks.update_one({'uid':current_user.uid},{'$set': {f'Leetcode {get_leetcode_solved_problems()}': 1}})
        else:
            mongo.db.daily_tasks.update_one({'uid': current_user.uid}, {'$set': {str(task): 0}})
    else:
        mongo.db.daily_tasks.update_one({'uid': current_user.uid}, {'$set': {str(task): 1}})

    return render_template('daily_task.html', tasks=mongo.db.daily_tasks.find_one({'uid': current_user.uid}))
@app.route('/update_quest/<task_id>', methods=['POST'])
@login_required
def update_quest(task_id):
    quest = mongo.db.quests.find_one({'_id': ObjectId(task_id), 'uid': current_user.uid})
    if not quest:
        return "Task not found or unauthorized", 404
    new_done = 0 if quest.get('done', 0) == 1 else 1
    mongo.db.quests.delete_one({'_id': ObjectId(task_id), 'uid': current_user.uid})
    quest_count=mongo.db.users.find_one({'uid':current_user.uid})['quest_count']
    mongo.db.users.update_one({'uid':current_user.uid},{'$set':{'quest_count':quest_count+1}})
    return redirect(url_for('quest'))
@app.route('/Rival', methods=['GET'])
@login_required
def rival():
    rivals = list(mongo.db.Rivals.find({'uid': current_user.uid}))
    print("the for ",rivals)  #[{'_id': ObjectId('685b9080b435783ea88846f4'), 'uid': 6305308151, 'Name': 'Salman', 'desc': 'Good Communication , Consistent'}]
    return render_template('Rival.html', rivals=rivals)
@app.route('/addRivalPage')
@login_required
def addRivalPage():
    return render_template('addRival.html')
@app.route("/addRival",methods=['POST'])
def addRival():
    rival_name = request.form['rival_name']
    rival_desc = request.form['rival_Desc']
    uid = current_user.uid
    rivals={
        'uid':(uid),
        'Name':rival_name,
        'desc':rival_desc,
    }
    mongo.db.Rivals.insert_one(rivals)
    rivals= list(mongo.db.Rivals.find({'uid': current_user.uid}))
    return render_template("Rival.html",rivals=rivals)


@app.route('/update_rival/<rival_id>')
@login_required
def update_rival(rival_id):
    rival = mongo.db.Rivals.find_one({'_id': ObjectId(rival_id), 'uid': current_user.uid})
    print(quest)
    return render_template("update_rival.html",rival=rival)
@app.route("/UpdateRival",methods=['POST'])
def UpdateRival():
    rival_name = request.form['rival_name']
    rival_desc = request.form['rival_Desc']
    rival_id=request.form['rival_id']
    print(f"{rival_id}   {rival_name}   {rival_desc}")
    mongo.db.Rivals.update_one({'_id':ObjectId( rival_id)}, {'$set': {'desc': rival_desc}})
    rivals= list(mongo.db.Rivals.find({'uid': current_user.uid}))
    return render_template("Rival.html",rivals=rivals)
@app.route('/delete_rival/<rival_id>', methods=['GET'])
@login_required
def delete_Rival(rival_id):
    mongo.db.Rivals.delete_one({'_id': ObjectId(rival_id), 'uid': current_user.uid})
    return redirect(url_for('rival'))




'''
                Function Section 
'''
def calculate_statistics():
    categories = ['IQ', 'strength', 'speed', 'consistency']
    today = datetime.now().strftime("%Y-%m-%d")
    users = list(mongo.db.users.find())

    for category in categories:
        done_tasks = mongo.db.quests.count_documents({'category': category, 'done': 1})
        not_done_tasks = mongo.db.quests.count_documents({'category': category, 'done': 0})
        total_tasks = done_tasks + not_done_tasks

        mean_percentage = (done_tasks / total_tasks) if total_tasks > 0 else 0
        mean_percentage_ceil = ceil(mean_percentage)

        stat = mongo.db.statistics.find_one({'category': category, 'date': today})
        if not stat:
            stat = {
                'category': category,
                'date': today,
                'total_tasks': total_tasks,
                'done_tasks': done_tasks,
                'not_done_tasks': not_done_tasks,
                'mean': mean_percentage_ceil
            }
            mongo.db.statistics.insert_one(stat)
        else:
            # Update existing record
            mongo.db.statistics.update_one(
                {'_id': stat['_id']},
                {'$set': {
                    'done_tasks': done_tasks,
                    'not_done_tasks': not_done_tasks,
                    'total_tasks': total_tasks,
                    'mean': mean_percentage_ceil
                }}
            )

        # Update users with the mean for the category
        for user in users:
            inc = {}
            if category == 'IQ':
                inc = {'IQ': stat['mean']}
            elif category == 'strength':
                inc = {'strength': stat['mean']}
            elif category == 'speed':
                inc = {'speed': stat['mean']}

            if inc:
                mongo.db.users.update_one({'_id': user['_id']}, {'$inc': inc})

        # After updating IQ, strength, speed, update consistency and level
        for user in users:
            user_doc = mongo.db.users.find_one({'_id': user['_id']})
            consistency_inc = (user_doc.get('IQ', 0) + user_doc.get('strength', 0) + user_doc.get('speed', 0)) // 3
            level_val = (user_doc.get('IQ', 0) + user_doc.get('strength', 0) + user_doc.get('speed', 0) + user_doc.get('consistency', 0)) // 4
            mongo.db.users.update_one({'_id': user['_id']},
                                     {'$inc': {'consistency': consistency_inc}, '$set': {'level': level_val}})


def reset_tasks():
    print("Resetting tasks...")
    with app.app_context():
        calculate_statistics()
        mongo.db.quests.update_many({}, {'$set': {'done': 0}})


# Scheduler to reset tasks daily at 1:19 AM
scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_tasks, trigger="cron", hour=1, minute=19)
scheduler.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
