import numpy as np
import os
import glob
import datetime
import time
import warnings
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
import matplotlib.colors as mcolors
import random
import shutil
import streamlit as st

warnings.simplefilter('ignore')

# ファイル初期化
for filename in  glob.glob('*.zip'):
    os.remove(filename)

files = os.listdir()
# 出力ディレクトリの作成
output_dir = "output_pdf"
os.makedirs(output_dir, exist_ok=True)
# PDFファイルを検索して移動
for file in files:
    if file.endswith(".pdf"):
        source_path = os.path.join(os.getcwd(), file)
        destination_path = os.path.join(os.getcwd(), output_dir, file)
        shutil.move(source_path, destination_path)


st.set_page_config(
    page_title="集中力チェックシートジェネレータ",
    page_icon='https://avatars.githubusercontent.com/u/107293507?v=4',
    )

st.title('集中力チェックシートジェネレータ')
st.caption('指定したパターンで集中力チェックシートらしきものを生成します')

def get_time(format:str):
  now_uct = datetime.datetime.now()
  format_time = now_uct.strftime(format)
  return format_time

def gen_imgs(amount:int, min:int, max:int):
    count = 1
    gen_time = get_time('%Y%m%d%H%M%S')

    save_dir = f'output_{gen_time}'
    os.mkdir(save_dir)

    for i in range(amount):
        # 画像のサイズ
        image_width = 800
        image_height = 1131
        padding = 10

        # 画像を作成
        image = Image.new("RGB", (image_width, image_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 数字のリストを作成
        numbers = list(range(min, max))

        # リストをシャッフル
        random.shuffle(numbers)

        # 数字を貼り付ける設定
        font_size = 20
        font = ImageFont.truetype("NotoSansArabic-Regular.ttf", font_size)

        # 数字の位置情報を保持するリスト
        number_positions = []

        # 数字をランダムな位置に貼り付ける
        for number in numbers:
            # 数字の位置をランダムに決定
            text_width, text_height = draw.textsize(str(number), font=font)
            x = random.randint(padding, image_width - text_width - padding)
            y = random.randint(padding, image_height - text_height - padding)
            
            # 数字が他の数字と重ならないように位置を微調整
            for existing_position in number_positions:
                existing_x, existing_y, existing_width, existing_height = existing_position
                if (
                    existing_x <= x <= existing_x + existing_width or
                    existing_x <= x + text_width <= existing_x + existing_width or
                    x <= existing_x <= x + text_width or
                    x <= existing_x + existing_width <= x + text_width
                ) and (
                    existing_y <= y <= existing_y + existing_height or
                    existing_y <= y + text_height <= existing_y + existing_height or
                    y <= existing_y <= y + text_height or
                    y <= existing_y + existing_height <= y + text_height
                ):
                    # 数字が重なる場合は、y座標を微調整
                    y = existing_y + existing_height + 5
            
            # 数字の位置情報をリストに追加
            number_positions.append((x, y, text_width, text_height))
            
            # 数字を画像に貼り付け
            draw.text((x, y), str(number), font=font)

        # 画像を保存
        image.save(f"{save_dir}/output_image_{count}.png")
        gen_progress.progress(count/amount, text=f'シート生成中...({count}/{amount})')
        count = count + 1

    return save_dir
        
def gen_pdf(directory_path):
    image_files_tmp = os.listdir(directory_path)

    image_files = []
    for file in image_files_tmp:
        image_files.append(directory_path+"/"+file)

    gen_time = get_time('%Y%m%d%H%M%S')
    output_pdf = f'output_{gen_time}.pdf'

    # PDFキャンバスを作成
    c = canvas.Canvas(output_pdf, pagesize=landscape)

    # 画像をPDFに追加
    for image_file in image_files:
        # 画像を開く
        image = Image.open(image_file)

        # 画像サイズを取得
        width, height = image.size

        # PDFページサイズを画像サイズに合わせて作成
        c.setPageSize((width, height))

        # 画像を描画
        c.drawImage(image_file, 0, 0, width, height)

        # 新しいページを追加
        c.showPage()

    # PDFファイルを保存
    c.save()

    return output_pdf

tab1, tab2 = st.tabs(["📈生成", "⚙設定"])

with tab1:
    input_form = st.form('input')

    with input_form:
        amount = st.number_input('枚数',1,100,5,key=str)
        values = st.slider('範囲',1, 100, (1, 50))
        
        warning_area = st.empty()
        gen_progress = st.empty()
        submit = st.form_submit_button('生成する',type='primary')

    if submit:
        warning_area.warning('生成中です。ボタンを押さないでください。', icon="⚠️")
        gen_progress.progress(0,f'シート生成中...(0/{amount})')
        save_dir = gen_imgs(amount,values[0], values[1]+1)
        gen_progress.empty()
        gen_progress.write('PDFファイル生成中...')
        pdf_path = gen_pdf(save_dir)
        gen_progress.empty()
        shutil.make_archive(save_dir, 'zip', save_dir)
        file_size_zip = os.path.getsize(save_dir+".zip")
        file_size_pdf = os.path.getsize(pdf_path)

        st.success("生成が完了しました。下のボタンからダウンロードして下さい。\n(キャンセルした場合、生成したファイルは削除されます。)")
        img_dl, pdf_dl ,cancel, = st.columns([7,7,8], gap='small')
        st.write(f"{save_dir}.zip({file_size_zip/100}KB) or {pdf_path}({file_size_pdf/100}KB)")
        with img_dl:
            with open(save_dir+".zip", "rb") as fp:
                btn = st.download_button(
                    label="画像でダウンロードする",
                    data=fp,
                    file_name=save_dir+".zip",
                    mime="application/zip"
                )
        with pdf_dl:
            with open(pdf_path, "rb") as fp:
                btn = st.download_button(
                    label="PDFでダウンロードする",
                    data=fp,
                    file_name=pdf_path,
                    mime="application/zip"
                )

        with cancel:    
            st.button('キャンセル')

        warning_area.empty()

with tab2:
    with st.form('pdf_remove'):
        st.text('PDFファイル削除')
        st.caption('生成済みのPDFファイル(output_pdf内)を削除します')
        with st.expander('削除対象の生成済みファイル(ファイル名クリックでダウンロード)'):
            for file in os.listdir('output_pdf'):
                file_size = os.path.getsize("output_pdf/"+file)
                href = f'<a href="output_pdf/{file}" download="output">{file}({file_size/100}KB)</a>'
                link = st.markdown(href, unsafe_allow_html=True)
        if st.form_submit_button('削除する'):
            shutil.rmtree('output_pdf')
            os.mkdir('output_pdf')
            sc_rm = st.success('削除しました')
            time.sleep(3)
            sc_rm.empty()


