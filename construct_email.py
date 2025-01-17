from paper import ArxivPaper
import math
from tqdm import tqdm
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import datetime
from loguru import logger
from typing import Optional
from urllib.parse import quote_plus

framework = """
<!DOCTYPE HTML>
<html>
<head>
  <style>
    .star-wrapper {
      font-size: 1.3em; /* 调整星星大小 */
      line-height: 1; /* 确保垂直对齐 */
      display: inline-flex;
      align-items: center; /* 保持对齐 */
    }
    .half-star {
      display: inline-block;
      width: 0.5em; /* 半颗星的宽度 */
      overflow: hidden;
      white-space: nowrap;
      vertical-align: middle;
    }
    .full-star {
      vertical-align: middle;
    }
  </style>
</head>
<body>

<div>
    __CONTENT__
</div>

<br><br>
<div>
To unsubscribe, remove your email in your Github Action setting.
</div>

</body>
</html>
"""

def get_empty_html():
  block_template = """
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
  <tr>
    <td style="font-size: 20px; font-weight: bold; color: #333;">
        No Papers Today. Take a Rest!
    </td>
  </tr>
  """
  return block_template

def get_block_html(title:str, authors:str, rate:str, arxiv_id:str, abstract:str, topic:str, tldr: Optional[str], pdf_url: Optional[str], code_url: Optional[str]=None, affiliations: Optional[str]=None):
    ai_url = f'''https://kimi.moonshot.cn/_prefill_chat?prefill_prompt=请你阅读{title}这篇论文，链接是 {pdf_url} ，并回答以下问题：
**Q1. 这篇论文试图解决什么问题？**
**Q2. 这是一个新问题吗？如果有相关研究，请给出并总结方法**
**Q3. 本文试图验证的科学假设是什么？**
**Q4. 这篇论文提出了什么新的想法、方法或模型？与以前的方法相比，有什么特点和优势？**
**Q5. 论文中的实验是如何设计的？**
**Q6. 实验和结果是否很好地支持了需要验证的科学假设**
回答时请先重复问题，再进行对应的回答。&system_prompt=你是一个学术专家，请你仔细阅读后续链接中的论文，并对用户的问题进行专业的回答，不要出现第一人称，当涉及到分点回答时，鼓励你以markdown格式输出。对于引用的内容，你需要及时在引用内容后给出参考链接。&send_immediately=true&force_search=true'''
    ai_url = quote_plus(ai_url, safe='/:?=&')
    code = f'<a href="{code_url}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #5bc0de; padding: 8px 16px; border-radius: 4px; margin-left: 8px;">Code</a>' if code_url else ''
    block_template = """
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
    <tr>
        <td style="font-size: 20px; font-weight: bold; color: #333;">
            {title}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #666; padding: 8px 0;">
            {authors}
            <br>
            <i>{affiliations}</i>
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Tag:</strong> {topic}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Score:</strong> {rate}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>arXiv ID:</strong> {arxiv_id}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Abstract:</strong> {abstract}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>TLDR:</strong> {tldr}
        </td>
    </tr>

    <tr>
        <td style="padding: 8px 0;">
            <a href="{pdf_url}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #d9534f; padding: 8px 16px; border-radius: 4px;">PDF</a>
            <a href="{kimi}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #476fae; padding: 8px 16px; border-radius: 4px;">Kimi</a>
            {code}
        </td>
    </tr>
</table>
"""
    return block_template.format(title=title, authors=authors,rate=rate, arxiv_id=arxiv_id, tldr=tldr, abstract=abstract, topic=topic, pdf_url=pdf_url, code=code, affiliations=affiliations, kimi=ai_url)

def get_stars(score:float):
    full_star = '<span class="full-star">⭐</span>'
    half_star = '<span class="half-star">⭐</span>'
    low = 0
    high = 5
    if score <= low:
        return ''
    elif score >= high:
        return full_star * 5
    else:
        full_star_num = int(score)
        half_star_num = int(2 * (score - full_star_num))
        return '<div class="star-wrapper">'+full_star * full_star_num + half_star * half_star_num + '</div>'


def render_email(papers:list[ArxivPaper]):
    parts = []
    if len(papers) == 0 :
        return framework.replace('__CONTENT__', get_empty_html())
    
    for p in tqdm(papers,desc='Rendering Email'):
        p.generate_property()
        rate = get_stars(p.score)
        authors = [a.name for a in p.authors[:5]]
        authors = ', '.join(authors)
        if len(p.authors) > 5:
            authors += ', ...'
        if p.affiliations is not None:
            affiliations = p.affiliations[:5]
            affiliations = ', '.join(affiliations)
            if len(p.affiliations) > 5:
                affiliations += ', ...'
        else:
            affiliations = 'Unknown Affiliation'
        parts.append(get_block_html(title = p.title, authors = authors, 
                                    rate = rate, arxiv_id = p.arxiv_id,
                                    tldr = p.tldr, abstract = p.summary,
                                    topic = p.topic, pdf_url = p.pdf_url, 
                                    code_url = p.code_url, affiliations = affiliations))

    content = '<br>' + '</br><br>'.join(parts) + '</br>'
    return framework.replace('__CONTENT__', content)

def send_email(sender:str, receiver:str, password:str,smtp_server:str,smtp_port:int, html:str,):
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = _format_addr('Github Action <%s>' % sender)
    msg['To'] = _format_addr('You <%s>' % receiver)
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    msg['Subject'] = Header(f'Daily arXiv {today}', 'utf-8').encode()

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
    except Exception as e:
        logger.warning(f"Failed to use TLS. {e}")
        logger.warning(f"Try to use SSL.")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)

    server.login(sender, password)
    server.sendmail(sender, [receiver], msg.as_string())
    server.quit()
