# -*- coding: utf-8 -*-


#ポートフォリオ用


import discord
from discord.ext import commands
import openai
import datetime

#カレントディレクトリの設定とコンフィグ読み込み
import os
import sys
import errno
import configparser

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

# 指定したiniファイルが存在しない場合、エラー発生
if not os.path.exists("config.ini"):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "config.ini")

# iniの値の取得準備

config_ini = configparser.ConfigParser()
config_ini.read("config.ini", encoding="utf-8")
read_setting = config_ini["Settings"]

# あなたのDiscord botトークンとOpenAI APIキーを環境変数に設定
DISCORD_TOKEN = read_setting.get("DISCORD_BOT_API_KEY")
OPENAI_API_KEY = read_setting.get("OPENAI_API_KEY")

#その他
model = read_setting.get("default_model")
usd_to_jpy_rate = int(read_setting.get("usd_to_jpy_rate"))

# 使用するGlobal変数
total_cost = 0
month = 0
response = "記録されている情報がありません。最低でも１つ以上の問い合わせをしてください。"
default_activity = "!hでhelpを確認!cでチャット"

# OpenAI APIキーを設定
openai.api_key = OPENAI_API_KEY

# Botの接続と設定

bot = commands.Bot(
    command_prefix="!",
    help_command=None,
    intents=discord.Intents.all()
    )


#文章生成問い合わせ関数 gpt
async def gpt(message):    
    
        # ステータス変更
        await bot.change_presence(activity=discord.Game(name="返答を作成中..."))
        
        # 整形など
        req = message.content[3:]
        
        # !cだけの呼び出し
        if req == "":
            await message.channel.send("!c の後ろに質問を入力してください")
            return
        
        # ChatGPTに問い合わせる
        print("@gptに問い合わせます\n"+"'"+req+"'")
        global response
        
        #問い合わせ
        try:    
            response = openai.ChatCompletion.create(
                model= model,
                messages = [{"role":"user", "content":req}]
                )
                        
        except Exception as e:
            await message.channel.send("@問い合わせエラー...\n"+str(e))
            print("@問い合わせエラー...\n"+str(e))
            
            # ステータス変更
            await bot.change_presence(activity=discord.Game(name=default_activity))
            return
        
        # レスポンスから料金をtotal_costに加算する
        global total_cost
        global month
        
        today = datetime.date.today()
        month_now = today.month
        
        # 月が替わったらリセットする
        if month != month_now:            
            month = month_now
            total_cost = 0
        
        total_cost += costculc()
            
            
        # レスポンスから回答を取り出す
        chatgpt_response = response.choices[0]['message']['content'].strip()
        
        # レスポンスをDiscordチャンネルにembedで送信
        
        title = req[:60]+'...'
        embed = discord.Embed(
                              title=title,
                              description=chatgpt_response,
                              color=discord.Color.from_rgb(0,255,0)
                              )
        embed.set_footer( text=f'Made by {response["model"]}')
        await message.channel.send(embed=embed)

        # ステータス変更
        await bot.change_presence(activity=discord.Game(name=default_activity))

        
# 画像生成用問い合わせ関数 text to photo        
async def ttp(message):
    
        # ステータス変更
        await bot.change_presence(activity=discord.Game(name="返答を作成中..."))
        
        # 整形など
        req = message.content[3:]
        
        # !dだけの呼び出し
        if req == "":
            await message.channel.send("!d の後ろに質問を入力してください")
            return
                    
        # ChatGPTに問い合わせる
        print("@画像生成系に問い合わせます\n"+"'"+req+"'")
        global response
        
        #問い合わせ
        try:    
            response = openai.Image.create(
                n=1,
                prompt = req,
                size="1024x1024"
                #response_format="b64_json"
                )
                        
        except Exception as e:
            await message.channel.send("@問い合わせエラー...\n"+str(e))
            print("@問い合わせエラー...\n"+str(e))
            
            # ステータス変更
            await bot.change_presence(activity=discord.Game(name=default_activity))
            return
        
        # レスポンスから料金をtotal_costに加算する
        global total_cost
        global month
        
        today = datetime.date.today()
        month_now = today.month
        
        # 月が替わったらリセットする
        if month != month_now:            
            month = month_now
            total_cost = 0
        
        total_cost += usd_to_jpy(0.02)#0.02$dalle2
            
            
        # レスポンスから回答を取り出す
        Image_url = response['data'][0]['url']
        
        # レスポンスをDiscordチャンネルにembedで送信
        
        title = req[:60]
        embed = discord.Embed(
                              title=title,
                              #description=Image_url,
                              color=discord.Color.from_rgb(0,255,0)
                              )
        
        embed.set_image(url=Image_url)
        embed.set_footer( text=f'Made by dalle-2')
        await message.channel.send(embed=embed)

        # ステータス変更
        await bot.change_presence(activity=discord.Game(name=default_activity))        



