import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DEBUG'] = True  # Enable debug mode
app.config['DEFAULT_CSV'] = 'bots3_fields_name.csv'  # Set the default CSV file


ALLOWED_EXTENSIONS = {'csv', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    global df  # Declare df as a global variable
    data = None
    columns = None
    event_codes = None
    fields = None
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
            file.save(filepath)
            df = pd.read_csv(filepath)
            # Splitting and stacking
            s = df['field'].str.split(' ').apply(lambda x: pd.Series(x)).stack()
            s.index = s.index.droplevel(-1)
            s.name = 'field'
            del df['field']
            df = df.join(s)
            # Get unique values for dropdowns
            event_codes = df['EventCode'].drop_duplicates().tolist()
            fields = s.drop_duplicates().tolist()
            # Preparing data for rendering
            data = df.to_dict(orient='records')
            columns = [{"title": col} for col in df.columns]
    return render_template('index.html', data=data, columns=columns, event_codes=event_codes, fields=fields)


@app.route('/filter', methods=['POST'])
def filter_data():
    global data, columns
    event_code = request.form.get('eventCode')
    field = request.form.get('field')
    df = pd.DataFrame(data)
    if event_code:
        df = df[df['EventCode'] == int(event_code)]
    if field:
        df = df[df['field'].str.contains(field, case=False, na=False)]
    data = df.to_dict(orient='records')
    return jsonify(data=data, columns=columns)

@app.route('/get_associated_event_codes', methods=['POST'])
def get_associated_event_codes():
    selected_field = request.form.get('field')
    global df  # Indicate that df is the global variable
    if df is not None and selected_field:
        filtered_df = df[df['field'].str.lower() == selected_field.lower()]
        available_event_codes = filtered_df['EventCode'].unique().tolist()
        return jsonify(available_event_codes)
    return jsonify([])

@app.route('/get_associated_fields', methods=['POST'])
def get_associated_fields():
    selected_event_code = request.form.get('eventCode')
    global df  # Indicate that df is the global variable
    if df is not None and selected_event_code:
        filtered_df = df[df['EventCode'] == int(selected_event_code)]
        available_fields = filtered_df['field'].unique().tolist()
        return jsonify(available_fields)
    return jsonify([])  # Return an empty list if df is None or no event code is selected


@app.route('/clear', methods=['POST'])
def clear():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index'))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure upload folder exists
    app.run()