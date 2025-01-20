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
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
  <style>
    body {
      font-family: 'Roboto', sans-serif;
      background-color: #f5f5f5;
      margin: 0;
      padding: 20px;
      color: #333;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      background-color: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      padding: 24px;
      position: relative;
    }
    .header {
      text-align: center;
      margin-bottom: 32px;
    }
    .header h1 {
      font-size: 32px;
      font-weight: 700;
      color: #2c3e50;
      margin-bottom: 8px;
    }
    .header p {
      font-size: 16px;
      color: #666;
    }
    .paper-block {
      margin-bottom: 24px;
      padding: 16px;
      border-radius: 8px;
      background-color: #f9f9f9;
      border: 1px solid #ddd;
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.6s ease, transform 0.6s ease;
    }
    .paper-block.visible {
      opacity: 1;
      transform: translateY(0);
    }
    .paper-title {
      font-size: 24px;
      font-weight: 700;
      color: #2c3e50;
      margin-bottom: 8px;
    }
    .paper-authors {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
    }
    .paper-affiliations {
      font-size: 12px;
      color: #888;
      font-style: italic;
      margin-bottom: 8px;
    }
    .paper-tag {
      font-size: 14px;
      color: #333;
      margin-bottom: 8px;
    }
    .paper-score {
      font-size: 14px;
      color: #333;
      margin-bottom: 8px;
    }
    .paper-abstract {
      font-size: 14px;
      color: #444;
      line-height: 1.6;
      margin-bottom: 16px;
    }
    .paper-tldr {
      font-size: 14px;
      color: #444;
      line-height: 1.6;
      margin-bottom: 16px;
    }
    .paper-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .paper-actions a {
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      color: #fff;
      background-color: #3498db;
      padding: 8px 16px;
      border-radius: 4px;
      transition: background-color 0.3s ease;
    }
    .paper-actions a:hover {
      background-color: #2980b9;
    }
    .heart-btn {
      cursor: pointer;
      font-size: 24px;
      filter: grayscale(1) brightness(0.8);
      transition: filter 0.3s ease, transform 0.2s ease;
    }
    .heart-btn:hover {
      filter: grayscale(0.8) brightness(1);
      transform: scale(1.1);
    }
    .heart-btn.active {
      filter: grayscale(0) drop-shadow(0 0 4px rgba(231, 76, 60, 0.5));
    }
    .star-wrapper {
      font-size: 1.3em;
      line-height: 1;
      display: inline-flex;
      align-items: center;
    }
    .half-star {
      display: inline-block;
      width: 0.5em;
      overflow: hidden;
      white-space: nowrap;
      vertical-align: middle;
    }
    .full-star {
      vertical-align: middle;
    }
    .footer {
      text-align: center;
      font-size: 12px;
      color: #888;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #ddd;
    }
    .footer a {
      color: #3498db;
      text-decoration: none;
    }
    .footer a:hover {
      text-decoration: underline;
    }
    .back-to-top {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background-color: #3498db;
      color: #fff;
      padding: 10px 16px;
      border-radius: 50%;
      text-decoration: none;
      font-size: 18px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      transition: background-color 0.3s ease;
    }
    .back-to-top:hover {
      background-color: #2980b9;
    }
    /* Toast 提示条样式 */
    .toast {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background-color: #333;
      color: #fff;
      padding: 12px 24px;
      border-radius: 4px;
      font-size: 14px;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0.3s ease;
      z-index: 1000;
    }
    .toast.visible {
      opacity: 1;
      visibility: visible;
    }
    /* 模态框样式 */
    .modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.5);
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }
    .modal.visible {
      display: flex;
    }
    .modal-content {
      background-color: #fff;
      border-radius: 8px;
      width: 90%;
      max-width: 800px;
      height: 80%;
      overflow: hidden;
      position: relative;
    }
    .modal-iframe {
      width: 100%;
      height: 100%;
      border: none;
    }
    .modal-actions {
      position: absolute;
      top: 10px;
      right: 10px;
      display: flex;
      gap: 8px;
    }
    .modal-button {
      background-color: #3498db;
      color: #fff;
      border: none;
      border-radius: 50%;
      width: 30px;
      height: 30px;
      font-size: 16px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.3s ease;
    }
    .modal-button:hover {
      background-color: #2980b9;
    }
    .modal-button.close {
      background-color: #e74c3c;
    }
    .modal-button.close:hover {
      background-color: #c0392b;
    }
    /* 提示条样式 */
    .browser-prompt {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      background-color: #3498db;
      color: #fff;
      padding: 12px;
      text-align: center;
      z-index: 1000;
      display: none;
      display: block;
    }
    .browser-prompt a {
      color: #fff;
      text-decoration: underline;
      margin-left: 8px;
    }
    .browser-prompt a:hover {
      color: #f1c40f;
    }
  </style>
