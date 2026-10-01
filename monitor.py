import os,re,json,html,hashlib
from datetime import datetime,timedelta,timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET
JST=timezone(timedelta(hours=9)); TODAY=datetime.now(JST).date()
TOKEN=os.getenv('TICKET_LINE_CHANNEL_ACCESS_TOKEN','').strip(); STATE='state.json'
S=['YOASOBI','Ado','Mrs. GREEN APPLE','Official髭男dism','King Gnu','藤井風','米津玄師','Vaundy','あいみょん','back number','サザンオールスターズ','福山雅治','B\'z','Mr.Children','星野源','Perfume','NiziU','FRUITS ZIPPER','乃木坂46','櫻坂46','日向坂46','Snow Man','SixTONES','なにわ男子','timelesz','Travis Japan','King & Prince','BE:FIRST','JO1','INI','HANA','TWICE','BTS','SEVENTEEN','Stray Kids','aespa','NewJeans','ILLIT','LE SSERAFIM','鬼滅の刃','呪術廻戦','ONE PIECE','ワンピース','ポケモン','名探偵コナン','ドラえもん','ちいかわ','サンリオ','SPY×FAMILY','ヒロアカ','ハイキュー','ブルーロック','ガンダム','ドラゴンボール','NARUTO','BORUTO','エヴァンゲリオン','ディズニー','Disney','ジブリ','花澤香菜','宮野真守','神谷浩史','梶裕貴','下野紘','花江夏樹','悠木碧','早見沙織','佐倉綾音','水瀬いのり','鬼頭明里','上坂すみれ','内田真礼','山寺宏一','SUMMER SONIC','サマーソニック','ROCK IN JAPAN','COUNTDOWN JAPAN','JAPAN JAM','FUJI ROCK','フジロック','METROCK','メトロック','AnimeJapan','アニメジャパン','コミックマーケット','東京ゲームショウ']
A=['東京','東京都','埼玉','さいたま','大宮','池袋','新宿','渋谷','有明','東京ドーム','日本武道館','さいたまスーパーアリーナ','舞台挨拶','完成披露','完成披露試写会','限定イベント','限定','先行','先行受付','抽選','抽選受付','プレオーダー','プレリザーブ','オフィシャル先行','最速先行','二次先行','一般発売前','一般発売に先駆け','試写会','トークショー','ファンミーティング']
EX=['スポーツ','野球','サッカー','Jリーグ','バスケットボール','eスポーツ','海外公演','海外イベント','中古','転売','相場','ランキング','炎上','事故']
Q=['"抽選" "受付開始" ライブ 東京','"抽選" "受付開始" ライブ 埼玉','"先行受付" "本日" ライブ 東京','"先行受付" "本日" ライブ 埼玉','"抽選受付" "舞台挨拶" 映画','"抽選受付" "完成披露" 映画','"プレオーダー" 東京 アニメ','"プレリザーブ" 東京 アニメ','"オフィシャル先行" 東京 ライブ','"オフィシャル先行" 埼玉 ライブ','"限定イベント" 抽選 東京','"ファンミーティング" 抽選 東京','"声優" "抽選" 東京 イベント','"大型フェス" "先行" 東京','"抽選" "受付開始" 人気アニメ','"抽選" "受付開始" 人気映画']
def fetch(u):
 r=Request(u,headers={'User-Agent':'Mozilla/5.0 TicketStartAlert/1.0'}); return urlopen(r,timeout=20).read()
def rss(q):
 try: root=ET.fromstring(fetch('https://news.google.com/rss/search?q='+quote(q+' when:1d',safe='')))
 except Exception as e: print('RSS error',e); return []
 out=[]
 for x in root.findall('./channel/item'):
  pub=x.findtext('pubDate') or ''
  try: dt=parsedate_to_datetime(pub).astimezone(JST)
  except: dt=datetime.now(JST)
  out.append({'title':html.unescape(x.findtext('title') or '').strip(),'link':x.findtext('link') or '','desc':html.unescape(re.sub('<[^>]+>',' ',x.findtext('description') or '')).strip(),'dt':dt.isoformat()})
 return out
