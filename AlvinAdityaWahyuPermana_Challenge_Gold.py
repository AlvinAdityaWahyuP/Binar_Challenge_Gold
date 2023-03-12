
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from flask import Flask, request, jsonify, render_template
import numpy
import re
import pandas as pd
import sqlite3



 
abusive  = pd.read_csv('abusive.csv', encoding = 'latin-1')
abusive = abusive['ABUSIVE'].tolist()
abusive


def sensor_abusive (old_text,abusive):
    
    
    old_text = old_text.lower()
    
  
    
   
    list_old = re.split(' ', old_text)
    

    for i in abusive :
        for j in list_old:
            if j == i :
                index = list_old.index(j)
                list_old[index] = '***'
    
    
    list_old = ' '.join(map(str,list_old))
    return list_old

app = Flask(__name__)

###############################################################################################################
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Documentation for Data Processing and Modeling'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'Dokumentasi API untuk Data Processing dan Modeling')
        }, host = LazyString(lambda: request.host)
    )

swagger_config = {
        "headers":[],
        "specs":[
            {
            "endpoint":'docs',
            "route":'/docs.json'
            }
        ],
        "static_url_path":"/flasgger_static",
        "swagger_ui":True,
        "specs_route":"/docs/"
    }

swagger = Swagger(app, template=swagger_template, config=swagger_config)
###############################################################################################################


@app.route('/')
def home ():
    return render_template("index.html")


@swag_from("docs/get16.yml", methods=['GET'])
@app.route('/get')
def testget():

    conn = sqlite3.connect('sql_gold.db')
    query = ''' select *
            from tweet '''
    
    df = pd.read_sql_query(query, conn)
    conn.commit()
    conn.close()
    data_dict = df.to_dict('record')

    response_data = jsonify(data_dict)
    return response_data



@swag_from("docs/post16.yml", methods=['POST'])
@app.route('/input', methods =['POST'])
def gold () : 
    
    input_json = request.get_json(force=True) 
    old_text  =  input_json ['tweet']

    text  = sensor_abusive(old_text,abusive)
    
    json_text = {
        "tweet" : old_text,
        "tweet_new" : text,
    }

    text = pd.DataFrame([json_text])

    conn = sqlite3.connect('sql_gold.db')
    text.to_sql('tweet' , conn, if_exists = 'append', index = False)
    conn.close()

    return jsonify(json_text)


@swag_from("docs/upload16.yml", methods=['POST'])
@app.route('/upload', methods =['POST'])
def uploaddoc () : 

  

    file = request.files['file']

    try:
        df = pd.read_csv(file, encoding='iso-8859-1', error_bad_lines=False)
    except:
        df = pd.read_csv(file, encoding='utf-8', error_bad_lines=False)
    

    
    df['tweet_new'] = df['tweet'].apply(lambda x : sensor_abusive(x,abusive))
    df = df[['tweet', 'tweet_new']]
    simpan = df.to_dict('record')

    conn = sqlite3.connect('sql_gold.db')

    cursor = conn.cursor()
    for i in simpan:
        cursor.execute("INSERT INTO tweet (tweet, tweet_new) VALUES (?,?) ", (i['tweet'],i['tweet_new']))
    conn.commit()
    conn.close()


    return jsonify(simpan)
 
if __name__ == "__main__":
    app.run()

