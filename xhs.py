import requests
from bs4 import BeautifulSoup
import os
import shutil
from flask import Flask, request, render_template_string, send_from_directory

# 定义保存图片的文件夹名称
folder_name = "downloaded_images"

# 创建 Flask 应用
app = Flask(__name__)

# 清空文件夹内容
def clear_folder():
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
        print(f"已清空文件夹 '{folder_name}'。")
    os.makedirs(folder_name)
    print(f"文件夹 '{folder_name}' 已创建。")

# 爬取并下载图片
@app.route('/scrape', methods=['POST'])
def scrape_images():
    url = request.form['url']  # 从网页表单获取输入的网址

    if not url:
        return "请输入有效的网址", 400

    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 发送请求获取网页数据
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"请求失败，状态码: {response.status_code}", 400

        # 解析网页数据
        soup = BeautifulSoup(response.content, 'html.parser')

        # 清空并重新创建文件夹
        clear_folder()

        # 查找所有 meta 标签
        meta_tags = soup.find_all('meta', attrs={'name': 'og:image'})

        if not meta_tags:
            return "未找到任何图片", 200

        # 保存图片文件名列表
        image_filenames = []

        # 遍历所有的 meta 标签并下载图片
        for meta_tag in meta_tags:
            img_url = meta_tag.get('content')

            try:
                # 请求图片
                img_response = requests.get(img_url)

                # 检查是否是图片
                if "image" in img_response.headers["Content-Type"]:
                    ext = img_response.headers["Content-Type"].split("/")[-1]
                    img_name = os.path.basename(img_url).split("?")[0] + f".{ext}"

                    # 保存图片到文件夹
                    img_path = os.path.join(folder_name, img_name)
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_response.content)
                    image_filenames.append(img_name)
                    print(f"已下载并保存图片: {img_name}")
                else:
                    print(f"跳过非图片资源: {img_url}")

            except Exception as e:
                print(f"无法下载图片: {img_url}, 错误: {e}")

        # 将本地图片文件名传递给前端页面进行显示
        return render_template_string('''
            <h1 style="font-size: 24px; text-align: center;">图片获取成功！点击图片保存：</h1>
            <div style="text-align: center;">
                {% for img in image_filenames %}
                    <div style="padding: 10px;">
                        <img src="{{ url_for('get_image', filename=img) }}" alt="图片" style="max-width: 100%; height: auto;"/>
                    </div>
                {% endfor %}
            </div>
            <br>
            <div style="text-align: center;">
                <a href="/" style="font-size: 18px;">返回输入页面</a>
            </div>
        ''', image_filenames=image_filenames)

    except Exception as e:
        return f"无法请求网页: {e}", 500

# 提供下载的图片文件
@app.route('/images/<filename>')
def get_image(filename):
    # 获取绝对路径的 downloaded_images 文件夹
    image_folder = os.path.abspath(folder_name)
    print(image_folder)
    return send_from_directory(image_folder, filename)

# 主页，用于输入网址
@app.route('/')
def home():
    return '''
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh; text-align: center; flex-direction: column;">
            <h1 style="font-size: 28px;">无水印图片下载 bySummer</h1>
            <form action="/scrape" method="post" style="font-size: 20px;">
                <label for="url" style="font-size: 20px;">请输入小红书链接:</label><br><br>
                <input type="text" id="url" name="url" style="width: 300px; font-size: 18px; padding: 10px;"/><br><br>
                <input type="submit" value="读取图片" style="font-size: 20px; padding: 10px 20px;"/>
            </form>
        </div>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
