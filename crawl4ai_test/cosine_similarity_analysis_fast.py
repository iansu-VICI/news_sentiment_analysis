#!/usr/bin/env python3
"""
快速餘弦相似度分析程式（優化版）
使用預處理好的向量資料庫進行快速相似度計算

功能：
1. 使用預處理好的向量資料庫進行快速查詢
2. 支援即時文檔分析（不使用資料庫）
3. 批次相似度計算
4. 向量資料庫管理

使用方式：
# 使用向量資料庫查詢
python cosine_similarity_analysis_fast.py --vector-db vector_cache/ --query 1.txt --method both

# 即時分析兩篇文章
python cosine_similarity_analysis_fast.py --file1 1.txt --file2 2.txt --method tfidf

# 批次分析
python cosine_similarity_analysis_fast.py --batch-analysis --input-dir articles/ --vector-db vector_cache/
"""

import os
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 導入我們的預處理模組
from preprocessing import DocumentVectorizer

class FastSimilarityAnalyzer:
    """快速相似度分析器"""
    
    def __init__(self, vector_db_path: Optional[str] = None, use_semantic: bool = True):
        """
        初始化快速分析器
        
        Args:
            vector_db_path: 向量資料庫路徑
            use_semantic: 是否啟用語義分析
        """
        self.vector_db_path = vector_db_path
        self.vectorizer = None
        self.use_semantic = use_semantic
        
        if vector_db_path:
            print(f"🔄 載入向量資料庫: {vector_db_path}")
            start_time = time.time()
            self.vectorizer = DocumentVectorizer(cache_dir=vector_db_path, use_semantic=use_semantic)
            load_time = time.time() - start_time
            print(f"✅ 向量資料庫載入完成 ({load_time:.2f}秒)")
            
            # 顯示資料庫統計
            stats = self.vectorizer.get_statistics()
            self._print_db_stats(stats)
        else:
            # 即時模式，每次都初始化
            print("⚠️  即時分析模式（較慢）")
    
    def _print_db_stats(self, stats: Dict):
        """打印資料庫統計資訊"""
        print(f"\n📊 向量資料庫統計:")
        print(f"   文檔總數: {stats['documents']['total']}")
        print(f"   已處理文檔: {stats['documents']['processed']}")
        
        if stats['tfidf']['available']:
            print(f"   ✅ TF-IDF資料庫: {stats['tfidf']['documents']} 文檔, {stats['tfidf']['vocab_size']} 詞彙")
        else:
            print(f"   ❌ TF-IDF資料庫: 未建立")
            
        if stats['semantic']['available']:
            print(f"   ✅ 語義向量資料庫: {stats['semantic']['documents']} 文檔, {stats['semantic']['vector_dim']} 維度")
        else:
            print(f"   ❌ 語義向量資料庫: 未建立")
    
    def analyze_similarity_fast(self, file1: str, file2: str, method: str = 'both') -> Dict:
        """
        快速計算兩個文檔的相似度（使用資料庫）
        
        Args:
            file1: 第一個文檔路徑
            file2: 第二個文檔路徑
            method: 'tfidf', 'semantic', 或 'both'
            
        Returns:
            相似度結果字典
        """
        if not self.vectorizer:
            return {'error': '向量資料庫未載入，請使用 --vector-db 參數指定資料庫路徑'}
        
        print("=== 快速餘弦相似度分析 ===")
        print(f"文檔1: {os.path.basename(file1)}")
        print(f"文檔2: {os.path.basename(file2)}")
        print(f"分析方法: {method}")
        print()
        
        start_time = time.time()
        results = {}
        
        # 確保兩個文檔都在資料庫中
        file1_abs = os.path.abspath(file1)
        file2_abs = os.path.abspath(file2)
        
        # TF-IDF分析
        if method in ['tfidf', 'both'] and self.vectorizer.tfidf_cache:
            tfidf_db = self.vectorizer.tfidf_cache
            
            try:
                # 查找文檔在資料庫中的索引
                idx1 = tfidf_db['file_paths'].index(file1_abs)
                idx2 = tfidf_db['file_paths'].index(file2_abs)
                
                # 獲取向量
                vector1 = tfidf_db['matrix'][idx1]
                vector2 = tfidf_db['matrix'][idx2]
                
                # 計算相似度
                similarity = cosine_similarity(vector1, vector2)[0][0]
                
                results['tfidf'] = {
                    'similarity': float(similarity),
                    'method': 'TF-IDF (快取)',
                    'vocab_size': len(tfidf_db['feature_names'])
                }
                
                print(f"📊 TF-IDF分析:")
                print(f"   詞彙表大小: {len(tfidf_db['feature_names'])}")
                print(f"   相似度: {similarity:.6f}")
                
            except ValueError as e:
                print(f"⚠️  TF-IDF分析失敗: 文檔不在資料庫中")
                # 回退到即時計算
                results['tfidf'] = self._fallback_tfidf_analysis(file1, file2)
        
        # 語義分析
        if method in ['semantic', 'both'] and self.vectorizer.semantic_cache:
            semantic_db = self.vectorizer.semantic_cache
            
            try:
                # 查找文檔在資料庫中的索引
                idx1 = semantic_db['file_paths'].index(file1_abs)
                idx2 = semantic_db['file_paths'].index(file2_abs)
                
                # 獲取向量
                vector1 = semantic_db['embeddings'][idx1:idx1+1]
                vector2 = semantic_db['embeddings'][idx2:idx2+1]
                
                # 計算相似度
                similarity = cosine_similarity(vector1, vector2)[0][0]
                
                results['semantic'] = {
                    'similarity': float(similarity),
                    'method': '語義向量 (快取)',
                    'vector_dim': semantic_db['vector_dim']
                }
                
                print(f"📊 語義向量分析:")
                print(f"   向量維度: {semantic_db['vector_dim']}")
                print(f"   相似度: {similarity:.6f}")
                
            except ValueError as e:
                print(f"⚠️  語義分析失敗: 文檔不在資料庫中")
                # 回退到即時計算
                if self.vectorizer.semantic_model:
                    results['semantic'] = self._fallback_semantic_analysis(file1, file2)
        
        processing_time = time.time() - start_time
        results['processing_time'] = processing_time
        
        print(f"\n⚡ 處理時間: {processing_time:.3f}秒")
        
        # 顯示最終結果
        self._print_similarity_results(results)
        
        return results
    
    def _fallback_tfidf_analysis(self, file1: str, file2: str) -> Dict:
        """回退到即時TF-IDF計算"""
        print("🔄 回退到即時TF-IDF計算...")
        
        # 使用現有的向量化器進行即時計算
        doc1_info = self.vectorizer.process_file(file1)
        doc2_info = self.vectorizer.process_file(file2)
        
        if not doc1_info or not doc2_info:
            return {'error': '無法處理文檔'}
        
        # 使用現有的TF-IDF向量化器或創建新的
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        documents = [doc1_info['tfidf_text'], doc2_info['tfidf_text']]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        return {
            'similarity': float(similarity),
            'method': 'TF-IDF (即時)',
            'vocab_size': len(vectorizer.get_feature_names_out())
        }
    
    def _fallback_semantic_analysis(self, file1: str, file2: str) -> Dict:
        """回退到即時語義分析"""
        print("🔄 回退到即時語義分析...")
        
        doc1_info = self.vectorizer.process_file(file1)
        doc2_info = self.vectorizer.process_file(file2)
        
        if not doc1_info or not doc2_info:
            return {'error': '無法處理文檔'}
        
        # 使用語義模型
        embeddings = self.vectorizer.semantic_model.encode([
            doc1_info['semantic_text'],
            doc2_info['semantic_text']
        ])
        
        similarity = cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0]
        
        return {
            'similarity': float(similarity),
            'method': '語義向量 (即時)',
            'vector_dim': embeddings.shape[1]
        }
    
    def analyze_similarity_realtime(self, file1: str, file2: str, method: str = 'both') -> Dict:
        """
        即時計算兩個文檔的相似度（不使用資料庫）
        
        Args:
            file1: 第一個文檔路徑
            file2: 第二個文檔路徑
            method: 'tfidf', 'semantic', 或 'both'
            
        Returns:
            相似度結果字典
        """
        print("=== 即時餘弦相似度分析 ===")
        print(f"文檔1: {os.path.basename(file1)}")
        print(f"文檔2: {os.path.basename(file2)}")
        print(f"分析方法: {method}")
        print()
        
        start_time = time.time()
        
        # 初始化向量化器（如果尚未初始化）
        if not self.vectorizer:
            self.vectorizer = DocumentVectorizer(use_semantic=self.use_semantic)
        
        results = {}
        
        # TF-IDF分析
        if method in ['tfidf', 'both']:
            results['tfidf'] = self._fallback_tfidf_analysis(file1, file2)
        
        # 語義分析
        if method in ['semantic', 'both'] and self.vectorizer.semantic_model:
            results['semantic'] = self._fallback_semantic_analysis(file1, file2)
        
        processing_time = time.time() - start_time
        results['processing_time'] = processing_time
        
        print(f"\n⚡ 處理時間: {processing_time:.3f}秒")
        
        # 顯示最終結果
        self._print_similarity_results(results)
        
        return results
    
    def query_similar_documents(self, query_file: str, method: str = 'both', top_k: int = 5) -> Dict:
        """
        查詢與指定文檔相似的其他文檔
        
        Args:
            query_file: 查詢文檔路徑
            method: 分析方法
            top_k: 返回前k個結果
            
        Returns:
            查詢結果字典
        """
        if not self.vectorizer:
            return {'error': '向量資料庫未載入'}
        
        print(f"🔍 查詢與 {os.path.basename(query_file)} 相似的文檔...")
        print(f"方法: {method}, 返回前 {top_k} 個結果")
        print()
        
        start_time = time.time()
        results = self.vectorizer.find_similar_documents(query_file, method, top_k)
        processing_time = time.time() - start_time
        
        print(f"⚡ 查詢時間: {processing_time:.3f}秒")
        
        if 'error' in results:
            print(f"❌ 查詢失敗: {results['error']}")
            return results
        
        # 顯示結果
        for method_name, method_results in results.items():
            print(f"\n📊 {method_name.upper()} 相似度結果:")
            if method_results:
                for result in method_results:
                    file_name = os.path.basename(result['file_path'])
                    print(f"  {result['rank']}. {file_name} (相似度: {result['similarity']:.4f})")
            else:
                print("  無相似文檔")
        
        return results
    
    def batch_analysis(self, input_dir: str, pattern: str = "*.txt", method: str = 'both') -> Dict:
        """
        批次分析目錄中所有文檔的相似度
        
        Args:
            input_dir: 輸入目錄
            pattern: 文件匹配模式
            method: 分析方法
            
        Returns:
            批次分析結果
        """
        if not self.vectorizer:
            return {'error': '向量資料庫未載入'}
        
        print(f"🔄 批次分析: {input_dir}")
        print(f"文件模式: {pattern}")
        print(f"分析方法: {method}")
        print()
        
        input_path = Path(input_dir)
        if not input_path.exists():
            return {'error': f'目錄不存在: {input_dir}'}
        
        file_paths = list(input_path.glob(pattern))
        file_paths = [str(p) for p in file_paths if p.is_file()]
        
        if len(file_paths) < 2:
            return {'error': f'需要至少2個文件進行批次分析'}
        
        print(f"找到 {len(file_paths)} 個文件")
        
        start_time = time.time()
        results = []
        
        # 計算所有文檔對的相似度
        for i, file1 in enumerate(file_paths):
            for j, file2 in enumerate(file_paths[i+1:], i+1):
                similarity_result = self.analyze_similarity_fast(file1, file2, method)
                
                if 'error' not in similarity_result:
                    pair_result = {
                        'file1': os.path.basename(file1),
                        'file2': os.path.basename(file2),
                        'file1_path': file1,
                        'file2_path': file2,
                    }
                    
                    # 添加各種方法的結果
                    for method_name in ['tfidf', 'semantic']:
                        if method_name in similarity_result:
                            pair_result[f'{method_name}_similarity'] = similarity_result[method_name]['similarity']
                    
                    results.append(pair_result)
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ 批次分析完成")
        print(f"   文檔對數: {len(results)}")
        print(f"   總處理時間: {processing_time:.2f}秒")
        print(f"   平均每對: {processing_time/len(results):.3f}秒")
        
        # 找出最相似和最不相似的文檔對
        if results:
            self._print_batch_summary(results, method)
        
        return {
            'results': results,
            'total_pairs': len(results),
            'processing_time': processing_time,
            'avg_time_per_pair': processing_time / len(results) if results else 0
        }
    
    def _print_similarity_results(self, results: Dict):
        """打印相似度結果摘要"""
        print("\n=== 相似度分析結果 ===")
        
        for method_name, result in results.items():
            if method_name == 'processing_time':
                continue
            if 'error' in result:
                print(f"❌ {method_name}: {result['error']}")
                continue
            
            similarity = result['similarity']
            method_desc = result['method']
            
            print(f"📊 {method_desc}: {similarity:.6f}")
            
            # 相似度解釋
            if similarity >= 0.8:
                interpretation = "非常高相似度 - 可能是重複或高度相似的文章"
                emoji = "🔴"
            elif similarity >= 0.6:
                interpretation = "高相似度 - 文章內容相關性很高"
                emoji = "🟠"
            elif similarity >= 0.4:
                interpretation = "中等相似度 - 文章有一定相關性"
                emoji = "🟡"
            elif similarity >= 0.2:
                interpretation = "低相似度 - 文章相關性較低"
                emoji = "🟢"
            else:
                interpretation = "很低相似度 - 文章內容基本不相關"
                emoji = "🔵"
            
            print(f"   {emoji} {interpretation}")
            
            # 根據論文中的0.8閾值判斷
            if similarity >= 0.8:
                print(f"   📋 論文判斷: 這兩篇文章會被標記為重複並捨棄")
            else:
                print(f"   📋 論文判斷: 這兩篇文章會被保留")
    
    def _print_batch_summary(self, results: List[Dict], method: str):
        """打印批次分析摘要"""
        print(f"\n📈 批次分析摘要:")
        
        for method_name in ['tfidf', 'semantic']:
            if method in [method_name, 'both']:
                similarity_key = f'{method_name}_similarity'
                similarities = [r[similarity_key] for r in results if similarity_key in r]
                
                if similarities:
                    max_sim = max(similarities)
                    min_sim = min(similarities)
                    avg_sim = sum(similarities) / len(similarities)
                    
                    print(f"\n{method_name.upper()} 統計:")
                    print(f"   平均相似度: {avg_sim:.4f}")
                    print(f"   最高相似度: {max_sim:.4f}")
                    print(f"   最低相似度: {min_sim:.4f}")
                    
                    # 找出最相似的文檔對
                    max_pair = max(results, key=lambda x: x.get(similarity_key, 0))
                    min_pair = min(results, key=lambda x: x.get(similarity_key, 1))
                    
                    print(f"   最相似文檔對: {max_pair['file1']} ↔ {max_pair['file2']} ({max_sim:.4f})")
                    print(f"   最不相似文檔對: {min_pair['file1']} ↔ {min_pair['file2']} ({min_sim:.4f})")
                    
                    # 高相似度警告
                    high_similarity_pairs = [r for r in results if r.get(similarity_key, 0) >= 0.8]
                    if high_similarity_pairs:
                        print(f"   ⚠️  高相似度警告: {len(high_similarity_pairs)} 對文檔相似度 ≥ 0.8")