def usd_to_jpy(amount)->int: #為替レートで変換する
    ans = usd_to_jpy_rate * amount
    return ans

def costculc()->int: #直前のAPI使用料金をintで返す
    # 使用料の算出
    tokens = response['usage']['total_tokens']
    cost_per_token = 0.06  # 現在の料金は $0.06/1,000トークン ですが、公式ウェブサイトを確認してください
    cost = tokens * cost_per_token / 1000
    cost = usd_to_jpy(cost)
    return cost

# 初期化
@bot.event
async def on_ready():
    
    print(f'{bot.user} is online')
    await bot.change_presence(activity=discord.Game(name=default_activity))
        
            
# メッセージイベント
@bot.event
async def on_message(message):
    
    # Bot自身が送信したメッセージは無視する
    if message.author == bot.user: 
            return
        
    # コマンドの読み取り help表示
    if message.content.startswith('!h'):
        await message.channel.send(f"""
対話コマンドの後ろに続けて質問を入力してください\n
<対話コマンド>\n
!c : 問い合わせる (default:gpt-4 !mで対話モデル指定可能)\n
!3 : gpt-3.5-turboに問い合わせる\n
!4 : gpt-4に問い合わせる\n
!p : テキストから画像を生成する (Dalle-2)\n
\n
<コマンド>\n
!u : おおよその料金を算出する\n
!m : コマンドの後ろに続けてモデルを指定する。指定後に!cで問い合わせる\n
!res : レスポンスオブジェクトを表示する\n
\n                                   
"""
                                   )
        return
        
    # コマンドの読み取り -> gpt3.5-turbo
    if message.content.startswith('!3'):
        
        global  model
        model = 'gpt-3.5-turbo'
        
        await gpt(message)
        return
        
    # コマンドの読み取り -> gpt4   
    if message.content.startswith('!4'):
        await gpt(message)
        return
    
    # コマンドの読み取り -> gpt4    
    if message.content.startswith('!c'):
        await gpt(message)
        return
    
    # コマンドの読み取り ->ttp
    if message.content.startswith('!p'):
        await ttp(message)
        return
    
            
    #　commandsとの併用で必要
    await bot.process_commands(message)



    
    
    
# api　料金の計算  
@bot.command()
async def u(ctx):
      
    #レスポンスオブジェクトが更新されない場合
    if response == "記録されている情報がありません。最低でも１つ以上の問い合わせをしてください。":
        await ctx.send(response)
        return
    
 
    ans = f"直前のメッセージのAPI使用料金(約): {costculc()}円\n{month}月の累積使用料: {total_cost}円\n(gpt-4,8kの値段で計算)\n\n詳細は以下公式HPより確認してください。\nhttps://platform.openai.com/account/usage"
    await ctx.send(ans)
    return

# モデルの指定（非推奨）
@bot.command()
async def m(ctx, arg):
    global model
    model = str(arg)
    await ctx.channel.send(f"モデルが「 {arg }」に設定されました。\n以降!c コマンドはモデル「 {arg }」によって返信されます。\nモデルが存在しない場合エラーになります。")
    return

#デバッグ用レスポンスオブジェクト表示コマンド    
@bot.command()
async def res(ctx):
    print('@レスポンスオブジェクトを表示します')
    print(response)
    await ctx.channel.send(response)
    return
    
# Botを実行
bot.run(DISCORD_TOKEN)