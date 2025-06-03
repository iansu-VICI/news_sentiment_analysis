#!/usr/bin/env python3
"""
根據 teach.md 中的方法計算兩篇文章的餘弦相似度
實現步驟：
1. 文字前處理
2. TF-IDF向量化或句向量嵌入
3. 計算餘弦相似度

優化版本（基於fix.md建議）：
- 移除不必要的punkt檢查，避免多餘的nltk.download()
- 使用TweetTokenizer改善金融專有名詞的斷詞精確度
- 移除手動實現，只保留高效的sklearn版本
- 支持sentence-transformers進行語義相似度分析
"""

import re
import string
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import TweetTokenizer
import argparse
import os

# 下載必要的NLTK數據（移除punkt檢查，根據fix.md建議）
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("下載stopwords數據...")
    nltk.download('stopwords')

# 嘗試導入sentence-transformers（可選）
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class TextSimilarityAnalyzer:
    def __init__(self, use_semantic=False):
        """
        初始化分析器
        
        Args:
            use_semantic: 是否使用語義相似度（需要sentence-transformers）
        """
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        # 使用TweetTokenizer改善金融專有名詞處理（fix.md建議）
        self.tokenizer = TweetTokenizer(preserve_case=False, reduce_len=True, strip_handles=True)
        
        self.use_semantic = use_semantic
        if use_semantic:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                print("⚠️  sentence-transformers未安裝，回退到TF-IDF方法")
                print("   安裝方法: pip install sentence-transformers")
                self.use_semantic = False
            else:
                print("🔄 載入語義向量模型...")
                # 使用適合金融文本的模型（fix.md建議用sentence-transformers）
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ 語義向量模型載入完成")
        
    def read_article(self, file_path):
        """讀取文章文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"讀取文件 {file_path} 時出錯: {e}")
            return None
    
    def extract_main_content(self, raw_content):
        """從原始內容中提取主要文章內容"""
        lines = raw_content.split('\n')
        
        # 找到分隔線的位置
        separator_line = -1
        for i, line in enumerate(lines):
            if line.strip() == '--------------------------------------------------------------------------------':
                separator_line = i
                break
        
        if separator_line == -1:
            # 如果沒找到分隔線，返回全部內容
            main_content = raw_content
        else:
            # 提取分隔線後的內容作為主要文章內容
            main_content = '\n'.join(lines[separator_line + 1:])
        
        return main_content
    
    def preprocess_text(self, text, for_semantic=False):
        """
        步驟1: 文字前處理
        
        Args:
            text: 原始文本
            for_semantic: 是否為語義分析準備（保留更多原始結構）
        """
        # 提取主要內容
        text = self.extract_main_content(text)
        
        # 去除HTML標記
        text = re.sub(r'<[^>]+>', '', text)
        
        # 去除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 去除email
        text = re.sub(r'\S+@\S+', '', text)
        
        if for_semantic:
            # 語義分析：保留更多原始結構，只做基本清理
            text = re.sub(r'[^\w\s]', ' ', text)  # 保留字母數字和空格
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        # TF-IDF分析：進行完整的前處理
        text = text.lower()
        
        # 去除數字和特殊字符，只保留字母和空格
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # 去除多餘空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 使用TweetTokenizer分詞（fix.md建議：改善金融專有名詞處理，避免word_tokenize切錯）
        tokens = self.tokenizer.tokenize(text)
        
        # 去除停用詞和短詞
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        # 詞幹還原
        tokens = [self.stemmer.stem(token) for token in tokens]
        
        # 返回處理後的文本
        return ' '.join(tokens)
    
    def analyze_similarity_tfidf(self, processed1, processed2):
        """使用TF-IDF方法計算相似度（fix.md建議：只保留sklearn版本，移除手動實現）"""
        documents = [processed1, processed2]
        
        # 使用scikit-learn的TF-IDF（高效實現，避免O(V×N×L)記憶體問題）
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        
        print(f"詞彙表大小: {len(feature_names)} 個詞")
        print(f"TF-IDF矩陣形狀: {tfidf_matrix.shape}")
        
        # 計算餘弦相似度
        similarity_matrix = cosine_similarity(tfidf_matrix)
        cosine_sim = similarity_matrix[0][1]
        
        return cosine_sim, "TF-IDF"
    
    def analyze_similarity_semantic(self, text1, text2):
        """使用語義向量方法計算相似度（fix.md建議：抓到語義近似，克服TF-IDF對語序語義失敏）"""
        # 生成句向量（sentence-transformers提供語義理解能力）
        embeddings = self.semantic_model.encode([text1, text2])
        
        print(f"語義向量維度: {embeddings.shape[1]}")
        print(f"向量矩陣形狀: {embeddings.shape}")
        
        # 計算餘弦相似度（語義層面的相似度）
        similarity_matrix = cosine_similarity(embeddings)
        cosine_sim = similarity_matrix[0][1]
        
        return cosine_sim, "語義向量"
    
    def analyze_similarity(self, file1, file2):
        """分析兩篇文章的相似度"""
        print("=== 餘弦相似度分析（優化版）===")
        print(f"文章1: {os.path.basename(file1)}")
        print(f"文章2: {os.path.basename(file2)}")
        
        method = "語義向量" if self.use_semantic else "TF-IDF"
        print(f"分析方法: {method}")
        print()
        
        # 讀取文章
        content1 = self.read_article(file1)
        content2 = self.read_article(file2)
        
        if not content1 or not content2:
            print("❌ 無法讀取文章內容")
            return
        
        print("步驟1: 文字前處理...")
        
        if self.use_semantic:
            # 語義分析：保留更多結構
            processed1 = self.preprocess_text(content1, for_semantic=True)
            processed2 = self.preprocess_text(content2, for_semantic=True)
            
            print(f"文章1前處理後長度: {len(processed1.split())} 個詞")
            print(f"文章2前處理後長度: {len(processed2.split())} 個詞")
            print()
            
            print("步驟2: 生成語義向量...")
            cosine_sim, method_used = self.analyze_similarity_semantic(processed1, processed2)
            
        else:
            # TF-IDF分析：完整前處理
            processed1 = self.preprocess_text(content1, for_semantic=False)
            processed2 = self.preprocess_text(content2, for_semantic=False)
            
            print(f"文章1前處理後長度: {len(processed1.split())} 個詞")
            print(f"文章2前處理後長度: {len(processed2.split())} 個詞")
            print()
            
            print("步驟2: TF-IDF向量化...")
            cosine_sim, method_used = self.analyze_similarity_tfidf(processed1, processed2)
        
        print("\n步驟3: 計算餘弦相似度...")
        print()
        print("=== 分析結果 ===")
        print(f"分析方法: {method_used}")
        print(f"餘弦相似度: {cosine_sim:.6f}")
        
        # 相似度解釋
        if cosine_sim >= 0.8:
            interpretation = "非常高相似度 - 可能是重複或高度相似的文章"
        elif cosine_sim >= 0.6:
            interpretation = "高相似度 - 文章內容相關性很高"
        elif cosine_sim >= 0.4:
            interpretation = "中等相似度 - 文章有一定相關性"
        elif cosine_sim >= 0.2:
            interpretation = "低相似度 - 文章相關性較低"
        else:
            interpretation = "很低相似度 - 文章內容基本不相關"
        
        print(f"相似度解釋: {interpretation}")
        
        # 根據論文中的0.8閾值判斷
        print(f"\n根據論文標準 (閾值 = 0.8):")
        if cosine_sim >= 0.8:
            print("🔄 這兩篇文章會被標記為重複並捨棄")
        else:
            print("✅ 這兩篇文章會被保留")
        
        # 方法比較建議
        if not self.use_semantic:
            print(f"\n💡 提示: 如需更準確的語義相似度分析，可安裝 sentence-transformers:")
            print("   pip install sentence-transformers")
            print("   然後使用 --semantic 參數")
        
        return cosine_sim
    
    def show_preprocessing_details(self, file1, file2):
        """顯示前處理的詳細過程"""
        print("=== 前處理詳細過程（優化版）===")
        
        for i, file_path in enumerate([file1, file2], 1):
            print(f"\n文章{i}: {os.path.basename(file_path)}")
            content = self.read_article(file_path)
            if not content:
                continue
            
            # 原始內容
            main_content = self.extract_main_content(content)
            print(f"原始內容長度: {len(main_content)} 字符")
            print(f"原始內容前100字符: {main_content[:100].replace(chr(10), ' ')}")
            
            # TF-IDF前處理
            processed_tfidf = self.preprocess_text(content, for_semantic=False)
            words_tfidf = processed_tfidf.split()
            print(f"TF-IDF前處理後詞數: {len(words_tfidf)} 個詞")
            print(f"TF-IDF前處理後前15個詞: {' '.join(words_tfidf[:15])}")
            
            # 語義分析前處理
            processed_semantic = self.preprocess_text(content, for_semantic=True)
            words_semantic = processed_semantic.split()
            print(f"語義分析前處理後詞數: {len(words_semantic)} 個詞")
            print(f"語義分析前處理後前15個詞: {' '.join(words_semantic[:15])}")

def main():
    parser = argparse.ArgumentParser(description='計算兩篇文章的餘弦相似度（優化版）')
    parser.add_argument('file1', help='第一篇文章的路徑')
    parser.add_argument('file2', help='第二篇文章的路徑')
    parser.add_argument('--semantic', action='store_true', help='使用語義向量而非TF-IDF（需要sentence-transformers）')
    parser.add_argument('--details', action='store_true', help='顯示前處理的詳細過程')
    
    args = parser.parse_args()
    
    # 檢查文件是否存在
    if not os.path.exists(args.file1):
        print(f"❌ 文件不存在: {args.file1}")
        return
    if not os.path.exists(args.file2):
        print(f"❌ 文件不存在: {args.file2}")
        return
    
    analyzer = TextSimilarityAnalyzer(use_semantic=args.semantic)
    
    if args.details:
        analyzer.show_preprocessing_details(args.file1, args.file2)
        print("\n" + "="*50 + "\n")
    
    # 計算相似度
    similarity = analyzer.analyze_similarity(args.file1, args.file2)

if __name__ == "__main__":
    main() 