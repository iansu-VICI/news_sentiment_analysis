#!/usr/bin/env python3
"""
文本預處理和向量資料庫建立程式
功能：
1. 批次處理多個文件的主要內容提取
2. 建立TF-IDF和語義向量資料庫
3. 支援增量更新和快取
4. 提供快速相似度查詢接口

使用方式：
python preprocessing.py --input-dir articles/ --output-dir vectors/ --method both
"""

import os
import re
import json
import pickle
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import time

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import TweetTokenizer

# 嘗試導入sentence-transformers（可選）
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# 下載必要的NLTK數據
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("下載stopwords數據...")
    nltk.download('stopwords')

class DocumentVectorizer:
    """文檔向量化處理器"""
    
    def __init__(self, cache_dir="vector_cache", use_semantic=True):
        """
        初始化向量化處理器
        
        Args:
            cache_dir: 快取目錄
            use_semantic: 是否使用語義向量（需要sentence-transformers）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 初始化NLP工具
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.tokenizer = TweetTokenizer(preserve_case=False, reduce_len=True, strip_handles=True)
        
        # 初始化向量化器
        self.tfidf_vectorizer = None
        self.semantic_model = None
        self.use_semantic = use_semantic
        
        # 快取
        self.document_cache = {}
        self.tfidf_cache = {}
        self.semantic_cache = {}
        
        # 載入語義模型（如果需要）
        if use_semantic and SENTENCE_TRANSFORMERS_AVAILABLE:
            print("🔄 載入語義向量模型...")
            start_time = time.time()
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            load_time = time.time() - start_time
            print(f"✅ 語義向量模型載入完成 ({load_time:.2f}秒)")
        elif use_semantic:
            print("⚠️  sentence-transformers未安裝，只使用TF-IDF方法")
            print("   安裝方法: pip install sentence-transformers")
            self.use_semantic = False
        
        # 載入現有快取
        self._load_cache()
    
    def _get_file_hash(self, file_path: str) -> str:
        """計算文件的MD5雜湊值用於快取"""
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    
    def _load_cache(self):
        """載入現有快取"""
        cache_files = {
            'documents': self.cache_dir / 'documents.json',
            'tfidf': self.cache_dir / 'tfidf_vectors.pkl',
            'semantic': self.cache_dir / 'semantic_vectors.pkl'
        }
        
        for cache_type, cache_file in cache_files.items():
            if cache_file.exists():
                try:
                    if cache_type == 'documents':
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            self.document_cache = json.load(f)
                    else:
                        with open(cache_file, 'rb') as f:
                            if cache_type == 'tfidf':
                                self.tfidf_cache = pickle.load(f)
                            else:
                                self.semantic_cache = pickle.load(f)
                    print(f"✅ 載入 {cache_type} 快取: {len(getattr(self, f'{cache_type}_cache'))} 項目")
                except Exception as e:
                    print(f"⚠️  載入 {cache_type} 快取失敗: {e}")
    
    def _save_cache(self):
        """保存快取"""
        cache_files = {
            'documents': (self.cache_dir / 'documents.json', self.document_cache),
            'tfidf': (self.cache_dir / 'tfidf_vectors.pkl', self.tfidf_cache),
            'semantic': (self.cache_dir / 'semantic_vectors.pkl', self.semantic_cache)
        }
        
        for cache_type, (cache_file, cache_data) in cache_files.items():
            if cache_data:  # 只有當快取有資料時才保存
                try:
                    if cache_type == 'documents':
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    else:
                        with open(cache_file, 'wb') as f:
                            pickle.dump(cache_data, f)
                    print(f"✅ 保存 {cache_type} 快取: {len(cache_data)} 項目")
                except Exception as e:
                    print(f"❌ 保存 {cache_type} 快取失敗: {e}")
    
    def extract_main_content(self, raw_content: str) -> str:
        """從原始內容中提取主要文章內容（優化版）"""
        # 快速檢查分隔線
        separator = '--------------------------------------------------------------------------------'
        separator_index = raw_content.find(separator)
        
        if separator_index != -1:
            # 找到分隔線，提取後面的內容
            main_content = raw_content[separator_index + len(separator):].strip()
        else:
            # 沒有分隔線，返回全部內容
            main_content = raw_content
        
        return main_content
    
    def preprocess_text(self, text: str, for_semantic: bool = False) -> str:
        """
        文字前處理（優化版）
        
        Args:
            text: 原始文本
            for_semantic: 是否為語義分析準備
        """
        # 提取主要內容
        text = self.extract_main_content(text)
        
        # 基本清理（使用編譯的正則表達式會更快）
        if not hasattr(self, '_compiled_regexes'):
            self._compiled_regexes = {
                'html': re.compile(r'<[^>]+>'),
                'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
                'email': re.compile(r'\S+@\S+'),
                'non_word': re.compile(r'[^\w\s]'),
                'non_alpha': re.compile(r'[^a-zA-Z\s]'),
                'whitespace': re.compile(r'\s+')
            }
        
        # 去除HTML、URL、email
        text = self._compiled_regexes['html'].sub('', text)
        text = self._compiled_regexes['url'].sub('', text)
        text = self._compiled_regexes['email'].sub('', text)
        
        if for_semantic:
            # 語義分析：保留更多原始結構
            text = self._compiled_regexes['non_word'].sub(' ', text)
            text = self._compiled_regexes['whitespace'].sub(' ', text).strip()
            return text
        
        # TF-IDF分析：完整前處理
        text = text.lower()
        text = self._compiled_regexes['non_alpha'].sub(' ', text)
        text = self._compiled_regexes['whitespace'].sub(' ', text).strip()
        
        # 分詞和過濾（向量化處理）
        tokens = self.tokenizer.tokenize(text)
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        # 詞幹還原（批次處理更有效率）
        if tokens:  # 只有當有token時才進行詞幹還原
            tokens = [self.stemmer.stem(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def process_file(self, file_path: str, force_update: bool = False) -> Optional[Dict]:
        """
        處理單個文件
        
        Args:
            file_path: 文件路徑
            force_update: 是否強制更新（忽略快取）
            
        Returns:
            文檔處理結果字典
        """
        file_path = str(file_path)
        file_hash = self._get_file_hash(file_path)
        
        # 檢查快取
        if not force_update and file_path in self.document_cache:
            cached_info = self.document_cache[file_path]
            if cached_info.get('file_hash') == file_hash:
                return cached_info
        
        # 讀取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            print(f"❌ 讀取文件失敗 {file_path}: {e}")
            return None
        
        # 處理文本
        main_content = self.extract_main_content(raw_content)
        tfidf_text = self.preprocess_text(raw_content, for_semantic=False)
        semantic_text = self.preprocess_text(raw_content, for_semantic=True) if self.use_semantic else None
        
        # 建立文檔資訊
        doc_info = {
            'file_path': file_path,
            'file_hash': file_hash,
            'file_size': len(raw_content),
            'main_content_length': len(main_content),
            'tfidf_text': tfidf_text,
            'tfidf_word_count': len(tfidf_text.split()) if tfidf_text else 0,
            'semantic_text': semantic_text,
            'semantic_word_count': len(semantic_text.split()) if semantic_text else 0,
            'processed_time': datetime.now().isoformat()
        }
        
        # 更新快取
        self.document_cache[file_path] = doc_info
        
        return doc_info
    
    def build_tfidf_vectors(self, file_paths: List[str], force_update: bool = False) -> Dict:
        """
        建立TF-IDF向量資料庫
        
        Args:
            file_paths: 文件路徑列表
            force_update: 是否強制更新
            
        Returns:
            TF-IDF資料庫字典
        """
        print("🔄 建立TF-IDF向量資料庫...")
        start_time = time.time()
        
        # 處理所有文檔
        documents = []
        valid_paths = []
        
        for file_path in file_paths:
            doc_info = self.process_file(file_path, force_update)
            if doc_info and doc_info['tfidf_text']:
                documents.append(doc_info['tfidf_text'])
                valid_paths.append(file_path)
        
        if not documents:
            print("❌ 沒有有效的文檔可以處理")
            return {}
        
        # 建立TF-IDF向量
        print(f"   處理 {len(documents)} 個文檔...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,  # 限制特徵數量以提升性能
            min_df=2,  # 忽略出現次數太少的詞
            max_df=0.95,  # 忽略出現次數太多的詞
            ngram_range=(1, 2)  # 考慮1-gram和2-gram
        )
        
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        # 建立向量資料庫
        tfidf_db = {
            'vectorizer': self.tfidf_vectorizer,
            'matrix': tfidf_matrix,
            'feature_names': feature_names,
            'file_paths': valid_paths,
            'vocab_size': len(feature_names),
            'created_time': datetime.now().isoformat()
        }
        
        # 更新快取
        self.tfidf_cache = tfidf_db
        
        processing_time = time.time() - start_time
        print(f"✅ TF-IDF向量資料庫建立完成")
        print(f"   文檔數量: {len(valid_paths)}")
        print(f"   詞彙表大小: {len(feature_names)}")
        print(f"   矩陣形狀: {tfidf_matrix.shape}")
        print(f"   處理時間: {processing_time:.2f}秒")
        
        return tfidf_db
    
    def build_semantic_vectors(self, file_paths: List[str], force_update: bool = False) -> Dict:
        """
        建立語義向量資料庫
        
        Args:
            file_paths: 文件路徑列表
            force_update: 是否強制更新
            
        Returns:
            語義向量資料庫字典
        """
        if not self.use_semantic or not self.semantic_model:
            print("⚠️  語義向量功能未啟用")
            return {}
        
        print("🔄 建立語義向量資料庫...")
        start_time = time.time()
        
        # 處理所有文檔
        documents = []
        valid_paths = []
        
        for file_path in file_paths:
            doc_info = self.process_file(file_path, force_update)
            if doc_info and doc_info['semantic_text']:
                documents.append(doc_info['semantic_text'])
                valid_paths.append(file_path)
        
        if not documents:
            print("❌ 沒有有效的文檔可以處理")
            return {}
        
        # 建立語義向量（批次處理提升效率）
        print(f"   處理 {len(documents)} 個文檔...")
        batch_size = 32  # 批次大小，避免記憶體不足
        all_embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_embeddings = self.semantic_model.encode(
                batch_docs,
                show_progress_bar=False,
                batch_size=batch_size
            )
            all_embeddings.append(batch_embeddings)
        
        # 合併所有批次
        embeddings = np.vstack(all_embeddings)
        
        # 建立向量資料庫
        semantic_db = {
            'model_name': 'all-MiniLM-L6-v2',
            'embeddings': embeddings,
            'file_paths': valid_paths,
            'vector_dim': embeddings.shape[1],
            'created_time': datetime.now().isoformat()
        }
        
        # 更新快取
        self.semantic_cache = semantic_db
        
        processing_time = time.time() - start_time
        print(f"✅ 語義向量資料庫建立完成")
        print(f"   文檔數量: {len(valid_paths)}")
        print(f"   向量維度: {embeddings.shape[1]}")
        print(f"   矩陣形狀: {embeddings.shape}")
        print(f"   處理時間: {processing_time:.2f}秒")
        
        return semantic_db
    
    def find_similar_documents(self, query_file: str, method: str = 'both', top_k: int = 5) -> Dict:
        """
        查找相似文檔
        
        Args:
            query_file: 查詢文件路徑
            method: 'tfidf', 'semantic', 或 'both'
            top_k: 返回前k個最相似的文檔
            
        Returns:
            相似度結果字典
        """
        results = {}
        
        # 處理查詢文檔
        query_doc = self.process_file(query_file)
        if not query_doc:
            return {'error': f'無法處理查詢文檔: {query_file}'}
        
        # TF-IDF相似度
        if method in ['tfidf', 'both'] and self.tfidf_cache:
            tfidf_db = self.tfidf_cache
            if query_doc['tfidf_text']:
                # 將查詢文檔轉換為向量
                query_vector = tfidf_db['vectorizer'].transform([query_doc['tfidf_text']])
                
                # 計算相似度
                similarities = cosine_similarity(query_vector, tfidf_db['matrix']).flatten()
                
                # 獲取前k個最相似的文檔
                top_indices = similarities.argsort()[-top_k-1:-1][::-1]  # 排除自己
                
                tfidf_results = []
                for idx in top_indices:
                    if similarities[idx] > 0:  # 只包含有相似度的文檔
                        tfidf_results.append({
                            'file_path': tfidf_db['file_paths'][idx],
                            'similarity': float(similarities[idx]),
                            'rank': len(tfidf_results) + 1
                        })
                
                results['tfidf'] = tfidf_results
        
        # 語義相似度
        if method in ['semantic', 'both'] and self.semantic_cache and self.semantic_model:
            semantic_db = self.semantic_cache
            if query_doc['semantic_text']:
                # 將查詢文檔轉換為向量
                query_embedding = self.semantic_model.encode([query_doc['semantic_text']])
                
                # 計算相似度
                similarities = cosine_similarity(query_embedding, semantic_db['embeddings']).flatten()
                
                # 獲取前k個最相似的文檔
                top_indices = similarities.argsort()[-top_k-1:-1][::-1]  # 排除自己
                
                semantic_results = []
                for idx in top_indices:
                    if similarities[idx] > 0:  # 只包含有相似度的文檔
                        semantic_results.append({
                            'file_path': semantic_db['file_paths'][idx],
                            'similarity': float(similarities[idx]),
                            'rank': len(semantic_results) + 1
                        })
                
                results['semantic'] = semantic_results
        
        return results
    
    def get_statistics(self) -> Dict:
        """獲取資料庫統計資訊"""
        stats = {
            'documents': {
                'total': len(self.document_cache),
                'processed': len([d for d in self.document_cache.values() if d.get('tfidf_text')])
            },
            'tfidf': {
                'available': bool(self.tfidf_cache),
                'documents': len(self.tfidf_cache.get('file_paths', [])),
                'vocab_size': self.tfidf_cache.get('vocab_size', 0)
            },
            'semantic': {
                'available': bool(self.semantic_cache),
                'documents': len(self.semantic_cache.get('file_paths', [])),
                'vector_dim': self.semantic_cache.get('vector_dim', 0)
            }
        }
        return stats
    
    def cleanup_cache(self):
        """清理快取（保存到磁碟）"""
        self._save_cache()
        print("✅ 快取已保存到磁碟")

def main():
    parser = argparse.ArgumentParser(description='文本預處理和向量資料庫建立程式')
    parser.add_argument('--input-dir', type=str, required=True,
                      help='輸入文件目錄')
    parser.add_argument('--output-dir', type=str, default='vector_cache',
                      help='輸出向量快取目錄 (預設: vector_cache)')
    parser.add_argument('--method', type=str, choices=['tfidf', 'semantic', 'both'], default='both',
                      help='向量化方法 (預設: both)')
    parser.add_argument('--pattern', type=str, default='*.txt',
                      help='文件匹配模式 (預設: *.txt)')
    parser.add_argument('--force-update', action='store_true',
                      help='強制更新所有快取')
    parser.add_argument('--query', type=str,
                      help='查詢文件路徑（用於相似度搜尋）')
    parser.add_argument('--top-k', type=int, default=5,
                      help='返回前k個最相似文檔 (預設: 5)')
    
    args = parser.parse_args()
    
    # 初始化向量化器
    use_semantic = args.method in ['semantic', 'both']
    vectorizer = DocumentVectorizer(cache_dir=args.output_dir, use_semantic=use_semantic)
    
    # 獲取輸入文件
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"❌ 輸入目錄不存在: {args.input_dir}")
        return
    
    file_paths = list(input_path.glob(args.pattern))
    file_paths = [str(p) for p in file_paths if p.is_file()]
    
    if not file_paths:
        print(f"❌ 在 {args.input_dir} 中找不到匹配 {args.pattern} 的文件")
        return
    
    print(f"找到 {len(file_paths)} 個文件")
    
    # 如果是查詢模式
    if args.query:
        if not Path(args.query).exists():
            print(f"❌ 查詢文件不存在: {args.query}")
            return
        
        print(f"\n🔍 搜尋與 {args.query} 相似的文檔...")
        results = vectorizer.find_similar_documents(args.query, args.method, args.top_k)
        
        if 'error' in results:
            print(f"❌ {results['error']}")
            return
        
        for method_name, method_results in results.items():
            print(f"\n{method_name.upper()} 相似度結果:")
            for result in method_results:
                print(f"  {result['rank']}. {result['file_path']} (相似度: {result['similarity']:.4f})")
    
    else:
        # 建立向量資料庫
        if args.method in ['tfidf', 'both']:
            vectorizer.build_tfidf_vectors(file_paths, args.force_update)
        
        if args.method in ['semantic', 'both']:
            vectorizer.build_semantic_vectors(file_paths, args.force_update)
        
        # 保存快取
        vectorizer.cleanup_cache()
        
        # 顯示統計資訊
        stats = vectorizer.get_statistics()
        print(f"\n📊 資料庫統計:")
        print(f"   文檔總數: {stats['documents']['total']}")
        print(f"   已處理文檔: {stats['documents']['processed']}")
        if stats['tfidf']['available']:
            print(f"   TF-IDF文檔數: {stats['tfidf']['documents']}")
            print(f"   TF-IDF詞彙表: {stats['tfidf']['vocab_size']}")
        if stats['semantic']['available']:
            print(f"   語義向量文檔數: {stats['semantic']['documents']}")
            print(f"   語義向量維度: {stats['semantic']['vector_dim']}")

if __name__ == "__main__":
    main() 