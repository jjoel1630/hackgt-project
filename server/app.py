from flask import Flask, request, jsonify
from modules.create_script import condense, convertToScript
from modules.upload_audio import init_mongodb, upload_audio
from modules.tts import chunk_text, synthesize_speech, combine_audios
from modules.conversion import *
from bson import ObjectId

from dotenv import load_dotenv

load_dotenv()
client = init_mongodb()

app = Flask(__name__)

@app.route('/')
def index():
	return "hello"

@app.route('/api/create_script', methods=['POST'])
def handle_data():
    if request.method == 'POST':
        data = request.get_json()["text"]
        duration = int (request.get_json()["duration"])
        
        script = create_script(duration, data)

        split_script = script.split(" ");
        res_arr = []
        res_arr_idx = -1
        for i in range(len(split_script)):
            if i % 100 == 0:
                res_arr_idx += 1
                res_arr.append("")

            res_arr[res_arr_idx] = res_arr[res_arr_idx] + " " + split_script[i]
        
        return jsonify({'message': 'Data received', 'text': res_arr})

@app.route('/api/upload_tts', methods=['POST'])
def upload_tts():
    script = "This lecture covers several concepts related to linear equations. Linear equations are mathematical statements representing relationships between different variables. When such equations are combined into a system, the solution for that system is the set of values for each variable making all equations true. An equivalent linear system is one that yields the same solution set. The solution can be unique, non-existent, or infinite. Diving deeper, matrices aid the solution process through row reduction operations aiming for echelon form or RREF, to reveal the solutions. RREF is a simplified representation of potential solution sets for a linear system. Two special cases are considered - overdetermined and underdetermined systems, where there are either more equations than unknowns or vice versa. Lastly, we touch upon vector equations, defining vector as an ordered list of numbers. The lecture delves into concepts like zero vector and linear combination. These underpin the understanding of systems of linear equations and their solutions. Hence, understanding these concepts brings clarity to linear algebra, which is crucial to many mathematical and scientific applications. The lecture essentially covers the fundamental concepts of linear algebra. The main topic is vectors in multi-dimensional space and their characteristics, including linear combinations and their feasible operations. The lecture emphasizes the concept of a vector span, which represents the set of all linear combinations of given vectors. Mathematical properties of vectors are discussed, and the idea of solving vector equations and linear systems using augmented matrices is introduced. Furthermore, the lecture defines \"identity matrix\", and discusses how to determine if the vector 'b' is in the span of other vectors. The concept of Ax=b, a matrix equation, is crucial in understanding linear combinations and their solutions. The lecture also explores statements logically equivalent to Ax=b in the context of matrix 'A'. The lecture introduces the terms 'homogeneous linear system' and 'non-homogeneous linear system' and explains their differences. A key takeaway is that every homogeneous system has at least one solution, even if it might be trivial. The lecture concludes with the exploration of 'parametric vector forms', which aid in expressing the solution set of a consistent system in vector form. This document discusses linear independence and linear transformations. Linear independence occurs when a vector equation has a trivial solution, meaning Matrix A has a pivot in every column and there are no free variables. Conversely, linear dependence has at least one free variable and not all weights are zero. Sets where one vector is a multiple of another are linearly dependent. In linear transformations, the matrix transformation assigns a vector in Rn to a vector T(x) in Rm and preserves vector addition and scalar multiplication operation. Special geometric transformations of R2 include reflections, rotations, and expansions. Furthermore, T: Rn -> Rm is onto Rm if each b in Rm is the image of at least one x in Rn, and one-to-one if each b in Rm is the image of at most one x in Rn. This PDF gives a comprehensive overview of various concepts in linear algebra. Contraction, expansion, shearing, rotation, projections, one-to-one & onto linear transformations are briefly discussed. Standard matrices are said to have a pivot in every row when they're onto and every column when one-to-one. Also, it describes matrix algebra, covering topics like matrix addition, multiplication, properties of matrix multiplication, transposition of a matrix and properties of resulting matrix. Then, the focus shifts to 'commuting' matrices (when AB=BA) and the caution to be exercised regarding multiplication order and zero matrices. Furthermore, it dives into matrix powers, and theorem related to the uniqueness of RREF. The 'Existence and Uniqueness Theorem' elucidates the conditions for a linear system to be consistent. Also, the logical equivalence of specific statements related to an m x n matrix is discussed. Lastly, there's a brief mention of the properties of the matrix-vector product Ax. This document covers essential theorems in the study of linear algebra. It discusses matrix-vector product properties, parametric vector form of a nonhomogeneous system, and characterizes linearly dependent sets indicating that a set is linearly dependent if a vector is a combination of others. The text also highlights conditions for linear dependence based on matrix size and presence of zero vectors. If a set has more vectors than entries in each vector or contains the zero vector, it is deemed linearly dependent. It also introduces the concept of using the standard matrix to find columns of A in defining linear transformations. Furthermore, the document explains one-to-one checking using the homogeneous equation - a transformation is one-to-one only if it equates to zero has the trivial solution. Lastly, it outlines conditions for 'onto' and 'one-to-one' using a standard matrix for T - T maps from Rn to Rm are onto if columns of A span Rm and one-to-one if columns of A are linearly independent."

    text_chunks = chunk_text(script)
    audios = []
    for idx, chunk in enumerate(text_chunks):
        audio_content = synthesize_speech(chunk, idx)
        audios.append(audio_content)

    db = client['audio']
    collection = db['files']

    combined = combine_audios(audios, "outputs/combined_audio.mp3")
    document_id = upload_audio(combined, "this is a test name", collection)

    return str(document_id)

