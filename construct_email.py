from paper import ArxivPaper
from tqdm import tqdm
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import datetime
from loguru import logger
from typing import Optional
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

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
      background-image: linear-gradient(120deg, #f5f7fa 0%, #c3cfe2 100%);
      min-height: 100vh;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
      background-color: rgba(255, 255, 255, 0.85);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
      padding: 24px;
      position: relative;
      border: 1px solid rgba(255, 255, 255, 0.18);
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
      background-color: rgba(249, 249, 249, 0.9);
      border: 1px solid #ddd;
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      position: relative;
    }
    .paper-block:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }
    .paper-block.visible {
      opacity: 1;
      transform: translateY(0);
    }
    .paper-block::after {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border-radius: 8px;
      box-shadow: 0 15px 25px rgba(0, 0, 0, 0.15);
      opacity: 0;
      transition: all 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
      z-index: -1;
    }
    .paper-block:hover::after {
      opacity: 1;
    }
    .paper-title {
      font-size: 24px;
      font-weight: 700;
      color: #2c3e50;
      margin-bottom: 16px;
      position: relative;
      padding-bottom: 10px;
      transition: color 0.3s ease;
    }
    .paper-title::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 50px;
      height: 3px;
      background: linear-gradient(90deg, #3498db, #9b59b6);
      transition: width 0.3s ease;
    }
    .paper-block:hover .paper-title::after {
      width: 100%;
    }
    .paper-block:hover .paper-title {
      color: #3498db;
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
      border-radius: 6px;
      transition: all 0.3s ease;
      box-shadow: 0 2px 5px rgba(52, 152, 219, 0.3);
      position: relative;
      overflow: hidden;
    }
    .paper-actions a:hover {
      background-color: #2980b9;
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
    }
    .paper-actions a:active {
      transform: translateY(0);
      box-shadow: 0 2px 5px rgba(52, 152, 219, 0.3);
    }
    .paper-actions a::before {
      content: "";
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
      transition: left 0.7s ease;
    }
    .paper-actions a:hover::before {
      left: 100%;
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
      width: 50px;
      height: 50px;
      border-radius: 50%;
      text-decoration: none;
      font-size: 24px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      visibility: visible;
    }
    .back-to-top:hover {
      background-color: #2980b9;
      transform: translateY(-5px);
      box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
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
    .date-navigation {
      display: flex;
      gap: 16px;
      justify-content: center;
      margin-bottom: 16px;
    }
    .nav-link {
      text-decoration: none;
      color: #3498db;
      font-weight: 500;
      padding: 8px 16px;
      border-radius: 4px;
      background-color: #f0f0f0;
      transition: all 0.3s ease;
    }
    .nav-link:hover {
      background-color: #3498db;
      color: white;
    }
    .progress-container {
      position: sticky;
      top: 0;
      width: 100%;
      height: 5px;
      background: transparent;
      z-index: 1000;
    }
    .progress-bar {
      height: 5px;
      background: linear-gradient(90deg, #3498db, #9b59b6);
      width: 0%;
      border-radius: 0 2px 2px 0;
    }
  </style>
</head>
<body>

<!-- 提示条 -->
<div class="browser-prompt" id="browser-prompt">
  For the best experience, please open this page in your browser.
  <a href="https://xiangsam.github.io/arxiv-daily/">Open in Browser</a>
</div>

<div class="progress-container">
  <div class="progress-bar" id="progress-bar"></div>
</div>

<div class="container">
  <div class="header">
    <h1>Daily Research Papers</h1>
    <p>Your daily dose of the latest research papers, curated just for you.</p>
    <div class="date-navigation">
      <a href="/arxiv-daily/archive/__PREV_DATE_1__.html" class="nav-link">← Previous Day</a>
      <a href="/arxiv-daily/archive/__PREV_DATE_2__.html" class="nav-link">← 2 Days Ago</a>
    </div>
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
  
  // 滚动进度条
  window.onscroll = function() {scrollFunction()};
  
  function scrollFunction() {
    var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    var scrolled = (winScroll / height) * 100;
    document.getElementById("progress-bar").style.width = scrolled + "%";
    
    // 显示/隐藏回到顶部按钮
    if (winScroll > 300) {
      backToTopButton.style.opacity = "1";
    } else {
      backToTopButton.style.opacity = "0";
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

def get_block_html(title:str, authors:str, rate:str, arxiv_id:str, abstract:str, topic: Optional[str], tldr: Optional[str], pdf_url: Optional[str], code_url: Optional[str]=None, affiliations: Optional[str]=None):
    title = title.replace('&', '')  # 移除特殊字符
    ai_url = f'''https://kimi.moonshot.cn/_prefill_chat?prefill_prompt=请你阅读{title}这篇论文，链接是 {pdf_url} ，并回答以下问题：
**Q1. 这篇论文试图解决什么问题？**
**Q2. 这是一个新问题吗？如果有相关研究，请给出并总结方法**
**Q3. 本文试图验证的科学假设是什么？**
**Q4. 这篇论文提出了什么新的想法、方法或模型？与以前的方法相比，有什么特点和优势？**
**Q5. 论文中的实验是如何设计的？**
**Q6. 实验和结果是否很好地支持了需要验证的科学假设**
回答时请先重复问题，再进行对应的回答。&system_prompt=你是一个学术专家，请你仔细阅读后续链接中的论文，并对用户的问题进行专业的回答，不要出现第一人称，当涉及到分点回答时，鼓励你以markdown格式输出。对于引用的内容，你需要及时在引用内容后给出参考链接。&send_immediately=true&force_search=false'''
    ai_url = quote_plus(ai_url, safe='/:?=&')
    code = f"""<a href="javascript:void(0)" onclick="openModal('{code_url}')" class="paper-actions">Code</a>""" if code_url else ''
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
            <a href="javascript:void(0)" onclick="openModal('{pdf_url}')">PDF</a>
            <a href="javascript:void(0)" onclick="openModal('{kimi}')">Kimi</a>
            {code}
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

def process_paper(paper:ArxivPaper):
    """处理单个论文并返回HTML块"""
    rate = get_stars(paper.score)
    authors = [a.name for a in paper.authors[:5]]
    authors = ', '.join(authors)
    if len(paper.authors) > 5:
        authors += ', ...'
    if paper.affiliations is not None:
        affiliations = paper.affiliations[:5]
        affiliations = ', '.join(affiliations)
        if len(paper.affiliations) > 5:
            affiliations += ', ...'
    else:
        affiliations = 'Unknown Affiliation'
    return get_block_html(title = paper.title, authors = authors, 
                                    rate = rate, arxiv_id = paper.arxiv_id,
                                    tldr = paper.tldr, abstract = paper.summary,
                                    topic = paper.topic, pdf_url = paper.pdf_url, 
                                    code_url = paper.code_url, affiliations = affiliations)

def render_email(papers:list[ArxivPaper]):
    parts = []
    today = datetime.datetime.now()
    prev_date_1 = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    prev_date_2 = (today - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    html = framework.replace('__PREV_DATE_1__', prev_date_1).replace('__PREV_DATE_2__', prev_date_2)
    if len(papers) == 0 :
        return html.replace('__CONTENT__', get_empty_html())
    
    # 使用线程池并行处理，但保持原始顺序
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_paper, paper): i for i, paper in enumerate(papers)}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(papers), desc='Rendering HTML'):
            try:
                index = futures[future]
                results[index] = future.result()
            except Exception as e:
                logger.error(f"论文处理出错: {e}")
    parts = [results[i] for i in range(len(papers)) if i in results]
    content = '<br>' + '</br><br>'.join(parts) + '</br>'
    return html.replace('__CONTENT__', content)

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
        logger.warning("Try to use SSL.")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)

    server.login(sender, password)
    server.sendmail(sender, [receiver], msg.as_string())
    server.quit()