def norm(s): return re.sub(r'[「」『』【】（）()［］\[\]・:：,.，、!！?？/／\-—_\s]','',s.lower())
def hits(t,ws): return [w for w in ws if norm(w) in norm(t)]
def score(i):
 t=i['title']+' '+i['desc']; z=0;r=[]
 h=hits(t,S)
 if h:z+=5;r.append('S:'+h[0])
 h=hits(t,A)
 if h:z+=2;r.append('A:'+h[0])
 if re.search(r'(抽選|プレオーダー|プレリザーブ|オフィシャル先行|先行受付)',t):z+=4;r.append('抽選/先行')
 if re.search(r'(舞台挨拶|完成披露|試写会)',t):z+=3;r.append('映画イベント')
 if re.search(r'(東京|東京都|埼玉|さいたま|大宮|池袋|新宿|渋谷)',t):z+=2;r.append('東京/埼玉')
 if re.search(r'(一般発売前|一般発売に先駆け)',t):z+=2;r.append('一般発売前')
 if '限定' in t:z+=2;r.append('限定')
 return z,r
def today_start(i):
 t=i['title']+' '+i['desc']
 try: d=datetime.fromisoformat(i['dt']).astimezone(JST).date()
 except:return False
 if d!=TODAY:return False
 if re.search(r'(本日|今日).{0,30}(受付|応募|抽選|申込|エントリー|先行|販売|発売|開始|スタート)',t):return True
 dates=[TODAY.strftime('%Y/%m/%d'),TODAY.strftime('%Y-%m-%d'),f'{TODAY.year}/{TODAY.month}/{TODAY.day}',f'{TODAY.year}-{TODAY.month}-{TODAY.day}']
 return any(x in t for x in dates) and bool(re.search(r'(受付期間|応募期間|申込期間|エントリー期間|販売期間|先行期間|開始)',t))
def dedupe(xs):
 seen=set();out=[]
 for i in xs:
  k=re.sub(r'(抽選|先行|受付|開始|応募|申込|エントリー|東京|埼玉|東京都|さいたま)','',norm(i['title']))
  h=hashlib.sha1(k.encode()).hexdigest()
  if h not in seen:seen.add(h);out.append(i)
 return out
def line(msg):
 if not TOKEN:raise RuntimeError('TICKET_LINE_CHANNEL_ACCESS_TOKEN 未設定')
 b=json.dumps({'messages':msg},ensure_ascii=False).encode();r=Request('https://api.line.me/v2/bot/message/broadcast',data=b,method='POST',headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'})
 print('LINE',urlopen(r,timeout=20).status)
def flex(xs):
 bubbles=[]
 for i in xs[:10]:
  z,rs=score(i);rank='S' if any(x.startswith('S:') for x in rs) else 'A'
  bubbles.append({'type':'bubble','size':'mega','body':{'type':'box','layout':'vertical','spacing':'sm','contents':[{'type':'text','text':f'🔥 {rank}ランク｜本日開始','weight':'bold','size':'sm'},{'type':'text','text':i['title'][:70],'weight':'bold','wrap':True,'size':'md'},{'type':'text','text':re.sub(r'\s+',' ',i['desc'])[:180] or '詳細はリンク先をご確認ください。','wrap':True,'size':'sm','color':'#666666'},{'type':'text','text':'｜'.join(rs[:4]),'wrap':True,'size':'xs','color':'#888888'}]},'footer':{'type':'box','layout':'vertical','contents':[{'type':'button','style':'primary','action':{'type':'uri','label':'詳細・応募はこちら','uri':i['link']}}]}})
 return {'type':'flex','altText':f'🎫 本日から応募・受付開始 {len(xs)}件','contents':{'type':'carousel','contents':bubbles}}
def main():
 xs=[]
 for q in Q:
  for i in rss(q):
   t=i['title']+' '+i['desc']
   if any(x.lower() in t.lower() for x in EX) or not today_start(i):continue
   z,r=score(i)
   if z>=7:i['score']=z;xs.append(i)
 xs=dedupe(sorted(xs,key=lambda x:(-x['score'],x['title'])))
 try: state=json.load(open(STATE,encoding='utf-8'))
 except: state={'sent':[]}
 sent=set(state.get('sent',[]));fresh=[]
 for i in xs:
  k=hashlib.sha1((norm(i['title'])+TODAY.isoformat()).encode()).hexdigest()
  if k not in sent:i['key']=k;fresh.append(i)
 print('候補',len(xs),'新規',len(fresh))
 for i in fresh:print(i['score'],i['title'],i['link'])
 if fresh:
  line([flex(fresh)]);sent.update(i['key'] for i in fresh);state['sent']=list(sent)[-1000:]
  json.dump(state,open(STATE,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
if __name__=='__main__':main()
