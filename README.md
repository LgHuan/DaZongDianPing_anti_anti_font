1、项目描述
爬取大众点评店铺信息
2、技术难点
（1）网站的字体文件woff是动态的，且字体文件解析后的（x,y）坐标并非国定不变，相同文字对应的坐标有细小差距，可采用余弦相似定理或距离公式判断；（2）大众点评反爬机制严格，可采用谷歌官方框架pyppeteer。
3、技术方案
（1）用pyppeteer两次请求url，解析保存template.woff，temp_大众点评.html，target.woff，targ_大众点评.html，对targ_大众点评.html解析需要解码的encoding_string.txt。（2）解析template.woff得到模板字体顺序template.png，存储笔画坐标tempalte.json。（3）解密encoding_string.txt，如果encoding_string.txt对应的target.woff笔画坐标与tempalte.json满足相似阀值，则返回相应顺序的template.png中的文字。（4）采用百度ai转译template.png中的文字。