def main():
    parser = argparse.ArgumentParser(description='快速餘弦相似度分析程式（優化版）')
    
    # 輸入模式
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file1', type=str, help='第一個文檔路徑（配合--file2使用）')
    input_group.add_argument('--query', type=str, help='查詢文檔路徑（在資料庫中搜尋相似文檔）')
    input_group.add_argument('--batch-analysis', action='store_true', help='批次分析模式')
    
    parser.add_argument('--file2', type=str, help='第二個文檔路徑（配合--file1使用）')
    parser.add_argument('--vector-db', type=str, help='向量資料庫路徑')
    parser.add_argument('--method', type=str, choices=['tfidf', 'semantic', 'both'], default='both',
                      help='分析方法 (預設: both)')
    parser.add_argument('--top-k', type=int, default=5,
                      help='查詢模式下返回前k個結果 (預設: 5)')
    
    # 批次分析參數
    parser.add_argument('--input-dir', type=str, default='.',
                      help='批次分析輸入目錄 (預設: 當前目錄)')
    parser.add_argument('--pattern', type=str, default='*.txt',
                      help='批次分析文件匹配模式 (預設: *.txt)')
    
    args = parser.parse_args()
    
    # 驗證參數
    if args.file1 and not args.file2:
        parser.error("使用 --file1 時必須同時指定 --file2")
    
    if args.batch_analysis and not args.vector_db:
        parser.error("批次分析模式需要指定 --vector-db")
    
    # 初始化分析器
    use_semantic = args.method in ['semantic', 'both']
    analyzer = FastSimilarityAnalyzer(vector_db_path=args.vector_db, use_semantic=use_semantic)
    
    try:
        # 執行相應的分析
        if args.file1 and args.file2:
            # 兩文檔比較模式
            if not os.path.exists(args.file1):
                print(f"❌ 文件不存在: {args.file1}")
                return
            if not os.path.exists(args.file2):
                print(f"❌ 文件不存在: {args.file2}")
                return
            
            if args.vector_db:
                result = analyzer.analyze_similarity_fast(args.file1, args.file2, args.method)
            else:
                result = analyzer.analyze_similarity_realtime(args.file1, args.file2, args.method)
                
        elif args.query:
            # 查詢模式
            if not os.path.exists(args.query):
                print(f"❌ 查詢文件不存在: {args.query}")
                return
            
            result = analyzer.query_similar_documents(args.query, args.method, args.top_k)
            
        elif args.batch_analysis:
            # 批次分析模式
            result = analyzer.batch_analysis(args.input_dir, args.pattern, args.method)
        
        # 處理結果
        if 'error' in result:
            print(f"❌ 分析失敗: {result['error']}")
        else:
            print(f"\n✅ 分析完成")
            
    except KeyboardInterrupt:
        print(f"\n❌ 用戶中斷程式")
    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 