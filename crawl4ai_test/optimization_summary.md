# 餘弦相似度分析優化摘要

根據 `fix.md` 中的建議，對 `cosine_similarity_analysis.py` 進行了以下優化：

## 優化項目

### 1. 移除不必要的punkt檢查 ✅
**問題**: `punkt_tab` 無此模型，會多跑一次 `nltk.download()`
**解決方案**: 移除 `punkt` 相關的檢查，只保留必要的 `stopwords` 檢查
```python
# 修改前
nltk.data.find('tokenizers/punkt')
nltk.download('punkt')

# 修改後
# 完全移除punkt相關檢查
```

### 2. 改善斷詞精確度 ✅
**問題**: `word_tokenize` 基於規則，易切錯金融專有名詞
**解決方案**: 使用 `TweetTokenizer` 改善金融專有名詞處理
```python
self.tokenizer = TweetTokenizer(preserve_case=False, reduce_len=True, strip_handles=True)
```

### 3. 移除手動實現，提升效能 ✅
**問題**: 手動版為 O(V×N×L)，記憶體和速度問題
**解決方案**: 只保留高效的 sklearn 版本，移除所有手動實現
- 使用 `TfidfVectorizer` 進行高效向量化
- 使用 `cosine_similarity` 進行快速相似度計算

### 4. 增加語義分析能力 ✅
**問題**: TF-IDF 對語序與語義失敏
**解決方案**: 整合 `sentence-transformers` 提供語義相似度分析
```python
# 語義向量模型
self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

# 使用語義向量計算相似度
embeddings = self.semantic_model.encode([text1, text2])
```

## 使用方式

### TF-IDF 分析（預設）
```bash
python cosine_similarity_analysis.py 1.txt 2.txt
```

### 語義向量分析
```bash
python cosine_similarity_analysis.py 1.txt 2.txt --semantic
```

### 詳細前處理過程
```bash
python cosine_similarity_analysis.py 1.txt 2.txt --details
```

## 效能改善

1. **記憶體使用**: 從 O(V×N×L) 降至 sklearn 的優化實現
2. **執行速度**: 移除不必要的下載和手動計算
3. **斷詞精確度**: TweetTokenizer 更適合金融文本
4. **語義理解**: sentence-transformers 提供語義層面的相似度

## 相容性

- 保持與原始 API 相容
- 支援兩種分析模式：TF-IDF 和語義向量
- 自動降級：如果 sentence-transformers 未安裝，自動回退到 TF-IDF
- 詳細錯誤處理和用戶提示 