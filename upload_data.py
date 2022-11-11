import firebase_admin
from firebase_admin import credentials, db

clinics = [{"ClinicID": 1, "Name": "Magic Paws", "Address": "Maharagama"},
           {"ClinicID": 2, "Name": "Pawing Packs", "Address": "Malabe"},
           {"ClinicID": 3, "Name": "Animal House", "Address": "Gampaha"},
           {"ClinicID": 4, "Name": "Creature Comforts", "Address": "Matara"},
           {"ClinicID": 5, "Name": "Giga Pet Clinic", "Address": "Dehiwala"},
           {"ClinicID": 6, "Name": "Puppy Love", "Address": "Maradhana"},
           {"ClinicID": 7, "Name": "Pet Life Care", "Address": "Grandpass"},
           {"ClinicID": 8, "Name": "Comfort Treatment", "Address": "Galleface"},
           {"ClinicID": 9, "Name": "Precise Vet Clinic", "Address": "Nikaweratiya"},
           {"ClinicID": 10, "Name": "Companion Care Vets", "Address": "Jayawardanapura"}]
comment_analysis = [
    {"ID": 1, "good_comment_count": 50, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 1},
    {"ID": 2, "good_comment_count": 100, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 2},
    {"ID": 3, "good_comment_count": 50, "bad_comment_count": 30, "unknown_comment_count": 0, "ClinicID": 3},
    {"ID": 4, "good_comment_count": 200, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 4},
    {"ID": 5, "good_comment_count": 800, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 5},
    {"ID": 6, "good_comment_count": 400, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 6},
    {"ID": 7, "good_comment_count": 500, "bad_comment_count": 30, "unknown_comment_count": 0, "ClinicID": 7},
    {"ID": 8, "good_comment_count": 2000, "bad_comment_count": 200, "unknown_comment_count": 0, "ClinicID": 8},
    {"ID": 9, "good_comment_count": 800, "bad_comment_count": 20, "unknown_comment_count": 0, "ClinicID": 9},
    {"ID": 10, "good_comment_count": 900, "bad_comment_count": 500, "unknown_comment_count": 0, "ClinicID": 10}]
comments = [{"CommentID": 10, "Content": "This is a dirty place", "ClinicID": 5, "Name": None, "Email": None},
            {"CommentID": 11, "Content": "I think this is the best animal hospital in Sri lanka", "ClinicID": 3,
             "Name": None, "Email": None},
            {"CommentID": 12, "Content": "I have no satisfaction with their services", "ClinicID": 4, "Name": None,
             "Email": None}]

clinic_lookup = dict()


def main():
    cred = credentials.Certificate("firebase_Dogcare_db.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://dogcarefirebase-default-rtdb.firebaseio.com/'
    })
    clinic_ref = db.reference('clinics')
    for item in clinics:
        item_ref = clinic_ref.push()
        item_ref.set(item)
        clinic_lookup[item['ClinicID']] = item_ref.key

    for item in comment_analysis:
        db.reference(f'comment_analysis/{clinic_lookup[item["ClinicID"]]}').set(item)

    comments_ref = db.reference('comments')
    for item in comments:
        item['ClinicRef'] = clinic_lookup[item["ClinicID"]]
        item_ref = comments_ref.push()
        item_ref.set(item)
        db.reference(f'clinics/{clinic_lookup[item["ClinicID"]]}/comments').push(item_ref.key)


if __name__ == '__main__':
    main()
