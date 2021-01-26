from typing import Generic, TypeVar, Type

import flask
from flask import Blueprint
from flask_login import current_user, login_required, logout_user
from datetime import datetime

from lagom import Container, bind_to_container, injectable
from sqlalchemy.orm import Query

from server.api.utils import jsonify_response, paginate
from server.error_handling import RouteError
from server.api.database.models import Topic


topics_routes = Blueprint("topics", __name__, url_prefix="/topics")

deps = Container()


T = TypeVar("T")


class SqlOrmModel(Generic[T]):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    @property
    def query(self) -> Query:
        return self.model_class.query

    def create(self, **kwargs) -> T:
        return self.model_class.create(**kwargs)

    def get_by_id(self, record_id):
        return self.model_class.get_by_id(record_id)


deps[SqlOrmModel[Topic]] = SqlOrmModel(Topic)


def init_app(app):
    app.register_blueprint(topics_routes)


@topics_routes.route("/", methods=["GET"])
@jsonify_response
@login_required
@bind_to_container(deps)
def topics(topic_repo: SqlOrmModel[Topic] = injectable):
    return {"data": [topic.to_dict() for topic in topic_repo.query.all()]}


@topics_routes.route("/", methods=["POST"])
@jsonify_response
@login_required
@bind_to_container(deps)
def new_topic(topic_repo: SqlOrmModel[Topic] = injectable):
    if not current_user.is_admin:
        raise RouteError("Admin required.", 401)

    data = flask.request.get_json()
    topic = topic_repo.create(
        title=data.get("title"),
        min_lesson_number=data.get("min_lesson_number"),
        max_lesson_number=data.get("max_lesson_number"),
    )
    return {"data": topic.to_dict()}, 201


@topics_routes.route("/<int:topic_id>", methods=["DELETE"])
@jsonify_response
@login_required
@bind_to_container(deps)
def delete_topic(topic_id, topic_repo: SqlOrmModel[Topic] = injectable):
    if not current_user.is_admin:
        raise RouteError("Admin required.", 401)
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        raise RouteError("Topic does not exist", 404)
    topic.delete()
    return {"message": "Topic deleted."}
