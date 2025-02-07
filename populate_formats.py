from models import db, TournamentFormat

# Initialize the database
def populate_formats():
    dart_formats = [
        {"format_name": "Single Elimination", "description": "Players are eliminated after a single loss."},
        {"format_name": "Double Elimination", "description": "Players are eliminated after two losses."},
        {"format_name": "Round Robin", "description": "Each player plays against every other player."}, 
        {"format_name": "Swiss System", "description": "Players are paired based on their scores."}
    ]

    # Add formats to the session
    for format_data in dart_formats:
        format_entry = TournamentFormat(
            format_name=format_data['format_name'],
            description=format_data['description']
        )
        db.session.add(format_entry)

    # Commit the session to save the formats
    db.session.commit()
    print("Tournament formats added to the database.")

if __name__ == "__main__":
    from app import app  # Import your Flask app
    with app.app_context():  # Create an application context
        populate_formats()