import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import shutil

# -------------------
# 辅助函数
# -------------------
def word_count(text):
    """计算文本中的单词数"""
    return len(text.split())

def is_text_complete(text):
    """判断文本是否以标点符号结束"""
    return re.search(r'.*["""";.!?]$', text.strip()) is not None

def split_text_into_chunks(text, min_words=1100):
    """
    将文本切割成多个片段，每个片段包含至少 min_words 个单词，并且以标点符号结束。
    :param text: 要切割的完整文本
    :param min_words: 每个片段的最小单词数
    :return: 切割后的文本片段列表
    """
    # 使用正则表达式将文本大致分割成句子
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = word_count(sentence)

        if current_word_count + sentence_word_count < min_words:
            current_chunk += sentence + " "
            current_word_count += sentence_word_count
        else:
            # 如果添加当前句子后达到或超过min_words，则结束当前片段
            current_chunk += sentence
            chunks.append(current_chunk.strip())
            current_chunk = ""
            current_word_count = 0

    # 若最后还有剩余文字（即使没达到 min_words），也作为一个片段
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# -------------------
# 主体GUI类
# -------------------
class TextSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TXT 文本批量切割工具")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # 1) 输入文件夹
        self.input_dir = tk.StringVar()
        self.create_input_dir_selection()

        # 2) 输出文件夹
        self.output_dir = tk.StringVar()
        self.create_output_dir_selection()

        # 3) 最小单词数设置
        self.min_words = tk.IntVar(value=1100)
        self.create_min_words_setting()

        # 4) 执行按钮
        self.create_execute_button()

        # 5) 进度显示(日志)
        self.create_progress_display()

        # 任务完成后出现的“打开输出目录”按钮（初始不显示）
        self.open_output_button = None

    # ---------- 创建UI各部分 ----------
    def create_input_dir_selection(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill='x')

        label = ttk.Label(frame, text="选择输入文件夹:")
        label.pack(side='left')

        # 显示用户选择的输入文件夹
        entry = ttk.Entry(frame, textvariable=self.input_dir, width=50, state='readonly')
        entry.pack(side='left', padx=5)

        # 浏览按钮
        button = ttk.Button(frame, text="浏览", command=self.browse_input_dir)
        button.pack(side='left')

    def browse_input_dir(self):
        """弹出文件夹选择对话框，并将其路径填入self.input_dir"""
        directory = filedialog.askdirectory(title="选择包含TXT文件的文件夹")
        if directory:
            self.input_dir.set(directory)

    def create_output_dir_selection(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill='x')

        label = ttk.Label(frame, text="选择输出目录:")
        label.pack(side='left')

        entry = ttk.Entry(frame, textvariable=self.output_dir, width=50, state='readonly')
        entry.pack(side='left', padx=5)

        button = ttk.Button(frame, text="浏览", command=self.browse_output_dir)
        button.pack(side='left')

    def browse_output_dir(self):
        """弹出文件夹选择对话框，并将其路径填入self.output_dir"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)

    def create_min_words_setting(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill='x')

        label = ttk.Label(frame, text="每个片段的最小单词数:")
        label.pack(side='left')

        entry = ttk.Entry(frame, textvariable=self.min_words, width=10)
        entry.pack(side='left', padx=5)

    def create_execute_button(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill='x')

        button = ttk.Button(frame, text="开始批量切割", command=self.confirm_and_execute)
        button.pack()

    def create_progress_display(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill='both', expand=True)

        self.progress_text = tk.Text(frame, wrap='word', state='disabled', height=12)
        self.progress_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(frame, command=self.progress_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.progress_text['yscrollcommand'] = scrollbar.set

    # ---------- 日志打印 ----------
    def log_message(self, message):
        self.progress_text.configure(state='normal')
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.configure(state='disabled')

    # ---------- 主要业务逻辑 ----------
    def confirm_and_execute(self):
        """
        先确认要处理的文件清单。只有在用户确认后，才开始执行切割操作。
        """
        in_dir = self.input_dir.get()
        out_dir = self.output_dir.get()
        min_words = self.min_words.get()

        if not in_dir:
            messagebox.showerror("错误", "请先选择输入文件夹。")
            return
        if not out_dir:
            messagebox.showerror("错误", "请先选择输出目录。")
            return
        if min_words <= 0:
            messagebox.showerror("错误", "最小单词数必须大于0。")
            return

        # 获取输入文件夹里的所有 TXT 文件
        txt_files = [f for f in os.listdir(in_dir) if f.lower().endswith('.txt')]
        if not txt_files:
            messagebox.showinfo("提示", "在该文件夹中未找到任何TXT文件。")
            return

        # 预览将要处理的文件
        preview_msg = "即将处理以下文件:\n\n" + "\n".join(txt_files)
        confirm = messagebox.askokcancel("确认", preview_msg)
        if confirm:
            # 用户点击“确定”后，执行切割操作
            self.execute_split(txt_files)

    def execute_split(self, txt_files):
        """
        真正执行文件切割逻辑。
        :param txt_files: 列表，包含待处理的文件名（不含路径）
        """
        in_dir = self.input_dir.get()
        out_dir = self.output_dir.get()
        min_words = self.min_words.get()

        self.log_message("开始批量切割...")

        total_files = len(txt_files)
        split_files = 0
        unmodified_files = 0

        self.log_message(f"共找到 {total_files} 个TXT文件。")

        for file_name in txt_files:
            input_path = os.path.join(in_dir, file_name)

            # 读取文本内容
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                self.log_message(f"错误: 无法读取文件 {file_name}:\n{e}")
                continue

            current_word_count = word_count(text)
            if current_word_count < min_words:
                # 文字不足，直接复制到输出目录
                try:
                    shutil.copy(input_path, os.path.join(out_dir, file_name))
                    self.log_message(f"未切割（文字不足）: {file_name} 已复制到输出目录。")
                    unmodified_files += 1
                except Exception as e:
                    self.log_message(f"错误: 无法复制文件 {file_name}:\n{e}")
                continue

            # 文字足够，进行切割
            chunks = split_text_into_chunks(text, min_words=min_words)
            num_chunks = len(chunks)
            self.log_message(f"切割文件: {file_name} 成 {num_chunks} 个片段。")

            # 提取原文件名（不含扩展名）作为切割后文件名的前缀
            base_name = os.path.splitext(file_name)[0]

            for idx, chunk in enumerate(chunks, 1):
                output_file = os.path.join(out_dir, f"{base_name}_part{idx}.txt")
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(chunk)
                    self.log_message(f"已生成: {output_file}")
                except Exception as e:
                    self.log_message(f"错误: 无法写入文件 {output_file}:\n{e}")

            split_files += 1

        self.log_message(
            f"批量切割完成！共处理了 {total_files} 个文件，其中 {split_files} 个文件已切割，"
            f"{unmodified_files} 个文件保持不变。"
        )

        # 在任务完成后，显示“打开输出目录”按钮
        if not self.open_output_button:
            self.open_output_button = ttk.Button(self.root, text="打开输出目录", command=self.open_output_folder)
            self.open_output_button.pack(pady=5)

    def open_output_folder(self):
        """用系统默认文件管理器打开输出目录"""
        folder = self.output_dir.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "输出目录无效或不存在。")
            return

        if os.name == 'nt':
            # Windows
            os.startfile(folder)
        else:
            # macOS 或 Linux
            import subprocess
            try:
                subprocess.Popen(["open", folder])  # macOS
            except FileNotFoundError:
                subprocess.Popen(["xdg-open", folder])  # Linux

# -------------------
# main
# -------------------
def main():
    root = tk.Tk()
    app = TextSplitterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
