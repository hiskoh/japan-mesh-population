# mesh_population_data
日本の国勢調査 人口メッシュデータのリストデータ（人口値の採録されたデータ）のe-StatAPIでの一括取得

**成果物CSVの例**

[国勢調査2020 人口メッシュデータ250mメッシュ・年齢別人口、世帯の種類別世帯数等](https://app.box.com/s/qcpal72afgrpwkidc5cpc6whww4za5ic)


# 手順

## 1. e-Stat API利用準備（ユーザ登録）
1. マイページ内「API機能(アプリケーションID発行)」より、「アプリケーションIDの取得」ページに移動
2. 名称とURLを入力し「発行」を選択
   
<img width="400" alt="image" src="https://github.com/hiskoh/japan-mesh-population/assets/13606213/ee421a41-bdc4-42d1-b78e-17db22f4f8ab">

4. 上記ページの「appId」欄に自身のAPIのアプリケーションIDが表示されるので手元に控える

## 2. Pythonでのデータ一括取得

取得用Pythonコードはこちらに格納済です。

https://github.com/hiskoh/japan-mesh-population/blob/main/get_japan_mesh_population_data.py

### 説明

データを取得するには、
1. 対象データの統計表IDの一覧表を取得（e-StatのWebサイト上でCSVファイルとして扱われている表の1つ1つを統計表と呼ぶらしい。CSV1つ1つのIDを取得するイメージです）
2. 統計表IDごとにデータを取得（CSVをダウンロードするイメージです）
の2段階のプロセスを踏みます。

#### 統計表IDの一覧表を取得

##### 変数の設定
最初にAPI取得に必要な各種変数を設定します。今回は国勢調査2020年の250mメッシュ人口データを取得する目的に特化したコードですが、別のデータを取る際にはまずはこの変数部分を変更してください。

```python
#各種変数を指定
appId = 'hoge' #自身のAPIキーを設定
statsCode = '00200521' #政府統計コード（国勢調査のコード番号は00200521)
surveyYear = '2020' #国勢調査の調査年
openYear = '2022' #データの公開年
updatedDate = '2022' #データの最終更新年
searchWord = '250m' #検索ワード
```

政府統計コード（国勢調査の場合は00200521）は、e-Statの対象データの「定義書」に載っています。

統計コード番号を検索するAPIもあるのですが、目的が決まっているなら定義書から索引したほうが早い（と思い）定義書から取得しました。

調査年などのデータもe-Statの<a href ="https://www.e-stat.go.jp/gis/statmap-search?page=1&type=1&toukeiCode=00200521&toukeiYear=2020&aggregateUnit=Q&serveyId=Q002005112020&statsId=T001102">ダウンロード画面</a>に載っているので、そこから変数に設定しました。



<img width="400" alt="image" src="https://github.com/hiskoh/japan-mesh-population/assets/13606213/69e7a94f-effd-4172-a6d3-fd60f062f53e">
<img width="400" alt="image" src="https://github.com/hiskoh/japan-mesh-population/assets/13606213/d71963c2-d5da-4589-9168-2c38fab6d09c">


##### 統計表情報取得APIの実行・統計表IDの取得

e-StatのAPIで統計表IDを取得します。

250mメッシュ人口データの場合、2次メッシュごとにデータが分けられている（CSVが分かれている）ので、全2次メッシュ分の統計表IDを取得します。

なお2023年6月にデータ取得した際は、151件の統計表IDがヒットしました。

```python
#e-Stat統計表情報取得APIで該当データの一覧を取得
url = 'http://api.e-stat.go.jp/rest/3.0/app/getStatsList?appId='+ appId + '&lang=J&surveyYears=' + surveyYear + '&openYears=' + openYear + '&updatedDate=' + updatedDate + '&statsCode=' + statsCode +'&collectArea=1&searchKind=2&searchWord=' + searchWord +'&explanationGetFlg=Y'
response = requests.get(url)
response.encoding = response.apparent_encoding

#取得結果からデータの統計表IDを取得（メッシュ統計データの場合、2次メッシュごとにファイルが分かれているので、そのファイルごとのIDを取得）
soup = bs(response.text, 'html.parser')
table_inf_tags = soup.find_all('table_inf')
table_inf_ids = [tag.get('id') for tag in table_inf_tags]
```
ちなみにAPIのパラーメータ設定方法は公式サイトに<a href ="https://www.e-stat.go.jp/api/sample/testform3-0/">テストフォーム</a>が用意されているので、違うデータを取得したい際はそちらでトライ＆エラーするとよい。

#### 統計データ取得API

##### API実行

e-StatAPIは、目的に応じて複数のAPIが公開されています。

上の処理までで、既に欲しいデータの統計表IDはわかっているので、あとはそのIDをキーに中身のデータを取得すればよい。

違うデータを取得したい際は先ほど同様に<a href ="https://www.e-stat.go.jp/api/sample/testform3-0/">テストフォーム</a>を使用するとよい。

```python
#Dataframeを初期化
df = pd.DataFrame()
pivot_df = pd.DataFrame()

#-Stat統計データ取得APIで、統計表IDごとにデータを取得
for table_inf_id in table_inf_ids:
    url = 'http://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData?appId='+appId+'&lang=J&statsDataId=' + table_inf_id + '&metaGetFlg=N&cntGetFlg=N&explanationGetFlg=N&annotationGetFlg=N&replaceSpChars=2&sectionHeaderFlg=2'
    response = requests.get(url)
    temp_df = pd.read_csv(io.BytesIO(response.content),sep=",")
    df = pd.concat([df, temp_df], ignore_index=True)
```
万一データ量が多く処理が終わらなさそうな場合は
``pyhton for table_inf_id in table_inf_ids[0:50]:``　``pyhton for table_inf_id in table_inf_ids[51:100]:``のように対象を分割して以降の処理を進めるのも手。

##### 取得データの集計（ピポッド）

取得データはリストデータになっている。サイトから直接CSVダウンロードした際のようにmesh番号に横並びで各種valueが並んでいる状態を作るためpivodする。

```python
#データ加工(のちにpivotする際にカラム名ソートをするため、コード番号を先頭に付与)
df['カラム名'] = df['cat01_code'].astype(str).str.zfill(4) + '_' + df['年齢別人口、世帯の種類別世帯数等　']

#pivodしカラム名でソート
pivot_df = df.pivot(index=['area_code','秘匿地域・合算地域有り'], columns='カラム名', values='value').sort_index(axis=1)

#不要となった先頭コード番号を削除
pivot_df.columns = [col[6:] for col in pivot_df.columns]
```

カラム名（国勢調査2020 人口データの場合「年齢別人口、世帯の種類別世帯数等　」）をCSV同様の順番に並べ替えるため、少し無理矢理にカラムにコード番号（ダウンロード時に付いてくるカラム識別用ID）をつかってソートをかけています。

##### CSV出力

最後はCSV出力して終わり。
```python 
#CSV出力
pivot_df.to_csv('C:\\Users\\hoge\\mesh_population_data_kokusei2020.csv')
```

# 参考情報

e-Stat APIは下記の公式サイトでAPIの組み方を指南してくれるので、それを参考に任意のAPIを組むことができます。

再掲）https://www.e-stat.go.jp/api/sample/testform3-0/