@app.route('/api/get_audio_id', methods=['POST'])
def get_audio_id():
    if request.method == 'POST':
        file_id = request.get_json()["file_id"]
        duration = int (request.get_json()["duration"])

        file_db = client['input_files']
        file_collection = file_db['files']
        document = file_collection.find_one({'_id': ObjectId(file_id)})

        if document is None:
            return "File not found in the database."
        
        file_data = document.get('file_data')
        file_type = document.get('file_type')

        if file_type == "pdf":
            data = pdf_to_txt(file_data)
        elif file_type == "latex":
            data = pdf_to_txt(file_data)
        elif file_type == "docx":
            data = docx_to_txt(file_data)
        elif file_type == "jpg":
            data = jpg_to_txt(file_data)
        elif file_type == "written_jpg":
            data = written_jpg_to_txt(file_data)
        
        script = create_script(duration, data)

        split_script = script.split(" ");
        res_arr = []
        res_arr_idx = -1
        for i in range(len(split_script)):
            if i % 100 == 0:
                res_arr_idx += 1
                res_arr.append("")

            res_arr[res_arr_idx] = res_arr[res_arr_idx] + " " + split_script[i]
        
        text_chunks = chunk_text(script)

        audios = []
        for idx, chunk in enumerate(text_chunks):
            audio_content = synthesize_speech(chunk, idx)
            audios.append(audio_content)

        audio_db = client['audio']
        audio_collection = audio_db['files']

        combined = combine_audios(audios, "outputs/combined_audio.mp3")
        document_id = upload_audio(combined, "audio_file", audio_collection)

        return jsonify({'message': 'Data received', 'document_id': str(document_id), 'text': res_arr})

@app.route('/api/conversion', methods=["POST"])
def conversion():
    with open("files/notes_example.pdf", "rb") as file:
        file_binary = file.read()
        document = {
            "file_name": "notes_example",
            "file_type": "pdf",
            "file_data": file_binary
        }

        file_db = client['input_files']
        file_collection = file_db['files']
        
        # Insert the document into MongoDB collection
        result = file_collection.insert_one(document)
        return str(result.inserted_id)
    # return str(result.inserted_id)

@app.route('/api/file_to_text', methods=["POST"])
def file_to_text():
    file_db = client['input_files']
    file_collection = file_db['files']
    document = file_collection.find_one({'_id': ObjectId("66f8541ddc30f544eeb40101")})

    if document is None:
        return "File not found in the database."
    
    file_data = document.get('file_data')
    file_type = document.get('file_type')
    return "done"

# Run all create_script methods and return final response
def create_script(maxDuration, text, WPM=160):
    maxWords = maxDuration * WPM
    
    response = convertToScript(text)
    if (len(response) > maxWords):
        response = condense(response, maxWords)
    
    return response

if __name__ == '__main__':
	app.run(debug=True)