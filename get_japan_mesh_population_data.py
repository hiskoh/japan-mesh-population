import requests
import pandas as pd
import io
import re
from bs4 import BeautifulSoup as bs

#各種変数を指定
appId = 'hoge' #自身のAPIキーを設定
statsCode = '00200521' #政府統計コード（国勢調査のコード番号は00200521)
surveyYear = '2020' #国勢調査の調査年
openYear = '2022' #データの公開年
updatedDate = '2022' #データの最終更新年
searchWord = '250m' #検索ワード


#e-Stat統計表情報取得APIで該当データの一覧を取得
url = 'http://api.e-stat.go.jp/rest/3.0/app/getStatsList?appId='+ appId + '&lang=J&surveyYears=' + surveyYear + '&openYears=' + openYear + '&updatedDate=' + updatedDate + '&statsCode=' + statsCode +'&collectArea=1&searchKind=2&searchWord=' + searchWord +'&explanationGetFlg=Y'
response = requests.get(url)
response.encoding = response.apparent_encoding

#取得結果からデータの統計表IDを取得（メッシュ統計データの場合、2次メッシュごとにファイルが分かれているので、そのファイルごとのIDを取得）
soup = bs(response.text, 'html.parser')
table_inf_tags = soup.find_all('table_inf')
table_inf_ids = [tag.get('id') for tag in table_inf_tags]

#Dataframeを初期化
df = pd.DataFrame()
pivot_df = pd.DataFrame()
result = pd.DataFrame()

#-Stat統計データ取得APIで、統計表IDごとにデータを取得
#もしデータ量が多すぎたときは for table_inf_id in table_inf_ids[:50]:などデータを絞り込んでfor文を動かす
for table_inf_id in table_inf_ids[:50]:

    #データ開始位置
    start_num = '0'
    
    #e-Stat仕様上一度に取れるデータは10万件に限定されるため、次のデータの開始位置がNone＝全データ取得完了までデータ取得を継続
    while start_num != None :
        #データフレーム初期化
        temp_df = pd.DataFrame()
        
        #データを取得   
        url = 'http://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData?appId='+appId+'&lang=J&statsDataId=' + table_inf_id + '&metaGetFlg=N&cntGetFlg=N&startPosition='+start_num +'&explanationGetFlg=N&annotationGetFlg=N&replaceSpChars=2&sectionHeaderFlg=1'
        response = requests.get(url)
        data = response.content.decode('utf-8')
    
        #冒頭の統計情報を読み飛ばし、データ行以降を取得
        data_after_cat01_code= '"cat01_code' + data.split('cat01_code')[1]
        temp_df = pd.read_csv(io.StringIO(data_after_cat01_code),sep=",")
    
        #同じ統計表IDのデータを1つのデータフレームに統合
        df = pd.concat([df, temp_df], ignore_index=True)

        #同じ統計表ID内で、次のデータ開始位置を取得
        match = re.search(r'"NEXT_KEY","(.*?)"\n', data)
        start_num = match.group(1) if match else None
        
    #同じ統計表ID内のデータについてpivodして整形する
    #データ加工(のちにpivotする際にカラム名ソートをするため、コード番号を先頭に付与)
    df['カラム名'] = df['cat01_code'].astype(str).str.zfill(4) + '_' + df['年齢別人口、世帯の種類別世帯数等　']

    #重複行削除
    df = df.drop_duplicates()
    
    #pivodしカラム名でソート
    pivot_df = df.pivot(index=['area_code','秘匿地域・合算地域有り'], columns='カラム名', values='value').sort_index(axis=1)

    #不要となった先頭コード番号を削除
    pivot_df.columns = [col[6:] for col in pivot_df.columns]
    
    #pivotしたデータをCSV出力用の結果DFに追加
    result = pd.concat([result, pivot_df], ignore_index=True)

#CSV出力
pivot_df.to_csv('C:\\Users\\hoge\\mesh_population_data_kokusei2020.csv')
