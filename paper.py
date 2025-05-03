from typing import Optional
from functools import cached_property
from tempfile import TemporaryDirectory
import arxiv
import tarfile
import re
from llm import get_llm
import requests
from requests.adapters import HTTPAdapter, Retry
from loguru import logger
import tiktoken
from contextlib import ExitStack
from ast import literal_eval




class ArxivPaper:
    def __init__(self,paper:arxiv.Result):
        self._paper = paper
        self.introduction: str = ""
        self.conclusion: str = ""
        self.tex: Optional[dict[str,str]] = None
        self.post_init()
    
    def post_init(self):
        self.tex = self.fetch_tex()
        if self.tex is not None:
            content = self.tex.get("all")
            if content is None:
                content = "\n".join(self.tex.values())
            #remove cite
            content = re.sub(r'~?\\cite.?\{.*?\}', '', content)
            #remove figure
            content = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', content, flags=re.DOTALL)
            #remove table
            content = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', content, flags=re.DOTALL)
            #find introduction and conclusion
            # end word can be \section or \end{document} or \bibliography or \appendix
            match = re.search(r'\\section\{Introduction\}.*?(\\section|\\end\{document\}|\\bibliography|\\appendix|$)', content, flags=re.DOTALL)
            if match:
                self.introduction = match.group(0)
            match = re.search(r'\\section\{Conclusion\}.*?(\\section|\\end\{document\}|\\bibliography|\\appendix|$)', content, flags=re.DOTALL)
            if match:
                self.conclusion = match.group(0)
    
    def generate_base_properties(self):
        """生成affiliations, score等基本属性"""
        self.affiliations = self.get_affiliations()
        self.score = 1.0
        if self.affiliations is not None:
            self.score = self.get_score()

    def generate_extended_property(self):
        tldr_and_topic = self.get_tldr_and_topic()
        if tldr_and_topic is not None:
            try:
                res = literal_eval(tldr_and_topic)
                if isinstance(res, dict):
                    self.tldr = res.get('tldr', None)
                    self.topic = res.get('topic', None)
            except:
                logger.warning(f'Could not parse {tldr_and_topic} to dict, display it in tldr directly.')
                self.tldr = tldr_and_topic
                self.topic = None
        

    @property
    def title(self) -> str:
        return self._paper.title
    
    @property
    def summary(self) -> str:
        return self._paper.summary
    
    @property
    def authors(self):
        return self._paper.authors
    
    @cached_property
    def arxiv_id(self):
        return re.sub(r'v\d+$', '', self._paper.get_short_id())
    
    @property
    def pdf_url(self):
        return self._paper.pdf_url.replace('http://', 'https://')
    
    
    @cached_property
    def code_url(self) -> Optional[str]:
        s = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1)
        s.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            paper_list = s.get(f'https://paperswithcode.com/api/v1/papers/?arxiv_id={self.arxiv_id}').json()
        except Exception as e:
            logger.debug(f'Error when searching {self.arxiv_id}: {e}')
            return None

        if paper_list.get('count',0) == 0:
            return None
        paper_id = paper_list['results'][0]['id']

        try:
            repo_list = s.get(f'https://paperswithcode.com/api/v1/papers/{paper_id}/repositories/').json()
        except Exception as e:
            logger.debug(f'Error when searching {self.arxiv_id}: {e}')
            return None
        if repo_list.get('count',0) == 0:
            return None
        return repo_list['results'][0]['url']
    
    def fetch_tex(self) -> Optional[dict[str,str]]:
        with ExitStack() as stack:
            tmpdirname = stack.enter_context(TemporaryDirectory())
            file = self._paper.download_source(dirpath=tmpdirname)
            try:
                tar = stack.enter_context(tarfile.open(file))
            except tarfile.ReadError:
                logger.debug(f"Failed to find main tex file of {self.arxiv_id}: Not a tar file.")
                return None
 
            tex_files = [f for f in tar.getnames() if f.endswith('.tex')]
            if len(tex_files) == 0:
                logger.debug(f"Failed to find main tex file of {self.arxiv_id}: No tex file.")
                return None
            
            bbl_file = [f for f in tar.getnames() if f.endswith('.bbl')]
            if len(bbl_file) == 0:
                if len(tex_files) > 1:
                    logger.debug(f"Cannot find main tex file of {self.arxiv_id} from bbl: There are multiple tex files while no bbl file.")
                    main_tex = None
                else:
                    main_tex = tex_files[0]
            elif len(bbl_file) == 1:
                main_name = bbl_file[0].replace('.bbl', '')
                main_tex = f"{main_name}.tex"
                if main_tex not in tex_files:
                    logger.debug(f"Cannot find main tex file of {self.arxiv_id} from bbl: The bbl file does not match any tex file.")
                    main_tex = None
            else:
                logger.debug(f"Cannot find main tex file of {self.arxiv_id} from bbl: There are multiple bbl files.")
                main_tex = None
            if main_tex is None:
                logger.debug(f"Trying to choose tex file containing the document block as main tex file of {self.arxiv_id}")
            #read all tex files
            file_contents = {}
            for t in tex_files:
                f = tar.extractfile(t)
                if f is None:
                    logger.debug(f"Failed to read {t} of {self.arxiv_id}")
                    continue
                content = f.read().decode('utf-8',errors='ignore')
                #remove comments
                content = re.sub(r'%.*\n', '\n', content)
                content = re.sub(r'\\begin{comment}.*?\\end{comment}', '', content, flags=re.DOTALL)
                content = re.sub(r'\\iffalse.*?\\fi', '', content, flags=re.DOTALL)
                #remove redundant \n
                content = re.sub(r'\n+', '\n', content)
                content = re.sub(r'\\\\', '', content)
                #remove consecutive spaces
                content = re.sub(r'[ \t\r\f]{3,}', ' ', content)
                if main_tex is None and re.search(r'\\begin\{document\}', content):
                    main_tex = t
                    logger.debug(f"Choose {t} as main tex file of {self.arxiv_id}")
                file_contents[t] = content
            
            if main_tex is not None:
                main_source:str = file_contents[main_tex]
                #find and replace all included sub-files
                include_files = re.findall(r'\\input\{(.+?)\}', main_source) + re.findall(r'\\include\{(.+?)\}', main_source)
                for f in include_files:
                    if not f.endswith('.tex'):
                        file_name = f + '.tex'
                    else:
                        file_name = f
                    main_source = main_source.replace(f'\\input{{{f}}}', file_contents.get(file_name, ''))
                file_contents["all"] = main_source
            else:
                logger.debug(f"Failed to find main tex file of {self.arxiv_id}: No tex file containing the document block.")
                file_contents["all"] = None
        return file_contents
    
    def get_tldr_and_topic(self) -> Optional[str]:
        prompt = """Given the title, abstract, introduction and the conclusion (if any) of a paper in latex format, generate a one-sentence TLDR summary in Chinese. Additionally, propose one relevant search topic (e.g. LLM Position Embedding) related to the paper's category in English, __CATEGORY__.
        
        \\title{__TITLE__}
        \\begin{abstract}__ABSTRACT__\\end{abstract}
        __INTRODUCTION__
        __CONCLUSION__

        Response a python dict with 'tldr' and 'topic' as keys, i.e., "{'tldr': "...", 'topic': "..."}". Make sure your response could be directly parserd by python eval function. Only return plaint text. Do not return any intermediate results.
        """
        prompt = prompt.replace('__TITLE__', self.title)
        prompt = prompt.replace('__ABSTRACT__', self.summary)
        prompt = prompt.replace('__INTRODUCTION__', self.introduction)
        prompt = prompt.replace('__CONCLUSION__', self.conclusion)
        prompt = prompt.replace('__CATEGORY__', str(self._paper.categories))

        # use gpt-4o tokenizer for estimation
        enc = tiktoken.encoding_for_model("gpt-4o")
        prompt_tokens = enc.encode(prompt)
        prompt_tokens = prompt_tokens[:4000]  # truncate to 4000 tokens
        prompt = enc.decode(prompt_tokens)
        llm = get_llm()
        res = llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant who perfectly summarizes scientific paper, and gives the core idea of the paper to the user. Make sure your response could be directly parserd by python eval function.",
                },
                {"role": "user", "content": prompt},
            ]
        )
        res = llm.generate(
                messages=[
                    {
                        'role': 'system',
                        'content': "You are an python dict assistant. Check the python dict format and make sure it is a valid python dict with key \'tldr\' and \'topic\'. If it is not a valid python dict, try to fix it. If it is a valid python dict, just return it. Make sure your response could be directly parserd by python eval function.",
                    },
                    {'role': 'user', 'content': res},
                ]
            )
        return res

    def get_affiliations(self) -> Optional[list[str]]:
        if self.tex is not None:
            content = self.tex.get("all")
            if content is None:
                content = "\n".join(self.tex.values())
            #search for affiliations
            match = re.search(r'\\author.*?\\maketitle', content, flags=re.DOTALL)
            if match:
                information_region = match.group(0)
            else:
                logger.debug(f"Failed to extract affiliations of {self.arxiv_id}: No author information found.")
                return None
            prompt = f"Given the author information of a paper in latex format, extract the affiliations of the authors in a python list format, which is sorted by the author order. If there is no affiliation found, return an empty list '[]'. Following is the author information:\n{information_region}"
            # use gpt-4o tokenizer for estimation
            enc = tiktoken.encoding_for_model("gpt-4o")
            prompt_tokens = enc.encode(prompt)
            prompt_tokens = prompt_tokens[:4000]  # truncate to 4000 tokens
            prompt = enc.decode(prompt_tokens)
            llm = get_llm()
            affiliations = llm.generate(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant who perfectly extracts affiliations of authors from the author information of a paper. You should return a python list of affiliations sorted by the author order, like ['TsingHua University','Peking University']. If an affiliation is consisted of multi-level affiliations, like 'Department of Computer Science, TsingHua University', you should return the top-level affiliation 'TsingHua University' only. Do not contain duplicated affiliations. If there is no affiliation found, you should return an empty list [ ]. You should only return the final list of affiliations, and do not return any intermediate results.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            affiliations = llm.generate(
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an python list assistant. Check the python list format and make sure it is a valid python list. If it is not a valid python list, try to fix it. If it is a valid python list, just return it.',
                    },
                    {'role': 'user', 'content': affiliations},
                ]
            )
            try:
                affiliations = re.search(r'\[.*?\]', affiliations, flags=re.DOTALL).group(0)
                affiliations = literal_eval(affiliations)
                affiliations = list(set(affiliations))
                affiliations = [str(a) for a in affiliations]
            except Exception as e:
                logger.debug(f"Failed to extract affiliations of {self.arxiv_id}: {e}")
                return None
            return affiliations
        return None
    
    def get_score(self) -> float:
        prompt = """Given the author affiliations, generate a score for the paper. Only for reference, here are my affiliations preferences list, listed higher are the ones I prefer more.

        USA University list: [
            Carnegie Mellon University,
            University of Illinois at Urbana-Champaign,
            University of Maryland - College Park,
            University of California - San Diego,
            Cornell University,
            University of Michigan,
            Stanford University,
            Georgia Institute of Technology,
            Massachusetts Institute of Technology,
            University of California - Los Angeles,
            University of California - Berkeley,
            University of Massachusetts Amherst,
            New York University,
            University of Washington]
        China University list: [Peking University, Tsinghua University, Hong Kong University of Science and Technology, Shanghai Jiao Tong University, Zhejiang University, Chinese Academy of Sciences]
        Lab list: [OpenAI, Deepseek-AI, DeepMind, Meta, Google, Alibaba, Tencent, ByteDance, Microsoft, Nvidia, Huawei, Facebook, Amazon, IBM Watson, Intel, Apple]
        
        The affiliations of this paper are as follows: __AFFILIATIONS__"""
        prompt = prompt.replace('__AFFILIATIONS__', str(self.affiliations))

        # use gpt-4o tokenizer for estimation
        enc = tiktoken.encoding_for_model("gpt-4o")
        prompt_tokens = enc.encode(prompt)
        prompt_tokens = prompt_tokens[:4000]  # truncate to 4000 tokens
        prompt = enc.decode(prompt_tokens)
        llm = get_llm()
        score = llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant who perfectly generates a score for the paper based on the affiliations of the authors. You prefer papers about knowledge and analysis rather than simply application. If the affiliations are not found, you should return 1. The score should be a number between 0 and 5, with 0.5 as the minimum step. Only retuen the score, do not return any intermediate results.",
                },
                {"role": "user", "content": prompt},
            ]
        )
        if score is None:
            return 1
        return literal_eval(score)
