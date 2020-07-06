from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json
import sys

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rohit:nfs@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Todo(db.Model):
    __tablename__='todos'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self):
        return f'<todo: id-{self.id}, description-{self.description}'


class TodoList(db.Model):
    __tablename__='todolists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship("Todo", backref='list', lazy=True, cascade="all, delete-orphan")


@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html', todos=Todo.query.filter_by(list_id=list_id).order_by('id').all(),
        lists=TodoList.query.order_by('id').all(), active_list=TodoList.query.get(list_id))


@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json()['description']
        list_id = request.get_json()['list_id']
        todo = Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['completed'] = todo.completed
        body['description'] = todo.description
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        return jsonify(body)
    else:
        abort(500)


@app.route('/lists/createList', methods=['POST'])
def create_todo_list():
    error = False
    body = {}
    try:
        name = request.get_json()['name']
        todolist = TodoList(name=name)
        db.session.add(todolist)
        db.session.commit()

        body = {'name': todolist.name, 'id':todolist.id}
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        return jsonify(body)
    else:
        abort(500)


@app.route('/todos/<todo_id>/setCompleted', methods=['POST'])
def set_completed(todo_id):
    error = False
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        return redirect(url_for('index'))
    else:
        abort(500)


@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    error = False
    try:
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        return jsonify({ 'success': True })
    else:
        abort(500)


@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_todo_list(list_id):
    error = False
    try:
        todolist = TodoList.query.get(list_id)
        db.session.delete(todolist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        redirect(url_for('get_list_todos', list_id=1))
        return jsonify({ 'success': True })
    else:
        abort(500)


@app.route('/lists/<list_id>/setCompleted', methods=['POST'])
def set_completed_list(list_id):
    error = False

    try:
        list = TodoList.query.get(list_id)
        checked = request.get_json()['checked']

        for todo in list.todos:
            todo.completed = checked

        db.session.commit()
    except:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return '', 200


if __name__ == '__main__':
    app.run(debug=True)