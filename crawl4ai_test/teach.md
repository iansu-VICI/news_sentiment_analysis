### 1. 文字前處理

* **轉小寫**、去除標點符號、HTML 標記等雜訊。
* **停用詞 (stop-words) 移除**，避免「the、and」之類高頻但無資訊量的字影響距離計算。
* 視需要做 **詞幹還原 (stemming) 或詞形還原 (lemmatization)**，把 “profits” 與 “profit” 視為同一詞根。

### 2. 文章向量化（最常見的是 TF-IDF）

1. 為整批新聞建立詞彙表 $V=\{w_1,\dots,w_{|V|}\}$。
2. 對每篇文章 $d$，計算 **詞頻 (tf)** 與 **逆文檔頻率 (idf)**：

   $$
   \text{tfidf}_{d,w}= \text{tf}_{d,w}\times\log\frac{N}{n_w}
   $$

   其中 $N$ 為所有文件數，$n_w$ 為含詞 $w$ 的文件數。
3. 將文章表示成稀疏向量 $\mathbf{v}_d=[\text{tfidf}_{d,w_1},\dots,\text{tfidf}_{d,w_{|V|}}]$。

（如果作者直接用現成語句嵌入模型──如 Sentence-BERT──步驟 1–2 會由模型一次完成，但後續餘弦相似度的概念與公式完全相同。）

### 3. 計算餘弦相似度

給定兩篇文章的向量 $\mathbf{v}_i, \mathbf{v}_j$，餘弦相似度定義為

$$
\cos(\theta) = 
\frac{\mathbf{v}_i\cdot\mathbf{v}_j}{\|\mathbf{v}_i\|\;\|\mathbf{v}_j\|}
       =\frac{\sum_k v_{ik} v_{jk}}{\sqrt{\sum_k v_{ik}^2}\sqrt{\sum_k v_{jk}^2}}.
$$

值域在 $[-1,1]$；對於非負的文字向量通常落在 $[0,1]$。數值愈接近 1，代表兩篇文章用詞模式愈相似。

### 4. 套用「20 天 × 0.8」的過濾規則

* 對於當天新進的新聞 $d_t$，只需把 $\mathbf{v}_{d_t}$ 與 **過去 20 個交易日**內所有新聞向量比對。
* 若存在某篇舊文 $d_s$ 使得

  $$
  \cos(\mathbf{v}_{d_t},\mathbf{v}_{d_s})\ge0.8,
  $$

  就標記 $d_t$ 為重複並捨棄；否則保留。

0.8 的門檻相當嚴格，表示只有極高度重複（幾乎是同一篇報導或簡單改寫）的新聞才會被排除，從而 **壓低冗餘、節省後續 LLM 微調與回測的計算量**。這條規則也在文中再次被提及。

---

## 小結

* **公式**：餘弦相似度 $=\dfrac{\mathbf{v}_i\cdot\mathbf{v}_j}{\|\mathbf{v}_i\|\|\mathbf{v}_j\|}$。
* **向量來源**：文中雖未明說，最常見做法是 TF-IDF（亦可能使用句向量）。
* **實務流程**：把新文與過去 20 天新聞比對；若相似度 ≥ 0.8 就視為重複。

若你需要在自己的研究或程式中重現這一過濾步驟，採用 **scikit-learn 的 `TfidfVectorizer` + `cosine_similarity`** 即可輕鬆完成，或改用 `sentence-transformers` 產生語句嵌入後再計算餘弦值，二者皆符合論文描述的判準。
