import tkinter as tk
import tkinter.simpledialog as dl
import tkinter.messagebox as mb

from PIL import Image,ImageTk

import requests
import re
import jieba 
from wordcloud import WordCloud
import json
import threading

import os
def create_dir_not_exist(path):
    if not os.path.exists(path):
        os.mkdir(path)
##########################爬虫

kv = {'user-agent':'Mozilla/5.0'}
post_kv = {
        'user-agent':'Mozilla/5.0',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9'
        }
font = './font./hlbs.ttf'#字体文件


#找piao页面的评论
piaorev = re.compile('content":"(.*?)","date')    
#找piao页面的评论数
revnum=re.compile('查看(\d+)条点评')
#找you页面的评论数
younum=re.compile('"f_orange">([0-9]+)</span>条点评')
#找you页面的评论
yourev=re.compile('<span class="heightbox">(.*?)</span>')
#找页面id
piaoid=re.compile('([0-9]+).html')
#piao的照片
piaopic=re.compile('(https://youimg[0-9].c-ctrip.com/target/.*?.jpg)"')
#you的照片https://youimg1.c-ctrip.com/target/100m10000000pc3dj595C_C_500_280_Q60.jpg
youpic=re.compile('(https://dimg[0-9]+.c-ctrip.com/images/.*?.jpg)"')
piaopic2=re.compile('(https://youimg[0-9].c-ctrip.com/target/.*?.png)"')
youpic2=re.compile('(https://dimg[0-9]+.c-ctrip.com/images/.*?.png)"')
#评论url
piaorevurl='https://sec-m.ctrip.com/restapi/soa2/12530/json/viewCommentList'
#获取景点的名字，网页和简介
nwi=re.compile('<span class="preferential_info">(.*?)</span></a><a class="search_newrecomname" href="(.*?)" target="_blank">(.*?)</a></li>')
sg = []#存放一整个国家的景点
#拼凑url


def geturl(nt):
    return ('https://vacations.ctrip.com/list/whole/sc140.html?sv={}&st={}'.format(nt,nt))
#获取页面
def getHTMLText(url):
    try:
        r = requests.get(url,headers=kv,timeout=30)
        r.raise_for_status()
        #r.encoding = r.apparent_encoding
        return r.text
    except:
        return 'Get error'

def creatwordcloud(n,rev):
    cut =' '.join(set(jieba.cut(' '.join(rev))))
    wc = WordCloud(font_path=font,background_color='white',width=500,height=400,).generate(cut)
    wc.to_file('{}{}{}'.format('./wordcloud./',n,'.png')) #保存图片
    print('{}词云已生成'.format(n))
#若网站是piao打头执行下面这个函数
def createphoto(n,phototext):
    p=re.findall(piaopic,phototext)+re.findall(youpic,phototext)+re.findall(piaopic2,phototext)+re.findall(youpic2,phototext)  
    photo = requests.get(p[0])

    with open('./photo./{}.jpg'.format(n),'wb') as file:
        file.write(photo.content)
        print('{}照片已生成'.format(n))
def webisyou(n,youtext):
    creatwordcloud(n,re.findall(yourev,youtext))

    return re.findall(younum,youtext)

def webispiao(n,urlid):
    data1={
    "pageid":"10650000804" ,
    "viewid":urlid,
    "tagid":"0",
    "pagenum":"1",
    "pagesize":"10",
    "contentType":"json",
    "SortType":"1",
    "head":{
            "appid":"10013776",
            "cid":"09031037211035410190",
            "ctok":"",
            "cver":"1.0",
            "lang":"01",
            "sid":"8888",
            "syscode":"09",
            "auth":"",
            "extension":[
                        {
                        "name":"protocal",
                        "value":"https"
                        }
                    ]
            },
            "ver":"7.10.3.0319180000"
            }  
    r = requests.post(piaorevurl,data=json.dumps(data1))
    creatwordcloud(n,re.findall(piaorev,r.text))
lock = threading.Lock()   
ei='' 
def getsight(nt,n,url):
    global sg
    global ei
    print('正在整理{}'.format(n))
    url='https:{}'.format(url)
    sighttext = getHTMLText(url)
    if sighttext == 'Get error':
        ei= '{}{}error'.format(nt,n)
    x=[]
    x = re.findall(revnum,sighttext)
    if x==[]:
        x=webisyou(n,sighttext)
        
    else:
        webispiao(n,re.findall(piaoid,url)[0])
    createphoto(n,sighttext)
    lock.acquire()
    try:
        sg.append([n,x[0]])
    finally:
        lock.release()