</head>
<body>

<!-- 提示条 -->
<div class="browser-prompt" id="browser-prompt">
  For the best experience, please open this page in your browser.
  <a href="https://xiangsam.github.io/arxiv-daily/">Open in Browser</a>
</div>

<div class="container">
  <div class="header">
    <h1>Daily Research Papers</h1>
    <p>Your daily dose of the latest research papers, curated just for you.</p>
  </div>

  <div>
    __CONTENT__
  </div>

  <div class="footer">
    <p>To unsubscribe, remove your email in your Github Action setting.</p>
    <p>To have a full reading experience, <a href='https://xiangsam.github.io/arxiv-daily/'>visit this page</a> in a modern brower.</p>
    <p>&copy; 2023 Research Digest. All rights reserved.</p>
  </div>
</div>

<!-- Toast 提示条 -->
<div class="toast" id="toast">Added to favorites!</div>

<!-- 模态框 -->
<div class="modal" id="modal">
  <div class="modal-content">
    <div class="modal-actions">
      <button class="modal-button" onclick="openInNewTab()" title="Open in new tab">
        <i class="fas fa-external-link-alt"></i>
      </button>
      <button class="modal-button close" onclick="closeModal()" title="Close">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <iframe class="modal-iframe" id="modal-iframe" src=""></iframe>
  </div>
</div>

<a href="#" class="back-to-top">↑</a>

<script>
  // 检测是否在浏览器中正常加载
  function isNormalBrowserLoad() {
    // 检查是否可以执行JavaScript
    if (typeof window!== 'undefined' && 'location' in window) {
      return true;
    }
    return false;
  }

  // 隐藏提示条
  if (isNormalBrowserLoad()) {
    const prompt = document.getElementById('browser-prompt');
    prompt.style.display = 'none'; // 隐藏提示条
  }
  
  // 动态加载效果
  document.addEventListener('DOMContentLoaded', function () {
    const paperBlocks = document.querySelectorAll('.paper-block');
    paperBlocks.forEach((block, index) => {
      setTimeout(() => {
        block.classList.add('visible');
      }, index * 200);
    });
  });

  // 回到顶部按钮
  const backToTopButton = document.querySelector('.back-to-top');
  backToTopButton.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // 心形按钮点击提示
  function toggleHeart(button) {
    button.classList.toggle('active');
    showToast('Added to favorites!');
  }

  // 显示 Toast 提示
  function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('visible');
    setTimeout(() => {
      toast.classList.remove('visible');
    }, 3000); // 3 秒后消失
  }
  
  // 打开模态框
  function openModal(url) {
    const modal = document.getElementById('modal');
    const iframe = document.getElementById('modal-iframe');
    iframe.src = url;
    modal.classList.add('visible');
  }

  // 关闭模态框
  function closeModal() {
    const modal = document.getElementById('modal');
    const iframe = document.getElementById('modal-iframe');
    iframe.src = ''; // 清空 iframe 内容
    modal.classList.remove('visible');
  }

  // 在新标签页打开
  function openInNewTab() {
    const iframe = document.getElementById('modal-iframe');
    const url = iframe.src;
    if (url) {
      window.open(url, '_blank');
    }
  }
</script>

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
    code = f"""<a href="#" onclick="openModal('{code_url}')" class="paper-actions">Code</a>""" if code_url else ''
    block_template = """
    <div class="paper-block">
        <div class="paper-title">{title}</div>
        <div class="paper-authors">{authors}</div>
        <div class="paper-affiliations">{affiliations}</div>
        <div class="paper-tag"><strong>Tag:</strong> {topic}</div>
        <div class="paper-score"><strong>Score:</strong> {rate}</div>
        <div class="paper-abstract"><strong>Abstract:</strong> {abstract}</div>
        <div class="paper-tldr"><strong>TLDR:</strong> {tldr}</div>
        <div class="paper-actions">
            <a href="#" onclick="openModal('{pdf_url}')">PDF</a>
            <a href="#" onclick="openModal('{kimi}')">Kimi</a>
            {code}
            <span class="heart-btn" onclick="toggleHeart(this)">❤️</span>
        </div>
    </div>
    """
    return block_template.format(title=title, authors=authors, rate=rate, arxiv_id=arxiv_id, tldr=tldr, abstract=abstract, topic=topic, pdf_url=pdf_url, code=code, affiliations=affiliations, kimi=ai_url)

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
