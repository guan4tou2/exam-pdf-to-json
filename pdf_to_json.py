import PyPDF2
import json
import re
import os
import argparse

def clean_text(text):
    """清理文本，處理特殊字符和格式"""
    # 替換全形字符為半形字符
    text = text.replace('（', '(').replace('）', ')')
    # 處理多餘的空格，但保留選項中的空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def merge_lines(text):
    """合併跨行的文本，將題目重新組合"""
    # 移除標題（如果存在）
    text = re.sub(r'^.*?(?=1\s*\([A-D]\)\s*1\.)', '', text, flags=re.DOTALL)
    
    # 使用更嚴格的正則表達式找到所有題目
    pattern = r'\(([A-D])\)\s*(\d+)\.'
    # 找到所有題號的位置
    matches = list(re.finditer(pattern, text))
    
    questions = []
    # 根據題號位置分割文本
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i < len(matches)-1 else len(text)
        question_text = text[start:end].strip()
        questions.append(question_text)
    
    return questions

def extract_options(text):
    """從文本中提取選項，使用改進的正則表達式"""
    options = {}
    
    # 使用更靈活的正則表達式來匹配選項
    pattern = r'\(([A-D])\)((?:(?!\([A-D]\)).)*?)(?=\([A-D]\)|$)'
    matches = list(re.finditer(pattern, text, re.DOTALL))
    
    for match in matches:
        option_letter = match.group(1)
        option_text = match.group(2).strip()
        if option_text:  # 只添加非空的選項
            # 清理選項文本，移除多餘的空格和換行
            option_text = re.sub(r'\s+', ' ', option_text).strip()
            options[option_letter] = option_text
    
    return options

def parse_question(text):
    """解析單個題目的完整文本"""
    # 清理文本
    text = clean_text(text)
    
    # 使用更精確的正則表達式解析題號、答案和題目
    header_pattern = r'^\(([A-D])\)\s*(\d+)\.\s*(.+?)(?=\([A-D]\))'
    header_match = re.match(header_pattern, text)
    
    if not header_match:
        # 嘗試使用更寬鬆的模式匹配
        header_pattern = r'^\(([A-D])\)\s*(\d+)\.(.*?)(?=\([A-D]\))'
        header_match = re.match(header_pattern, text)
        if not header_match:
            num_match = re.match(r'^\(([A-D])\)\s*(\d+)', text)
            if num_match:
                print(f"\n解析失敗的題目 {num_match.group(2)}:")
                print(text)
            return None
    
    answer = header_match.group(1)
    question_id = int(header_match.group(2))
    question_text = header_match.group(3).strip() if len(header_match.groups()) > 2 else ""
    
    # 提取選項
    options = extract_options(text)
    
    # 驗證是否有完整的四個選項
    if len(options) != 4:
        print(f"\n解析失敗的題目 {question_id}:")
        print("原始文本:", text)
        print(f"已找到的選項:", options)
        return None
    
    return {
        "id": question_id,
        "answer": answer,
        "question_text": question_text,
        "options": dict(sorted(options.items()))  # 確保選項順序
    }

