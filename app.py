import os
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import markdown
from docx import Document
from io import BytesIO
import zipfile
from splitter import split_text_into_chunks, word_count

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'md', 'docx'}

def read_docx(file):
    doc = Document(file)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

def read_markdown(file):
    content = file.read().decode('utf-8')
    # 直接返回原始的Markdown内容，不转换为纯文本
    return content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    min_words = int(request.form.get('min_words', 1100))
    
    try:
        # 根据文件类型读取内容
        if file.filename.endswith('.docx'):
            text = read_docx(file)
        elif file.filename.endswith('.md'):
            text = read_markdown(file)
        else:  # .txt文件
            text = file.read().decode('utf-8')
        
        # 检查文本长度
        if word_count(text) < min_words:
            return jsonify({
                'message': '文件内容太短，无需切割',
                'original_text': text
            })
        
        # 切割文本
        chunks = split_text_into_chunks(text, min_words=min_words)
        
        # 创建ZIP文件
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, chunk in enumerate(chunks, 1):
                filename = f'part{i}.txt'
                zf.writestr(filename, chunk)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'split_result.zip'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))