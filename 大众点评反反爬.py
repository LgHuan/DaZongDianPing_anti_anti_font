import json
import numpy
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from lxml import etree
from pyppeteer import launch
import asyncio
import re
import requests
from aip import AipOcr



class Pyppeteer():
    async def init(self):
        # 'headless': False如果想要浏览器隐藏更改False为True
        # ’--disable-infobars‘：禁用浏览器正在被自动化程序控制的提示
        #self.browser = await launch (headless=False, args=['--disable-infobars','--proxy-server=171.35.210.116:9999'])
        self.browser = await launch(headless=False, args=['--disable-infobars'])
        await asyncio.sleep (1)
        self.page = await self.browser.newPage ( )
        await asyncio.sleep (1)
        await self.page.evaluate (
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        await asyncio.sleep (1)
    async def Requests(self,save_name):
        await self.page.goto ('http://www.dianping.com/shenzhen/ch10/g117')
        await asyncio.sleep (5)
        #await self.try_validation(200)
        page_text = await self.page.content ( )
        # print(page_text)
        self.save(page_text, save_name,'w')
    def Parse(self,filename,save_name):
        """
        解析网页，获取字体文件并保存为template与woff,target.woff
        """
        file = open (filename, 'r').read ( )
        #font_url = re.findall ("url\(\'(.*?woff)", file)
        try:
            css_url=re.findall('(//s3plus.meituan.net/v1.*?\.css)',file)[0]
            css_text=requests.get('http:'+css_url).text
            print(css_text)
            font_url=re.findall('tagName.*?,url\(\"(.*?woff).*?tagName',css_text)[0]
            woff_text=requests.get('http:'+font_url).content
            self.save(woff_text, save_name,'wb')
            return font_url
        except IndexError:
            print('访问限制')
    def Encoding_string(self,target):
        """
        解析target_大众点评.html中需要解码的内容
        """
        file=open(target,'r').read()
        et=etree.HTML(file)
        tagName=et.xpath('//span[@class="tag"]//text()')
        shop=et.xpath('//div[@class="tit"]//h4/text()')
        dic={
            'tagName':tagName,
            'shop':shop
        }
        self.save(str(dic),'encoding_string.txt','w')
        print(dic)
    async def try_validation(self, distance):
        """
        如果遇到滑动验证码，调用该函数
        :distance1,distance2: 将距离拆分成两段，模拟正常人的行为
        """
        distance1 = distance - 30
        distance2 = 30
        btn_position = await self.page.evaluate ('''
           () =>{
            return {
             x: document.querySelector('#yodaBox').getBoundingClientRect().x,
             y: document.querySelector('#yodaBox').getBoundingClientRect().y,
             width: document.querySelector('#yodaBox').getBoundingClientRect().width,
             height: document.querySelector('#yodaBox').getBoundingClientRect().height
             }}
            ''')
        x = btn_position['x'] + btn_position['width'] / 2
        y = btn_position['y'] + btn_position['height'] / 2
        # print(btn_position)
        await self.page.mouse.move (x, y)
        await self.page.mouse.down ( )
        await self.page.mouse.move (x + distance1, y, {'steps': 10})
        await self.page.waitFor (800)
        await self.page.mouse.move (x + distance1 + distance2, y, {'steps': 20})
        await self.page.waitFor (800)
        await self.page.mouse.up ( )
    def save(self,page_text,path,mode):
        with open(path,mode)as f:
            f.write(page_text)
    async def run(self):
        #两次请求，一次获取模板数据，一次获取目标数据
        await self.init()
        await self.Requests('template_大众点评.html')
        self.Parse('template_大众点评.html','template.woff')
        await self.Requests('target_大众点评.html')
        self.Parse('target_大众点评.html','target.woff')
        self.Encoding_string('target_大众点评.html')

class FontDecrypter():
    def __init__(self,dynamic=True):
        if dynamic:
            self.glyphs_seq = None  # 字形序列
            self.template_font = None  # 笔画坐标
            self.current_font = None  # 当前笔画
    def show_glyphs(self, template):
        """
        存储字体顺序template.png，存储笔画坐标teamplate.json
        :param font_url:字体地址
        """
        current_font = TTFont(template)
        current_font.saveXML('template.html')
        glyph_map = current_font.getBestCmap()  # 代码点-字形名称映射
        print('代码点-字形名称映射',glyph_map)
        glyph_list = list(glyph_map)  # 留下代码点
        print('留下代码点',glyph_list)
        text = ''
        result = dict()
        for index, code in enumerate(glyph_list):
            print('index',index)
            print('code',code)
            glyph = current_font['glyf'][glyph_map[code]]  # 字形
            end_pts = glyph.endPtsOfContours  # 端点位置
            print('端点位置',end_pts)
            coordinates = glyph.coordinates.array  # 顶底坐标
            print ('顶点坐标', coordinates)
            print('顶点坐标list',list(coordinates))
            sliced_coordinates = self.slice_coordinates(list(coordinates), end_pts)
            print('sliced_coordinates',sliced_coordinates)
            number_of_contours = glyph.numberOfContours  # 轮廓数
            print('轮廓数',number_of_contours)
            result[number_of_contours] = result.get(number_of_contours, [])  # 将具有相同轮廓数的字形放在同一列表下
            result[number_of_contours].append({
                'coord': sliced_coordinates,
                'index': index
            })
            print('result',result)
            text =text + chr(code)  # 将unicode码转成对应的字符
            if index%20==0:
                text=text+'\n'#方便绘图时换行
        with open('template_font.json', 'w')as f:  # 保存坐标信息，存储笔画坐标
                json.dump(result, f)
        #显示字体顺序
        img = Image.new("RGB", (1920, 1050), '#fff')
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(template, 12)  # 设置图片字体
        draw.text((0, 0), text, font=font, fill="red", spacing=10)
        img.save('template.png')
        img.show()
    @staticmethod
    #静态方法，类似普通函数，无self,可以使用FontDecrypter.load_glyphs_data()直接调用
    def slice_coordinates(_coordinates, _end_pts):
        """
        将坐标按笔画拆分。由于不同字体文件中每段笔画的坐标数可能会不同，故需分段计算；若一并计算则后面的误差极大
        :param _coordinates: 坐标
        :param _end_pts: 端点
        :return: 切分后的坐标
        """
        end_pts = [0] + _end_pts  # 为方便遍历首位添0
        sliced_coordinates = [
            _coordinates[end_pts[index]:(end_pts[index + 1]) * 2]  # 坐标包含x和y，故需*2
            for index in range(len(end_pts) - 1)
        ]
        return sliced_coordinates
    @staticmethod
    def get_cosine_sim(_vector1, _vector2):
        """
        计算余弦相似度
        :param _vector1: 输入向量1
        :param _vector2: 输入向量2
        :return: 余弦
        """
        length = min(len(_vector1), len(_vector2))
        vector1 = numpy.array(_vector1[:length])
        vector2 = numpy.array(_vector2[:length])
        product = numpy.linalg.norm(vector1) * numpy.linalg.norm(vector2)
        sim = numpy.dot(vector1, vector2) / product
        return sim
    def load_glyphs_data(self, seq):
        """
        加载字体数据
        :param glyphs_seq:字体序列
        :return:
        """
        self.glyphs_seq = open(seq,'r').read()
        print(len(self.glyphs_seq))
        with open('template_font.json')as f:
            self.template_font = json.load(f)
    def sub_all(self, encoded_string, font_path):
        """
        替换所有加密字符
        :param encoded_string: 加密字符串
        :param font_path: 字体地址
        :return: 解密字符串
        """
        encoded_string=open(encoded_string,'r').read()
        print(encoded_string)
        self.current_font = TTFont(file=font_path)
        results = re.sub("u([0-9a-zA-Z]{4})'", self._sub_one, encoded_string)
        print(results)
        return results
    def _sub_one(self, match_result):
        """
        替换一个加密字符
        :param match_result: 正则匹配结果
        :return: 计算余弦相似度后最接近的字符
        """
        matched_one = match_result.group(1)
        unicode = int(matched_one, 16)
        glyph_name = self.current_font.getBestCmap().get(unicode)  # 代码点-字形名称映射
        if not glyph_name:
            return matched_one
        current_glyph = self.current_font['glyf'][glyph_name]
        if not current_glyph:
            print('Code %s not found in this font file.' % unicode)
            return '🐓填补空白'
        number_of_contours = current_glyph.numberOfContours
        template_glyphs = self.template_font.get(str(number_of_contours))  # 选取具有相同笔画数的字形
        if len(template_glyphs) == 1:  # 只有一个字形相匹配，无需比较相似度
            predicted_index = template_glyphs[0]['index']
        else:
            end_pts = current_glyph.endPtsOfContours
            coordinates = current_glyph.coordinates.array
            sliced_coordinates1 = self.slice_coordinates(list(coordinates), end_pts)
            predicted_index = max_sim = -1  # 预测的索引、最大相似度
            for template_glyph in template_glyphs:
                sim_sum = 0  # 所有笔画的相似度之和
                sliced_coordinates2 = template_glyph['coord']
                for vector1, vector2 in zip(sliced_coordinates1, sliced_coordinates2):
                    sim = self.get_cosine_sim(vector1, vector2)
                    sim_sum += sim
                if sim_sum > max_sim:
                    max_sim = sim_sum
                    predicted_index = template_glyph['index']
        print(predicted_index)
        try:
            predicted_value = self.glyphs_seq[predicted_index]
        except IndexError:
            predicted_value='#'
        return predicted_value

class BaiduAI():
    def __init__(self,font):
        self.font=font
    def baidu_ai(self):
        """
        使用百度ai把template.png抓为文字
        :return: 模板文字
        """
        APP_ID='x'
        API_KEY='x'
        SECRET_KEY='x'
        client=AipOcr(APP_ID,API_KEY,SECRET_KEY)
        i=open(self.font,'rb').read()
        message=client.basicGeneral(i)
        print(message)
        pattern=re.compile("'words'.*?'([^0-9a-zA-Z{}:].*?)'")
        template_font_text=re.findall(pattern,str(message))
        print(template_font_text)
        text=''.join(template_font_text).replace(' ','')
        with open('seq.txt','w')as f:
            f.write(text)
        return text

def main():
    asyncio.get_event_loop().run_until_complete(Pyppeteer().run())
    FD=FontDecrypter()
    FD.show_glyphs('template.woff')
    BD=BaiduAI('template.png')
    BD.baidu_ai()#AI转译也会有错误，需要人工校验
    FD.load_glyphs_data('seq.txt')
    FD.sub_all('encoding_string.txt','target.woff')

if __name__ == '__main__':
    main()