def extract_questions_from_pdf(pdf_path):
    """從 PDF 文件中提取題目"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"找不到 PDF 文件：{pdf_path}")
    
    questions = []
    failed_questions = []
    processed_ids = set()
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # 收集所有頁面的文本
        all_text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            print(f"正在處理第 {page_num} 頁...")
            text = page.extract_text()
            # 保留換行符，以便後續處理
            all_text += text
        
        # 預處理文本，處理跨頁問題
        all_text = re.sub(r'-\n', '', all_text)  # 處理連字符
        all_text = re.sub(r'(?<=[^.])\n(?=[^(])', ' ', all_text)  # 合併跨行文本
        
        # 合併跨行的題目
        question_texts = merge_lines(all_text)
        
        # 解析每個題目
        for text in question_texts:
            question_data = parse_question(text)
            if question_data:
                question_id = question_data['id']
                if question_id not in processed_ids:
                    questions.append(question_data)
                    processed_ids.add(question_id)
                    print(f"成功解析題目 {question_id}")
            else:
                num_match = re.match(r'^(\d+)', text)
                if num_match:
                    failed_id = int(num_match.group(1))
                    if failed_id not in processed_ids:
                        failed_questions.append(failed_id)
    
    if not questions:
        print("警告：未找到任何題目，請確認 PDF 格式是否正確")
    else:
        print(f"\n共找到 {len(questions)} 個題目")
        if failed_questions:
            print(f"解析失敗的題號：{sorted(list(set(failed_questions)))}")
    
    # 按題號排序
    questions.sort(key=lambda x: x['id'])
    return {"questions": questions}

def save_to_json(data, output_path):
    """保存結果到 JSON 文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"成功保存到：{output_path}")
    except Exception as e:
        raise Exception(f"保存 JSON 文件時發生錯誤：{str(e)}")

def validate_questions(questions_data):
    """驗證所有題目的完整性"""
    has_issues = False
    
    # 檢查題號連續性
    question_ids = [q['id'] for q in questions_data['questions']]
    if question_ids:
        expected_ids = set(range(min(question_ids), max(question_ids) + 1))
        missing_ids = expected_ids - set(question_ids)
        if missing_ids:
            print(f"\n警告：缺少的題號：{sorted(missing_ids)}")
            has_issues = True
        
        # 檢查題號是否有重複
        duplicate_ids = [id for id in question_ids if question_ids.count(id) > 1]
        if duplicate_ids:
            print(f"\n警告：重複的題號：{sorted(set(duplicate_ids))}")
            has_issues = True
    
    for question in questions_data["questions"]:
        issues = []
        
        # 檢查題目內容
        if not question['question_text']:
            issues.append("題目內容為空")
        
        # 檢查選項
        options = question['options']
        if len(options) != 4:
            issues.append(f"選項數量不正確（找到 {len(options)} 個，應該有 4 個）")
            if options:
                issues.append(f"已找到的選項：{', '.join(sorted(options.keys()))}")
        
        # 檢查每個選項的內容
        for option in ['A', 'B', 'C', 'D']:
            if option not in options:
                issues.append(f"缺少選項 {option}")
            elif not options[option].strip():
                issues.append(f"選項 {option} 的內容為空")
        
        if issues:
            has_issues = True
            print(f"\n題目 {question['id']} 存在以下問題：")
            for issue in issues:
                print(f"- {issue}")
    
    return not has_issues

def main():
    """主程序"""
    # 設置命令列參數解析
    parser = argparse.ArgumentParser(description='將 PDF 試題轉換為 JSON 格式')
    parser.add_argument('pdf_file', help='輸入的 PDF 檔案路徑')
    args = parser.parse_args()

    # 檢查輸入檔案是否存在
    if not os.path.exists(args.pdf_file):
        print(f"錯誤：找不到檔案 {args.pdf_file}")
        return

    # 生成輸出檔案名稱（保持原始檔名，只改副檔名為 .json）
    output_path = os.path.splitext(args.pdf_file)[0] + '.json'
    
    try:
        print(f"開始處理 PDF 文件：{args.pdf_file}")
        questions_data = extract_questions_from_pdf(args.pdf_file)
        
        if validate_questions(questions_data):
            print("\n所有題目驗證通過！")
            save_to_json(questions_data, output_path)
            print("處理完成！")
        else:
            print("\n警告：部分題目可能需要手動檢查和修正")
            save_choice = input("是否仍要保存結果？(y/n): ")
            if save_choice.lower() == 'y':
                save_to_json(questions_data, output_path)
                print("已保存結果。")
            else:
                print("已取消保存。")
    
    except Exception as e:
        print(f"錯誤：{str(e)}")

if __name__ == "__main__":
    main() 