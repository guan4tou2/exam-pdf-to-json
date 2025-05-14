# PDF 題目轉 JSON 工具

這個工具可以將 PDF 格式的試題轉換成結構化的 JSON 格式。

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 使用方法

1. 將您的 PDF 試題文件放在程式同一目錄下
2. 在 `pdf_to_json.py` 中設定您的 PDF 文件名稱和輸出的 JSON 文件名稱
3. 運行程式：
   ```bash
   python pdf_to_json.py
   ```

## 輸出格式

輸出的 JSON 格式如下：
```json
{
    "questions": [
        {
            "id": 1,
            "answer": "",
            "question_text": "題目內容",
            "options": {
                "A": "選項A內容",
                "B": "選項B內容",
                "C": "選項C內容",
                "D": "選項D內容"
            }
        }
    ]
}
```

## 注意事項

- PDF 文件中的題目格式需要符合特定規範（數字編號開頭，後接題目內容，然後是 A/B/C/D 選項）
- 答案欄位預設為空字串，需要手動填寫或從其他來源獲取
- 確保 PDF 文件內容清晰可讀，避免特殊格式或圖片干擾
- 支持中文內容處理 