#核心函数爬取数据
def sgget(nt):
    global sg
    global ei
    sg=[]
    nationtext = getHTMLText(geturl(nt)) 
    if nationtext == 'Get error':
        ei='{} error'.format(nt)
    sight = re.findall(nwi,nationtext)
    t=[]
    for i in sight:
        t+=[threading.Thread(target=getsight,args=(nt,i[0],i[1]))]
        with open('./introduce./{}.txt'.format(i[0]), 'wt',encoding='utf-8')as file:
            file.write(i[2])
    for i in t:
        i.start()
    for i in t:
        i.join()
    sg.sort(key=lambda x:int(x[1]),reverse=True)
    
    return sg


#####################基本数据
##############爬取新国家    
def addnewnt():
    global sight
    global nation
    mb.showinfo('添加新国家','请输入国家名')
    new = dl.askstring('添加新国家','请输入国家名')
    if new in nation:
        mb.showinfo('国家已存在','国家已存在')
    else:
        sgget(new)
        if'error' in ei:
            mb.showinfo('出错',ei)
        elif sg==[]:
            mb.showinfo('返回数据为空','返回数据为空')   
        else:
            with open('./数据./{}.csv'.format(new),'wt',encoding='utf-8')as f:
                for i in sg:
                    f.write(','.join(i)+'\n')
            with open('./数据./国家.csv','at',encoding='utf-8')as f:
                f.write(','+new)
            nation+=[new]
            sight[new]=sg
            lsbox1.insert(tk.END,new)
#############top窗口初始化
def cyinit(n):
    global cy
    cy.destroy()
    cy=tk.Toplevel()
    global img1
    global img2
    cy.title(n)
    frm=tk.Frame(cy)
    t = tk.Text(frm,height=5)
    with open('./introduce./{}.txt'.format(n),'rt',encoding='UTF-8')as intr:
        t.insert('1.0',intr.read())
    t.pack(side='bottom')#,fill=tk.X)
    im1=Image.open("./wordcloud./{}.png".format(n))
    img1=ImageTk.PhotoImage(im1)
    imLabel1=tk.Label(cy,image=img1)
    imLabel1.pack(side='left')#,image=img
    im2=Image.open("./photo./{}.jpg".format(n)).resize((500,280))
    img2=ImageTk.PhotoImage(im2)
    imLabel2=tk.Label(frm,image=img2)
    imLabel2.pack(side='top')
    frm.pack(side='right')
    
    

#读取某个国家的数据
def readsight(nt):
    with open('./数据./{}.csv'.format(nt),'rt',encoding='UTF-8')as sight:
        ns=[]
        for line in sight:
            line = line.replace('\n','')
            ns.append(line.split(','))
        return ns
#读取国家列表
def readnation():
    nt=[]
    with open('./数据./国家.csv','rt',encoding = 'UTF-8')as n:
        nt=n.read().split(',')
    return nt
def changent(event):
    global nt
    nt=nation[lsbox1.curselection()[0]]
    lsbox2.delete(0,tk.END)
    l2['text']=nt
    for i in sight[nt]:
        lsbox2.insert(tk.END,i[0]+i[1])
def changest(event):

    st=sight[nt][lsbox2.curselection()[0]][0]
    cyinit(st)

###################初始化
create_dir_not_exist('数据')
create_dir_not_exist('photo')
create_dir_not_exist('wordcloud')
create_dir_not_exist('introduce')

nt='日本'
st=''
nation=readnation()
sight={}
for i in nation:
    sight[i]=readsight(i)

###################GUI
window = tk.Tk()
#窗口设置
window.title('sight')
window.geometry('300x250')
window.resizable(0,0)
cy = tk.Toplevel()

cyinit('日本环球影城')

#列表框1显示国家
l1 = tk.Label(window,text = "国家",bg='pink',font=('Arial',12))
lsbox1 = tk.Listbox(window,width=8,height=10)

for i in nation:
    lsbox1.insert(tk.END,i)

#列表框2显示景点
l2 = tk.Label(window,text = "日本",bg='blue',font=('Arial',12))
lsbox2 = tk.Listbox(window,width=20,height=10)
for i in sight['日本']:
    lsbox2.insert(tk.END,i[0]+i[1])

l1.place(x=0,y=0,anchor='nw')
l2.place(x=60,y=0,anchor='nw')
lsbox1.pack(side=tk.LEFT)
lsbox2.pack(side=tk.LEFT)
#############按钮爬取新国家

b1 = tk.Button(window,width=8,height=1,text='爬取新国家',command=addnewnt)
b1.pack(side='right')


###############################################################


lsbox1.bind("<Double-Button-1>",changent)
lsbox2.bind("<Double-Button-1>",changest)
#####################################################
window.mainloop()
