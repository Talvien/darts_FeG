from models import db, GroupStageFormat, KnockOutStageFormat
from app import app

# Initialize the database
def populate_formats():
    group_stage_formats = [
        {"format_id": 1, "format_name": "Single Round Robin"},
        {"format_id": 2, "format_name": "Double Round Robin"},
        {"format_id": 3, "format_name": "Keine Group Stage"},
    ]
    knock_out_stage_formats = [
        {"format_id": 1, "format_name": "Single Elimination"},
        {"format_id": 2, "format_name": "Double Elimination"},
        {"format_id": 4, "format_name": "Keine Knock-Out Stage"},
    ]

    with app.app_context():
        for format in group_stage_formats:
            if not db.session.query(GroupStageFormat).filter_by(format_id=format["format_id"]).first():
                db.session.add(GroupStageFormat(**format))
        
        for format in knock_out_stage_formats:
            if not db.session.query(KnockOutStageFormat).filter_by(format_id=format["format_id"]).first():
                db.session.add(KnockOutStageFormat(**format))
        
        db.session.commit()

# Call the function to populate the formats

# Call the function to populate the formats
populate_formats()

