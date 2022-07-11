import datetime
import sys

from flask import Flask, abort, request
from flask_restful import Api, Resource, inputs, reqparse, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_calendar.db'

resource_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': fields.DateTime(dt_format='iso8601')
}


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()


class EventResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'event',
            type=str,
            help='The event name is required!',
            required=True
        )
        self.parser.add_argument(
            'date',
            type=inputs.date,
            help=
            'The event date with the correct format is required! '
            'The correct format is YYYY-MM-DD!',
            required=True
        )

    @marshal_with(resource_fields)
    def get(self):
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        if start_time and end_time:
            events = Event.query.filter(Event.date >= start_time).filter(Event.date <= end_time).all()

            if len(events) < 1:
                abort(404, {"message": "The event doesn't exist!"})
            return events

        return Event.query.all()

    def post(self):
        args = self.parser.parse_args()
        new_event = args['event']
        new_event_date = args['date'].date()

        new_event_obj = Event(event=new_event, date=new_event_date)
        db.session.add(new_event_obj)
        db.session.commit()

        return {
            'message': 'The event has been added!',
            'event': new_event,
            'date': str(new_event_date)
        }


class EventsTodayResource(Resource):
    @marshal_with(resource_fields)
    def get(self):
        return Event.query.filter(Event.date == datetime.date.today()).all()


class EventByIdResource(Resource):
    @marshal_with(resource_fields)
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")

        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}


api.add_resource(EventResource, '/event')
api.add_resource(EventsTodayResource, '/event/today')
api.add_resource(EventByIdResource, '/event/<int:event_id>')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()