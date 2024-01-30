from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    attendance = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), db.ForeignKey('student.roll_no'), nullable=False)
    attendance_status = db.Column(db.String(10), nullable=False)
    custom_date = db.Column(db.String(20), nullable=False)

# Move db.create_all() inside the application context
with app.app_context():
    db.create_all()

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json()

    roll_no = data.get('roll_no')
    name = data.get('name')

    if not roll_no or not name:
        return jsonify({'error': 'Roll number and name are required'}), 400

    # Check if student with the same roll number already exists
    existing_student = Student.query.filter_by(roll_no=roll_no).first()

    if existing_student:
        return jsonify({'error': 'Student with the same roll number already exists'}), 409

    new_student = Student(roll_no=roll_no, name=name)
    db.session.add(new_student)
    db.session.commit()

    return jsonify({'message': 'Student added successfully'}), 201


@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    data = request.get_json()

    roll_no = data.get('roll_no')
    attendance_status = data.get('attendance_status')
    custom_date = data.get('custom_date')

    if not roll_no or not attendance_status or not custom_date:
        return jsonify({'error': 'Roll number, attendance status, and custom date are required'}), 400

    student = Student.query.filter_by(roll_no=roll_no).first()

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    new_attendance = Attendance(roll_no=roll_no, attendance_status=attendance_status, custom_date=custom_date)
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({'message': 'Attendance recorded successfully'}), 201

@app.route('/check_attendance', methods=['GET'])
def check_attendance():
    roll_no = request.args.get('roll_no')
    custom_date = request.args.get('custom_date')

    if not roll_no or not custom_date:
        return jsonify({'error': 'Roll number and custom date are required'}), 400

    student = Student.query.filter_by(roll_no=roll_no).first()

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    attendance_record = Attendance.query.filter_by(roll_no=roll_no, custom_date=custom_date).first()

    if not attendance_record:
        return jsonify({'message': 'Attendance not recorded for the given date'}), 404

    attendance_status = attendance_record.attendance_status

    return jsonify({'roll_no': roll_no, 'name': student.name, 'attendance_status': attendance_status, 'date': custom_date})

@app.route('/attendance_details_by_status', methods=['GET'])
def attendance_details_by_status():
    custom_date = request.args.get('custom_date')
    attendance_status = request.args.get('attendance_status')

    if not custom_date or not attendance_status:
        return jsonify({'error': 'Custom date and attendance status are required'}), 400

    attendance_records = Attendance.query.filter_by(custom_date=custom_date, attendance_status=attendance_status).all()

    if not attendance_records:
        return jsonify({'message': f'No {attendance_status} attendance recorded for the given date'}), 404

    attendance_details = []
    for record in attendance_records:
        attendance_details.append({
            'roll_no': record.roll_no,
            'name': record.student.name,
            'attendance_status': record.attendance_status,
            'date': custom_date
        })

    return jsonify({'attendance_details': attendance_details})

@app.route('/modify_attendance_status', methods=['PUT'])
def modify_attendance_status():
    data = request.get_json()

    roll_no = data.get('roll_no')
    custom_date = data.get('custom_date')
    new_attendance_status = data.get('new_attendance_status')

    if not roll_no or not custom_date or not new_attendance_status:
        return jsonify({'error': 'Roll number, custom date, and new attendance status are required'}), 400

    attendance_record = Attendance.query.filter_by(roll_no=roll_no, custom_date=custom_date).first()

    if not attendance_record:
        return jsonify({'error': 'Attendance record not found'}), 404

    attendance_record.attendance_status = new_attendance_status
    db.session.commit()

    return jsonify({'message': 'Attendance status modified successfully'})


if __name__ == '__main__':
    app.run(debug=True)
