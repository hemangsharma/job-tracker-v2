from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
application = app
csv_file = 'data/applications.csv'
cv_pdf_path = 'data/cv.pdf'

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def calculate_acceptance(cv_text, job_description):
    documents = [cv_text, job_description]
    count_vectorizer = CountVectorizer().fit_transform(documents)
    vectors = count_vectorizer.toarray()
    csim = cosine_similarity(vectors)
    return csim[0][1] * 100

@app.route('/')
def index():
    return redirect(url_for('view'))



@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            job_description = request.form['job_description']  # Add job_description to form
            cv_text = extract_text_from_pdf(cv_pdf_path)  # Extract text from CV
            acceptance_score = calculate_acceptance(cv_text, job_description)
            
            application = {
                'Date': request.form['application_date'],
                'Company Name': request.form['company'],
                'Position Title': request.form['position'],
                'Platform Used to Apply': request.form['platform'],
                'Job Type': request.form['job_type'],
                'Wage/Salary Type': request.form['wage_type'],
                'Application Date': request.form['application_date'],
                'Status': request.form['status'],
                'Job Description': job_description,
                'Acceptance Score': acceptance_score
            }
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                new_row = pd.DataFrame([application])
                df = pd.concat([df, new_row], ignore_index=True)
            else:
                df = pd.DataFrame([application])
            df.to_csv(csv_file, index=False)
            return redirect(url_for('view'))
        except KeyError as e:
            # Handle missing form field error
            print(f"Missing form field: {e}")
            return "Bad Request: Missing form field", 400
    return render_template('add.html')

@app.route('/view')
def view():
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        applications = df.to_dict('records')
    else:
        applications = []
    
    return render_template('view.html', applications=applications)

@app.route('/analysis')
def analysis():
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        status_counts = df['Status'].value_counts().to_dict()
        job_types = df['Job Type'].value_counts().to_dict()
        platforms = df['Platform Used to Apply'].value_counts().to_dict()
        if 'Acceptance Score' in df.columns:
            acceptance_scores = df['Acceptance Score'].tolist()
        else:
            acceptance_scores = []
    else:
        status_counts = {}
        job_types = {}
        platforms = {}
        acceptance_scores = []

    return render_template('analysis.html', status_counts=status_counts, job_types=job_types, platforms=platforms, acceptance_scores=acceptance_scores)

@app.route('/update/<int:index>', methods=['GET', 'POST'])
def update(index):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        return redirect(url_for('view'))
    
    if request.method == 'POST':
        df.at[index, 'Status'] = request.form['status']
        df.at[index, 'Interview/Test Date'] = request.form.get('interview_date', '')

        df.to_csv(csv_file, index=False)
        return redirect(url_for('view'))
    
    application = df.iloc[index].to_dict()
    return render_template('update.html', application=application, index=index)

if __name__ == '__main__':
    app.run(debug=True)
