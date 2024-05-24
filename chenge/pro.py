from flask import Flask,redirect,url_for,render_template,request,jsonify,send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import cv2
import subprocess
import sys
import shutil
from datetime import datetime
import win32gui
import win32con
import time

#
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/login"
db = SQLAlchemy(app)


# assing database attribute for integrestion to the server database
class New(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    fname = db.Column(db.String(80), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    pin = db.Column(db.String(6), nullable=False)
    dlno = db.Column(db.String(15), nullable=False)
    doi = db.Column(db.Date, nullable=False)
    validtill = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(255), nullable=False)
    fdata = db.Column(db.String(255), nullable=False)



@app.route("/")
def home():
    return render_template("1 home.html")

# after click on home page it will redirect to this page
@app.route("/new")
def new():
    return render_template("2.html")

# after click on the left side redirect to this form
@app.route("/old")
def old():
    return render_template("4.html")


# the login form of the page
@app.route("/login", methods=['POST','GET'])
def login():
    if request.method == "POST":
        user = request.form["full-name"]
        fuser = request.form["relativeName"]
        DOB = request.form["dob"]
        doi = request.form["doi"]
        Dnum = request.form["dl-number"]
        VD = request.form["valid-till"]
        address = request.form['address']
        pin = request.form['pin-code']

        # collecting photo or image from the user
        if 'profilePic' in request.files:

            pic = request.files['profilePic']
            if pic.filename != '':
                image_path = os.path.join("static/", secure_filename(pic.filename))
                pic.save(image_path)
            else:
                return url_for("login")

        sing = "chenge/uplod"

        # storing all the files or data on database with add() and below methods
        entry = New(name = user, fname = fuser, dob = DOB, doi= doi, address = address, pin = pin, dlno = Dnum, validtill = VD, photo = secure_filename(pic.filename),fdata  = sing)
        db.session.add(entry)
        db.session.commit()
        return render_template("3.html")
    else:
       return render_template("2.html")


# close window
def run_as_admin(command):
    try:
        # Use ShellExecute to run the program as administrator
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as e:
        print(f"Error: {e}")

#giving the path for the fingerprint image
def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
    except Exception as e:
        print(f"Error copying file: {e}")
        sys.exit(1)



@app.route('/start_capture', methods=['POST'])
def start_capture():
    number = request.form['number']
    # Path to the biometric fingerprint capture program
    program_path = r"C:\Program Files\Mantra\MFS100\Driver\MFS100Test\MANTRA.MFS100.Test.exe"

    # Destination directory to save the captured images
    destination_dir = r"D:/work/major_progect/chenge/uploads/"

    # Run the program as administrator
    run_as_admin([program_path])

    # Wait for the program to initialize (adjust sleep time if needed)
    time.sleep(15)

    # Assuming the biometric fingerprint program saves the image to this path
    source_path = r"C:\Program Files\Mantra\MFS100\Driver\MFS100Test\FingerData\FingerImage.bmp"

    # Generate a unique filename based on the current timestamp and user's name
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    new_filename = f"{number}_FingerImage_{current_time}.bmp"

    # Construct the full destination path for the new image
    destination_path = os.path.join(destination_dir, new_filename)

    # Copy the captured image to the destination
    copy_file(source_path, destination_path)

    # for add path to the database
    result = New.query.filter_by(dlno=number).first()
    if result:
        result.fdata = os.path.join("uploads/", secure_filename(new_filename))
        db.session.commit()

    return jsonify({'message': f"Image captured and saved for {number} as {new_filename}", 'filename': new_filename})





# closeing the window for the exicution
def close_window_by_title(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd != 0:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return True
    else:
        print("Window not found!")
        return False


#Authentication model for fingerprint
@app.route('/match_capture', methods=['POST','GET'])
def match_capture():

    # Path to the biometric fingerprint capture program
    program_path = r"C:\Program Files\Mantra\MFS100\Driver\MFS100Test\MANTRA.MFS100.Test.exe"

    # Run the program as administrator
    run_as_admin([program_path])

    # Wait for the program to initialize (adjust sleep time if needed)
    time.sleep(15)

    window_title = "MFS100"

    if close_window_by_title(window_title):

         # Assuming the biometric fingerprint program saves the image to this path
        sample = cv2.imread("C:/Program Files/Mantra/MFS100/Driver/MFS100Test/FingerData/FingerImage.bmp")

        # Initialize variables to store the best matching result
        best_score = 0
        filename = None
        image = None
        kp1, kp2, mp = None, None, None

        #variable for sift model
        sbest_score = 0
        sfilename = None
        simage = None
        skp1, skp2, smp = None, None, None

        # Loop through each fingerprint image in the directory
        for file in os.listdir("uploads"):
            # Read the fingerprint image
            fingerprint_image = cv2.imread("uploads/" + file)

            # Initialize ORB detector Oriented FAST and Rotated BRIEF (ORB)
            orb = cv2.ORB_create()
            sift = cv2.SIFT_create()

            #sift model (Scale-Invariant Feature Transform)

            skeypoints_1, sdescriptors_1 = sift.detectAndCompute(sample, None)
            skeypoints_2, sdescriptors_2 = sift.detectAndCompute(fingerprint_image, None)

            smatches = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 10}, {}).knnMatch(sdescriptors_1, sdescriptors_2,
                                                                                        k=2)
            smatch_points = []

            for p, q in smatches:
                if p.distance < (0.4 * q.distance):
                    smatch_points.append(p)

            skeypoints = 0
            if len(skeypoints_1) < len(skeypoints_2):
                skeypoints = len(skeypoints_1)
            else:
                skeypoints = len(skeypoints_2)

            if len(smatch_points) / skeypoints * 100 > sbest_score:
                sbest_score = len(smatch_points) / skeypoints * 100
                sfilename = file
                simage = fingerprint_image
                skp1, skp2, smp = skeypoints_1, skeypoints_2, smatch_points

            #orb model

            # Find keypoints and descriptors for the sample and current fingerprint image
            keypoints_1, descriptors_1 = orb.detectAndCompute(sample, None)
            keypoints_2, descriptors_2 = orb.detectAndCompute(fingerprint_image, None)

            # Match descriptors using FLANN matcher
            matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
            matches = matcher.match(descriptors_1, descriptors_2)

            # Filter matches based on distance
            match_points = []
            for match in matches:
                if match.distance < 55:  # Adjust this threshold as needed
                    match_points.append(match)

            # Calculate the number of keypoints
            keypoints = min(len(keypoints_1), len(keypoints_2))

            # Calculate the score based on the number of matched keypoints
            score = len(match_points) / keypoints * 100

            # Update the best score and corresponding information if a better match is found
            if score > best_score:
                best_score = score
                filename = file
                image = fingerprint_image
                kp1, kp2, mp = keypoints_1, keypoints_2, match_points

        if best_score >= 2:

            # Print the best matching result
            print("BEST MATCH : " + str(filename))
            print("SCORE: " + str(best_score))

            print("BEST MATCH : " + str(sfilename))
            print("SCORE: " + str(sbest_score))

             # finding the fingerprint that are match to the present fingerprint data from model 1
            pic = os.path.join("uploads/", secure_filename(filename))
            result = New.query.filter_by(fdata = pic ).first()

            if result:
                return render_template('show.html', data=result)
            else:
                # finding the fingerprint that are match to the present fingerprint data from model 2
                pic1 = os.path.join("uploads/", secure_filename(sfilename))
                result1 = New.query.filter_by(fdata=pic1).first()
                return render_template('show.html', data=result1)

            # Draw the matches
            # result = cv2.drawMatches(sample, kp1, image, kp2, mp, None)
            # result = cv2.resize(result, None, fx=1, fy=1)
            # cv2.imshow("Result", result)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
            # return redirect("/match_fingerprint")

        else:
            print("Match Not found!")
            return render_template('show.html', data=None)

    else:
        return redirect("/match_capture")



# If fingerprint match the data will show
@app.route('/match_fingerprint')
def match_fingerprint():
    return render_template("show.html")

#If fingerprint is not match the no data will show.
@app.route('/no_match_fingerprint')
def no_match_fingerprint():
    return "<h1>Match Not Found! </h1>"


# for testing purpose
@app.route('/kb')
def kb():
    return render_template("3.html")


# for act and rules show data.
@app.route('/acts_and_rules')
def acts_and_rules():
    # Provide the path to your PDF file
    pdf_path = 'The-Road-Regulations-Rules-1989.pdf'
    return send_file(pdf_path, as_attachment=True)

# main function for exicution
if __name__ == "__main__":
    app.run(debug=True)
    db.create_all()






# @app.route("/name")
# def name():
#     return render_template("3.html")